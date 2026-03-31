/**
 * Auth Snapshot - Extract storageState from debug Chrome via CDP
 *
 * Flow:
 * 1. Connect to debug Chrome (port 9222) via CDP
 * 2. Call context.storageState() to export cookies + localStorage
 * 3. Save to data/snapshots/auth-{timestamp}.json
 * 4. Cache with 1-hour TTL
 */

const fs = require('fs');
const path = require('path');

const SNAPSHOTS_DIR = path.join(__dirname, '..', 'data', 'snapshots');
const CACHE_TTL_MS = 60 * 60 * 1000; // 1 hour
const CDP_URL = process.env.CHROME_CDP_URL || 'http://127.0.0.1:9222';

// Resolve playwright from the sibling playwright-skill
const PW_SKILL = path.join(__dirname, '..', '..', 'playwright-skill');
const { chromium } = require(path.join(PW_SKILL, 'node_modules', 'playwright'));

/**
 * Find the latest snapshot file
 * @returns {{ path: string, timestamp: number } | null}
 */
function findLatestSnapshot() {
  if (!fs.existsSync(SNAPSHOTS_DIR)) return null;

  const files = fs.readdirSync(SNAPSHOTS_DIR)
    .filter(f => f.startsWith('auth-') && f.endsWith('.json'))
    .sort()
    .reverse();

  if (files.length === 0) return null;

  const latest = files[0];
  // Extract timestamp from filename: auth-{timestamp}.json
  const match = latest.match(/auth-(\d+)\.json/);
  const timestamp = match ? parseInt(match[1], 10) : 0;

  return {
    path: path.join(SNAPSHOTS_DIR, latest),
    timestamp
  };
}

/**
 * Check if cached snapshot is still valid
 */
function getCachedSnapshot() {
  const latest = findLatestSnapshot();
  if (!latest) return null;

  const age = Date.now() - latest.timestamp;
  if (age < CACHE_TTL_MS) {
    return JSON.parse(fs.readFileSync(latest.path, 'utf8'));
  }

  return null;
}

/**
 * Take a fresh auth snapshot from debug Chrome
 * @returns {Promise<Object>} storageState object
 */
async function takeSnapshot() {
  let browser;
  try {
    browser = await chromium.connectOverCDP(CDP_URL);
    const contexts = browser.contexts();

    if (contexts.length === 0) {
      throw new Error('No browser contexts found in debug Chrome');
    }

    const context = contexts[0];
    const state = await context.storageState();

    // Save snapshot
    fs.mkdirSync(SNAPSHOTS_DIR, { recursive: true });
    const filename = `auth-${Date.now()}.json`;
    const filepath = path.join(SNAPSHOTS_DIR, filename);
    fs.writeFileSync(filepath, JSON.stringify(state, null, 2));

    // Clean old snapshots (keep last 3)
    const files = fs.readdirSync(SNAPSHOTS_DIR)
      .filter(f => f.startsWith('auth-') && f.endsWith('.json'))
      .sort()
      .reverse();

    for (const old of files.slice(3)) {
      fs.unlinkSync(path.join(SNAPSHOTS_DIR, old));
    }

    console.log(`Auth snapshot saved: ${filename} (${state.cookies.length} cookies, ${state.origins.length} origins)`);
    return state;
  } finally {
    if (browser) {
      await browser.close(); // Just disconnects, doesn't close Chrome
    }
  }
}

/**
 * Get auth storageState - cached or fresh
 * @param {boolean} forceRefresh - Force a new snapshot
 * @returns {Promise<Object>} storageState object
 */
async function getAuthState(forceRefresh = false) {
  if (!forceRefresh) {
    const cached = getCachedSnapshot();
    if (cached) {
      console.log('Using cached auth snapshot (< 1 hour old)');
      return cached;
    }
  }

  try {
    return await takeSnapshot();
  } catch (e) {
    if (e.message.includes('ECONNREFUSED') || e.message.includes('connect')) {
      // Debug Chrome not running, try expired snapshot as fallback
      const latest = findLatestSnapshot();
      if (latest) {
        console.warn('Debug Chrome not running. Using expired snapshot as fallback.');
        return JSON.parse(fs.readFileSync(latest.path, 'utf8'));
      }
      console.warn('Debug Chrome not running and no cached snapshots found.');
      console.warn('Start debug Chrome: chrome-debug');
      console.warn('Continuing without auth state...');
      return null;
    }
    throw e;
  }
}

module.exports = { getAuthState, takeSnapshot, findLatestSnapshot };
