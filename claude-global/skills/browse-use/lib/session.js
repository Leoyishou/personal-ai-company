/**
 * Session Manager - Track and manage independent browser instances
 *
 * Uses a daemon process pattern:
 * - createSession() spawns a detached daemon.js process that holds the browser
 * - The daemon outputs wsEndpoint, then stays alive in background
 * - Main process connects via wsEndpoint, executes, disconnects
 * - Registry: data/sessions.json tracks PID + wsEndpoint
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const DATA_DIR = path.join(__dirname, '..', 'data');
const REGISTRY_PATH = path.join(DATA_DIR, 'sessions.json');
const DAEMON_SCRIPT = path.join(__dirname, 'daemon.js');

// Resolve playwright from the sibling playwright-skill
const PW_SKILL = path.join(__dirname, '..', '..', 'playwright-skill');
const { chromium } = require(path.join(PW_SKILL, 'node_modules', 'playwright'));

/**
 * Load session registry
 */
function loadRegistry() {
  if (!fs.existsSync(REGISTRY_PATH)) {
    return { sessions: {} };
  }
  try {
    return JSON.parse(fs.readFileSync(REGISTRY_PATH, 'utf8'));
  } catch {
    return { sessions: {} };
  }
}

/**
 * Save session registry
 */
function saveRegistry(registry) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.writeFileSync(REGISTRY_PATH, JSON.stringify(registry, null, 2));
}

/**
 * Check if a process is alive
 */
function isProcessAlive(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

/**
 * Clean dead sessions from registry
 */
function cleanRegistry() {
  const registry = loadRegistry();
  let cleaned = false;

  for (const [name, session] of Object.entries(registry.sessions)) {
    if (!isProcessAlive(session.pid)) {
      delete registry.sessions[name];
      cleaned = true;
    }
  }

  if (cleaned) saveRegistry(registry);
  return registry;
}

function registerSession(name, { pid, wsEndpoint, mode }) {
  const registry = loadRegistry();
  registry.sessions[name] = {
    pid,
    wsEndpoint,
    mode,
    createdAt: new Date().toISOString()
  };
  saveRegistry(registry);
}

function unregisterSession(name) {
  const registry = loadRegistry();
  delete registry.sessions[name];
  saveRegistry(registry);
}

function getSession(name) {
  const registry = cleanRegistry();
  return registry.sessions[name] || null;
}

function listSessions() {
  const registry = cleanRegistry();
  return registry.sessions;
}

/**
 * Spawn a detached daemon process that runs the browser server.
 * Returns the wsEndpoint once the daemon is ready.
 */
function spawnDaemon({ headed = false, storageStatePath = null }) {
  return new Promise((resolve, reject) => {
    const args = [DAEMON_SCRIPT];
    if (headed) args.push('--headed');
    if (storageStatePath) args.push(`--storageState=${storageStatePath}`);

    const child = spawn(process.execPath, args, {
      detached: true,
      stdio: ['ignore', 'pipe', 'pipe'],
      cwd: path.join(__dirname, '..')
    });

    let wsEndpoint = '';
    let stderr = '';
    const timeout = setTimeout(() => {
      child.kill();
      reject(new Error('Daemon startup timeout (10s)'));
    }, 10000);

    child.stdout.on('data', (data) => {
      wsEndpoint += data.toString();
      if (wsEndpoint.includes('\n')) {
        clearTimeout(timeout);
        wsEndpoint = wsEndpoint.trim();
        // Detach - allow parent to exit without killing daemon
        child.unref();
        child.stdout.destroy();
        child.stderr.destroy();
        resolve({ wsEndpoint, pid: child.pid });
      }
    });

    child.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    child.on('error', (err) => {
      clearTimeout(timeout);
      reject(err);
    });

    child.on('exit', (code) => {
      clearTimeout(timeout);
      if (!wsEndpoint.includes('ws://')) {
        reject(new Error(`Daemon exited with code ${code}: ${stderr}`));
      }
    });
  });
}

/**
 * Create a new browser session via daemon
 */
async function createSession({ name, headed = false, storageState = null }) {
  const existing = getSession(name);
  if (existing) {
    throw new Error(`Session "${name}" already exists (PID: ${existing.pid}). Close it first or use a different name.`);
  }

  // If storageState provided, write to temp file for daemon
  let storageStatePath = null;
  if (storageState) {
    storageStatePath = path.join(DATA_DIR, `_tmp_state_${Date.now()}.json`);
    fs.mkdirSync(DATA_DIR, { recursive: true });
    fs.writeFileSync(storageStatePath, JSON.stringify(storageState));
  }

  // Spawn daemon
  const { wsEndpoint, pid } = await spawnDaemon({ headed, storageStatePath });

  // Clean up temp state file
  if (storageStatePath) {
    try { fs.unlinkSync(storageStatePath); } catch {}
  }

  const mode = storageState ? 'debug' : 'normal';
  registerSession(name, { pid, wsEndpoint, mode });

  console.log(`Session "${name}" created (PID: ${pid}, mode: ${mode})`);

  // Connect and return browser/context/page for immediate use
  const browser = await chromium.connect(wsEndpoint);
  const contexts = browser.contexts();
  let context, page;

  if (contexts.length > 0) {
    // Daemon pre-created a context with storageState
    context = contexts[0];
    page = context.pages()[0] || await context.newPage();
  } else {
    context = await browser.newContext();
    page = await context.newPage();
  }

  return { browser, context, page };
}

/**
 * Reconnect to an existing session
 */
async function reconnectSession(name) {
  const session = getSession(name);
  if (!session) {
    throw new Error(`Session "${name}" not found or dead`);
  }

  const browser = await chromium.connect(session.wsEndpoint);
  const contexts = browser.contexts();
  const context = contexts[0] || await browser.newContext();
  const pages = context.pages();
  const page = pages[0] || await context.newPage();

  console.log(`Reconnected to session "${name}" (PID: ${session.pid})`);
  return { browser, context, page };
}

/**
 * Close a specific session (kills the daemon)
 */
async function closeSession(name) {
  const session = getSession(name);
  if (!session) {
    console.log(`Session "${name}" not found or already dead`);
    return;
  }

  // Kill the daemon process
  try {
    process.kill(session.pid, 'SIGTERM');
  } catch {
    // Already dead
  }

  unregisterSession(name);
  console.log(`Session "${name}" closed`);
}

/**
 * Close all sessions
 */
async function closeAllSessions() {
  const active = listSessions();
  const names = Object.keys(active);

  if (names.length === 0) {
    console.log('No active sessions');
    return;
  }

  for (const name of names) {
    await closeSession(name);
  }
  console.log(`Closed ${names.length} session(s)`);
}

module.exports = {
  createSession,
  reconnectSession,
  closeSession,
  closeAllSessions,
  listSessions,
  getSession,
  cleanRegistry
};
