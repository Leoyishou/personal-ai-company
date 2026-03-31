#!/usr/bin/env node
/**
 * Browser daemon - runs as detached background process
 * Keeps a Playwright browser server alive for session reuse.
 *
 * Usage: node daemon.js [--headed] [--storageState=/path/to/state.json]
 * Outputs wsEndpoint to stdout, then stays alive.
 */

const path = require('path');
const fs = require('fs');

const PW_SKILL = path.join(__dirname, '..', '..', 'playwright-skill');
const { chromium } = require(path.join(PW_SKILL, 'node_modules', 'playwright'));

const args = process.argv.slice(2);
const headed = args.includes('--headed');

(async () => {
  try {
    const server = await chromium.launchServer({
      headless: !headed,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const wsEndpoint = server.wsEndpoint();

    // Output wsEndpoint so parent process can read it
    process.stdout.write(wsEndpoint + '\n');

    // If storageState was provided, create a context with it pre-loaded
    // so subsequent connections get the auth state
    const stateArg = args.find(a => a.startsWith('--storageState='));
    if (stateArg) {
      const statePath = stateArg.split('=')[1];
      if (fs.existsSync(statePath)) {
        const browser = await chromium.connect(wsEndpoint);
        const storageState = JSON.parse(fs.readFileSync(statePath, 'utf8'));
        await browser.newContext({ storageState });
        // Disconnect client, keep server alive
        await browser.close();
      }
    }

    // Handle graceful shutdown
    process.on('SIGTERM', async () => {
      await server.close();
      process.exit(0);
    });

    // Keep alive
  } catch (error) {
    process.stderr.write('Daemon error: ' + error.message + '\n');
    process.exit(1);
  }
})();
