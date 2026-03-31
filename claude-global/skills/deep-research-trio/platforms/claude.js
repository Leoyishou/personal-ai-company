/**
 * Claude Research Mode Platform Handler
 */

const { BasePlatform } = require('./base-platform');
const { safeClick, elementExists } = require('../lib/helpers');

class ClaudePlatform extends BasePlatform {
  constructor(page, config) {
    super(page, config);
  }

  async navigate() {
    console.log(`  📍 Navigating to Claude...`);
    await this.page.goto('https://claude.ai/new', {
      waitUntil: 'domcontentloaded',
      timeout: this.timeouts.navigation
    });
    await this.page.waitForTimeout(3000);
  }

  async checkLogin() {
    try {
      const loginSelectors = [
        '.ProseMirror',                     // Editor (logged in only)
        'fieldset',                         // UI form elements
        'button[data-testid="user-menu"]',
        'img[alt*="Profile"]',
      ];

      for (const selector of loginSelectors) {
        if (await elementExists(this.page, selector, 3000)) {
          console.log(`  🔐 Claude: ✅ Logged in`);
          return true;
        }
      }

      console.log(`  🔐 Claude: ❌ Not logged in`);
      return false;
    } catch (e) {
      return false;
    }
  }

  async submitQuery(query) {
    console.log(`  📝 Submitting query to Claude...`);

    // Enable extended thinking if available
    await this.enableResearchMode();

    // Find input area - Claude uses ProseMirror
    const inputSelectors = [
      '[contenteditable="true"].ProseMirror',
      'div[data-placeholder]',
      '.ProseMirror',
      '[contenteditable="true"]'
    ];

    let inputFound = false;
    for (const selector of inputSelectors) {
      try {
        const input = await this.page.$(selector);
        if (input) {
          await input.click();
          await this.page.keyboard.type(query, { delay: 30 });
          inputFound = true;
          break;
        }
      } catch (e) {
        continue;
      }
    }

    if (!inputFound) {
      throw new Error('Could not find Claude input field');
    }

    // Submit
    await this.page.waitForTimeout(500);

    const submitSelectors = [
      'button[aria-label="Send Message"]',
      'button:has(svg[data-icon="arrow-up"])',
      'button[type="submit"]'
    ];

    let submitted = false;
    for (const selector of submitSelectors) {
      try {
        if (await elementExists(this.page, selector, 1000)) {
          await safeClick(this.page, selector, { optional: true });
          submitted = true;
          break;
        }
      } catch (e) {
        continue;
      }
    }

    if (!submitted) {
      await this.page.keyboard.press('Enter');
    }

    console.log(`  ✅ Query submitted to Claude`);
  }

  async enableResearchMode() {
    try {
      // Try to enable Extended Thinking or Research mode
      const toggleSelectors = [
        'button[aria-label*="Extended thinking"]',
        'button[aria-label*="Research"]',
        '[data-testid="extended-thinking-toggle"]',
        'button:has-text("Extended")'
      ];

      for (const selector of toggleSelectors) {
        if (await elementExists(this.page, selector, 2000)) {
          await safeClick(this.page, selector, { optional: true });
          console.log(`  🔬 Extended thinking/Research mode enabled`);
          await this.page.waitForTimeout(500);
          return true;
        }
      }

      console.log(`  ⚠️ Extended thinking toggle not found, using default mode`);
      return false;
    } catch (e) {
      return false;
    }
  }

  async waitForComplete(options = {}) {
    const { onProgress } = options;
    const startTime = Date.now();

    console.log(`  ⏳ Waiting for Claude response...`);

    const thinkingSelectors = [
      '[data-is-streaming="true"]',
      '.thinking-indicator',
      '.animate-pulse',
      'button[aria-label="Stop Response"]'
    ];

    const responseSelectors = [
      '[data-is-streaming="false"] .prose',
      '.message-content',
      '[data-testid="assistant-message"]',
      '.prose'
    ];

    let lastContent = '';
    let stableCount = 0;
    const requiredStable = 3;

    while (true) {
      const elapsed = Date.now() - startTime;

      if (elapsed > this.timeouts.researchComplete) {
        console.log('');
        return { status: 'timeout', elapsed };
      }

      // Check if still streaming
      let isStreaming = false;
      for (const selector of thinkingSelectors) {
        if (await elementExists(this.page, selector, 500)) {
          isStreaming = true;
          break;
        }
      }

      if (isStreaming) {
        stableCount = 0;
        const mins = Math.floor(elapsed / 60000);
        const secs = Math.floor((elapsed % 60000) / 1000);
        process.stdout.write(`\r  ⏳ Claude: Thinking... (${mins}m ${secs}s)     `);
        await this.page.waitForTimeout(this.timeouts.pollInterval);
        continue;
      }

      // Get content
      let content = '';
      for (const selector of responseSelectors) {
        try {
          const elements = await this.page.$$(selector);
          if (elements.length > 0) {
            content = await elements[elements.length - 1].textContent() || '';
            if (content.length > 100) break;
          }
        } catch (e) {
          continue;
        }
      }

      if (content && content === lastContent) {
        stableCount++;
        if (stableCount >= requiredStable) {
          console.log('');
          return { status: 'success', elapsed, content };
        }
      } else if (content) {
        stableCount = 0;
        lastContent = content;
      }

      const mins = Math.floor(elapsed / 60000);
      const secs = Math.floor((elapsed % 60000) / 1000);
      process.stdout.write(`\r  ⏳ Claude: Checking ${stableCount}/${requiredStable} (${mins}m ${secs}s)     `);

      if (onProgress) {
        onProgress({ stage: 'checking', elapsed, stableCount, contentLength: content.length });
      }

      await this.page.waitForTimeout(this.timeouts.pollInterval);
    }
  }

  async extractResult() {
    try {
      const responseSelectors = [
        '[data-is-streaming="false"] .prose',
        '.message-content',
        '[data-testid="assistant-message"]',
        '.prose'
      ];

      let fullText = '';
      for (const selector of responseSelectors) {
        try {
          const elements = await this.page.$$(selector);
          if (elements.length > 0) {
            fullText = await elements[elements.length - 1].textContent() || '';
            if (fullText.length > 100) break;
          }
        } catch (e) {
          continue;
        }
      }

      const summary = fullText.slice(0, 500) + (fullText.length > 500 ? '...' : '');
      const citations = await this.extractCitations();

      return { summary, fullText, citations };
    } catch (e) {
      return { summary: '', fullText: '', citations: [], error: e.message };
    }
  }

  async extractCitations() {
    try {
      const citations = await this.page.$$eval('.prose a[href^="http"]', els =>
        els.map(el => ({
          title: el.textContent?.trim() || '',
          url: el.href
        })).filter(c =>
          c.url &&
          !c.url.includes('claude.ai') &&
          !c.url.includes('anthropic.com')
        )
      );
      return citations.slice(0, 20);
    } catch (e) {
      return [];
    }
  }
}

module.exports = { ClaudePlatform };
