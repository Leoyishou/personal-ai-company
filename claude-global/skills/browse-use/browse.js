#!/usr/bin/env node
/**
 * browse-use - Headless browser automation with auth inheritance and session isolation
 *
 * Commands:
 *   run <script.js> [--session=name] [--debug] [--headed]
 *   run-inline '<code>' [--session=name] [--debug] [--headed]
 *   sessions                    - List active sessions
 *   close [name|--all]          - Close session(s)
 *   snapshot                    - Refresh auth snapshot from debug Chrome
 */

const fs = require('fs');
const path = require('path');

// Resolve playwright from sibling playwright-skill
const PW_SKILL = path.join(__dirname, '..', 'playwright-skill');
const { chromium } = require(path.join(PW_SKILL, 'node_modules', 'playwright'));
const helpers = require(path.join(PW_SKILL, 'lib', 'helpers'));

const { getAuthState, takeSnapshot } = require('./lib/auth-snapshot');
const sessions = require('./lib/session');

// ─── Argument Parsing ────────────────────────────────────────────────

function parseArgs(argv) {
  const args = argv.slice(2);
  const result = { command: null, positional: [], flags: {} };

  for (const arg of args) {
    if (arg.startsWith('--')) {
      const [key, ...rest] = arg.slice(2).split('=');
      result.flags[key] = rest.length > 0 ? rest.join('=') : true;
    } else if (!result.command) {
      result.command = arg;
    } else {
      result.positional.push(arg);
    }
  }

  return result;
}

// ─── Script Wrapper ──────────────────────────────────────────────────

/**
 * Wrap user script so it receives pre-initialized { browser, context, page, helpers }
 */
function wrapScript(code) {
  // If code already has require('playwright'), treat as complete script
  if (code.includes("require('playwright')") || code.includes('require("playwright")')) {
    return code;
  }

  return `
module.exports = async function({ browser, context, page, helpers }) {
  ${code}
};
`;
}

// ─── Command: run / run-inline ───────────────────────────────────────

async function cmdRun({ positional, flags }) {
  const isInline = false;
  const scriptPath = positional[0];
  const sessionName = flags.session || null;
  const debugMode = flags.debug || false;
  const headed = flags.headed || false;

  if (!scriptPath) {
    console.error('Usage: node browse.js run <script.js> [--session=name] [--debug] [--headed]');
    process.exit(1);
  }

  const absPath = path.resolve(scriptPath);
  if (!fs.existsSync(absPath)) {
    console.error(`Script not found: ${absPath}`);
    process.exit(1);
  }

  const rawCode = fs.readFileSync(absPath, 'utf8');
  const cdpMode = flags.cdp || false;
  await executeCode(rawCode, { sessionName, debugMode, headed, cdpMode });
}

async function cmdRunInline({ positional, flags }) {
  const code = positional.join(' ');
  if (!code) {
    console.error('Usage: node browse.js run-inline \'<code>\' [--session=name] [--debug] [--headed]');
    process.exit(1);
  }

  const sessionName = flags.session || null;
  const debugMode = flags.debug || false;
  const headed = flags.headed || false;
  const cdpMode = flags.cdp || false;

  await executeCode(code, { sessionName, debugMode, headed, cdpMode });
}

async function executeCode(rawCode, { sessionName, debugMode, headed, cdpMode }) {
  let browser, context, page;
  let shouldClose = true;
  let isCDP = false;

  try {
    if (cdpMode) {
      // CDP Direct Mode - connect to running debug Chrome via CDP
      // Full session auth (works for Google, etc. where cookie injection fails)
      const cdpUrl = process.env.CHROME_CDP_URL || 'http://127.0.0.1:9222';
      console.log(`Connecting to debug Chrome via CDP (${cdpUrl})...`);

      try {
        browser = await chromium.connectOverCDP(cdpUrl);
      } catch (e) {
        if (e.message.includes('ECONNREFUSED') || e.message.includes('connect')) {
          console.error('Debug Chrome not running. Start it with: chrome-debug');
          console.error('Then log into the sites you need in that browser window.');
          process.exit(1);
        }
        throw e;
      }

      const contexts = browser.contexts();
      if (contexts.length === 0) {
        throw new Error('No browser contexts found in debug Chrome');
      }
      context = contexts[0];

      // Use existing page or create new one
      const pages = context.pages();
      page = pages[0] || await context.newPage();

      shouldClose = false; // Never close the debug Chrome
      isCDP = true;
      console.log(`Connected. ${pages.length} existing tab(s).`);

    } else {
      // Get auth state if debug mode
      let storageState = null;
      if (debugMode) {
        console.log('Fetching auth state from debug Chrome...');
        storageState = await getAuthState();
      }

      if (sessionName) {
        // Named session mode
        const existing = sessions.getSession(sessionName);
        if (existing) {
          // Reconnect
          console.log(`Reconnecting to session "${sessionName}"...`);
          ({ browser, context, page } = await sessions.reconnectSession(sessionName));
          shouldClose = false; // Don't close named sessions after execution
        } else {
          // Create new session (daemon stays alive in background)
          console.log(`Creating session "${sessionName}"...`);
          ({ browser, context, page } = await sessions.createSession({
            name: sessionName,
            headed,
            storageState
          }));
          shouldClose = false; // Named sessions persist
        }
      } else {
        // Ephemeral mode - launch and close after execution
        browser = await chromium.launch({
          headless: !headed,
          args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        const contextOpts = {};
        if (storageState) contextOpts.storageState = storageState;
        context = await browser.newContext(contextOpts);
        page = await context.newPage();
      }
    }

    // Wrap and execute user code
    const wrappedCode = wrapScript(rawCode);
    const tempFile = path.join(__dirname, `.temp-${Date.now()}.js`);

    try {
      fs.writeFileSync(tempFile, wrappedCode, 'utf8');
      const userFn = require(tempFile);

      if (typeof userFn === 'function') {
        await userFn({ browser, context, page, helpers });
      }
      // If not a function (complete script), it already executed via require
    } finally {
      // Clean up temp file
      try { fs.unlinkSync(tempFile); } catch {}
    }

    console.log('Done.');
  } catch (error) {
    console.error('Execution error:', error.message);
    if (error.stack) console.error(error.stack);
    process.exitCode = 1;
  } finally {
    if (isCDP && browser) {
      // CDP mode: disconnect without closing the browser
      try { await browser.close(); } catch {} // close() on CDP just disconnects
    } else if (shouldClose && browser) {
      // Ephemeral mode: shut down the browser
      await browser.close().catch(() => {});
    } else if (!shouldClose && !isCDP) {
      // Named sessions: force exit to release the WebSocket without
      // calling browser.close() (which would destroy server-side contexts).
      // The daemon process keeps the browser alive independently.
      process.exit(process.exitCode || 0);
    }
  }
}

// ─── Command: sessions ───────────────────────────────────────────────

function cmdSessions() {
  const active = sessions.listSessions();
  const names = Object.keys(active);

  if (names.length === 0) {
    console.log('No active sessions');
    return;
  }

  console.log(`Active sessions (${names.length}):\n`);
  for (const [name, info] of Object.entries(active)) {
    console.log(`  ${name}`);
    console.log(`    PID: ${info.pid} | Mode: ${info.mode} | Created: ${info.createdAt}`);
  }
}

// ─── Command: close ──────────────────────────────────────────────────

async function cmdClose({ positional, flags }) {
  if (flags.all) {
    await sessions.closeAllSessions();
  } else if (positional[0]) {
    await sessions.closeSession(positional[0]);
  } else {
    console.error('Usage: node browse.js close [name|--all]');
    process.exit(1);
  }
}

// ─── Command: snapshot ───────────────────────────────────────────────

async function cmdSnapshot() {
  console.log('Taking fresh auth snapshot from debug Chrome...');
  try {
    await takeSnapshot();
    console.log('Snapshot complete.');
  } catch (error) {
    console.error('Snapshot failed:', error.message);
    process.exit(1);
  }
}

// ─── Main ────────────────────────────────────────────────────────────

async function main() {
  const parsed = parseArgs(process.argv);

  switch (parsed.command) {
    case 'run':
      await cmdRun(parsed);
      break;
    case 'run-inline':
      await cmdRunInline(parsed);
      break;
    case 'sessions':
      cmdSessions();
      break;
    case 'close':
      await cmdClose(parsed);
      break;
    case 'snapshot':
      await cmdSnapshot();
      break;
    default:
      console.log('browse-use - Headless browser automation\n');
      console.log('Commands:');
      console.log('  run <script.js> [--session=name] [--debug] [--headed] [--cdp]');
      console.log('  run-inline \'<code>\' [--session=name] [--debug] [--headed] [--cdp]');
      console.log('  sessions                    List active sessions');
      console.log('  close [name|--all]          Close session(s)');
      console.log('  snapshot                    Refresh auth snapshot');
      process.exit(parsed.command ? 1 : 0);
  }
}

main().catch(error => {
  console.error('Fatal:', error.message);
  process.exit(1);
});
