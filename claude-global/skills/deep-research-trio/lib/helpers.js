/**
 * Browser helpers for Deep Research Trio
 * Extended from playwright-skill/lib/helpers.js
 */

const { chromium } = require('playwright');
const { CDP_URL } = require('./config');

/**
 * Connect to user's running Chrome via CDP (Chrome DevTools Protocol)
 * This shares ALL login sessions from user's actual browser
 */
async function connectToChrome() {
  try {
    const browser = await chromium.connectOverCDP(CDP_URL);
    const contexts = browser.contexts();

    if (contexts.length === 0) {
      throw new Error('No browser contexts found');
    }

    const context = contexts[0];
    console.log('🔐 Connected to Chrome via CDP');

    return { browser, context };
  } catch (e) {
    if (e.message.includes('ECONNREFUSED') || e.message.includes('connect')) {
      console.error('❌ Chrome 未以调试模式运行');
      console.error('');
      console.error('启动方式：在终端运行 chrome-debug');
      console.error('');
      console.error('首次使用需在该 Chrome 中登录 Google/OpenAI/Anthropic 账号');
    }
    throw e;
  }
}

/**
 * Create a new tab in the browser context
 */
async function createTab(context) {
  const page = await context.newPage();
  page.setDefaultTimeout(30000);
  return page;
}

/**
 * Safe click with retry logic
 */
async function safeClick(page, selector, options = {}) {
  const maxRetries = options.retries || 3;
  const retryDelay = options.retryDelay || 1000;

  for (let i = 0; i < maxRetries; i++) {
    try {
      await page.waitForSelector(selector, {
        state: 'visible',
        timeout: options.timeout || 5000
      });
      await page.click(selector, {
        force: options.force || false,
        timeout: options.timeout || 5000
      });
      return true;
    } catch (e) {
      if (i === maxRetries - 1) {
        if (options.optional) {
          console.log(`  ⚠️ Optional click failed: ${selector}`);
          return false;
        }
        throw e;
      }
      await page.waitForTimeout(retryDelay);
    }
  }
}

/**
 * Safe text input
 */
async function safeType(page, selector, text, options = {}) {
  await page.waitForSelector(selector, {
    state: 'visible',
    timeout: options.timeout || 10000
  });

  // Try fill first (faster), fallback to type (more reliable)
  try {
    await page.fill(selector, text);
  } catch (e) {
    // For contenteditable elements, use keyboard
    await page.click(selector);
    await page.keyboard.type(text, { delay: options.delay || 50 });
  }
}

/**
 * Take screenshot with timestamp
 */
async function takeScreenshot(page, name, outputDir) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `${name}-${timestamp}.png`;
  const filepath = require('path').join(outputDir, filename);

  await page.screenshot({
    path: filepath,
    fullPage: false
  });

  console.log(`📸 Screenshot saved: ${filename}`);
  return filepath;
}

/**
 * Extract text content from an element
 */
async function extractText(page, selector, options = {}) {
  try {
    await page.waitForSelector(selector, {
      timeout: options.timeout || 5000
    });
    return await page.$eval(selector, el => el.textContent?.trim() || '');
  } catch (e) {
    return '';
  }
}

/**
 * Check if element exists and is visible
 */
async function elementExists(page, selector, timeout = 3000) {
  try {
    await page.waitForSelector(selector, { state: 'visible', timeout });
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Wait for any of multiple selectors
 */
async function waitForAny(page, selectors, timeout = 10000) {
  const promises = selectors.map(selector =>
    page.waitForSelector(selector, { state: 'visible', timeout })
      .then(() => selector)
      .catch(() => null)
  );

  const result = await Promise.race(promises);
  if (!result) {
    throw new Error(`None of selectors found: ${selectors.join(', ')}`);
  }
  return result;
}

module.exports = {
  connectToChrome,
  createTab,
  safeClick,
  safeType,
  takeScreenshot,
  extractText,
  elementExists,
  waitForAny
};
