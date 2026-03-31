/**
 * ChatGPT Deep Research Platform Handler
 */

const { BasePlatform } = require('./base-platform');
const { safeClick, elementExists } = require('../lib/helpers');

class ChatGPTPlatform extends BasePlatform {
  constructor(page, config) {
    super(page, config);
  }

  async navigate() {
    console.log(`  📍 Navigating to ChatGPT...`);
    // Navigate directly to research model
    await this.page.goto('https://chatgpt.com/?model=gpt-4o-mini', {
      waitUntil: 'domcontentloaded',
      timeout: this.timeouts.navigation
    });
    await this.page.waitForTimeout(3000);
  }

  async checkLogin() {
    try {
      const loginSelectors = [
        'nav',                              // Navigation bar (logged in only)
        '.text-token-text-secondary',       // Logged-in UI elements
        'button[data-testid="profile-button"]',
        'img[alt="User"]',
      ];

      for (const selector of loginSelectors) {
        if (await elementExists(this.page, selector, 3000)) {
          console.log(`  🔐 ChatGPT: ✅ Logged in`);
          return true;
        }
      }

      console.log(`  🔐 ChatGPT: ❌ Not logged in`);
      return false;
    } catch (e) {
      return false;
    }
  }

  async submitQuery(query) {
    console.log(`  📝 Submitting query to ChatGPT...`);

    // Try to enable Deep Research first
    await this.enableDeepResearch();

    // Wait for page to stabilize after mode change
    await this.page.waitForTimeout(2000);

    // Find input area - Deep Research mode has different input
    const inputSelectors = [
      // Deep Research mode specific
      'textarea[placeholder*="detailed report"]',
      'textarea[placeholder*="researching"]',
      'input[placeholder*="detailed report"]',
      // Standard ChatGPT input
      '#prompt-textarea',
      'textarea[data-id="root"]',
      '[contenteditable="true"]',
      'textarea[placeholder*="Message"]',
      // Fallback - any visible textarea
      'textarea',
    ];

    let inputFound = false;
    for (const selector of inputSelectors) {
      try {
        const input = await this.page.$(selector);
        if (input) {
          await input.click();

          // Clear and type
          await this.page.keyboard.selectAll();
          await this.page.keyboard.type(query, { delay: 30 });
          inputFound = true;
          break;
        }
      } catch (e) {
        continue;
      }
    }

    if (!inputFound) {
      throw new Error('Could not find ChatGPT input field');
    }

    // Submit
    await this.page.waitForTimeout(500);

    // Try click submit button or press Enter
    const submitSelectors = [
      'button[data-testid="send-button"]',
      'button[aria-label="Send prompt"]',
      'button[aria-label="Send message"]'
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

    console.log(`  ✅ Query submitted to ChatGPT`);
  }

  async enableDeepResearch() {
    try {
      // Step 1: Click the "+" button next to input field to open attachment menu
      const plusButtonSelectors = [
        'button[aria-label="Attach files"]',
        'button[aria-label="Add content"]',
        'button[data-testid="composer-attach-button"]',
        'button[class*="attach"]',
        // Generic + button near input
        'form button:has(svg)',
        'div[class*="composer"] button:first-child',
      ];

      let menuOpened = false;
      for (const selector of plusButtonSelectors) {
        try {
          const buttons = await this.page.$$(selector);
          for (const btn of buttons) {
            const text = await btn.textContent();
            const ariaLabel = await btn.getAttribute('aria-label');
            // Look for + button or attach button
            if (text === '+' || text === '' || ariaLabel?.includes('Attach') || ariaLabel?.includes('Add')) {
              await btn.click();
              await this.page.waitForTimeout(1000);
              menuOpened = true;
              break;
            }
          }
          if (menuOpened) break;
        } catch (e) {
          continue;
        }
      }

      // Fallback: try clicking any button with just "+" text
      if (!menuOpened) {
        try {
          const allButtons = await this.page.$$('button');
          for (const btn of allButtons) {
            const text = (await btn.textContent())?.trim();
            if (text === '+') {
              await btn.click();
              await this.page.waitForTimeout(1000);
              menuOpened = true;
              break;
            }
          }
        } catch (e) {}
      }

      if (!menuOpened) {
        console.log(`  ⚠️ Could not find + button to open menu`);
        return false;
      }

      // Step 2: Look for "Deep research" option in the dropdown menu
      const researchOptions = [
        'div[role="menuitem"]:has-text("Deep research")',
        'button:has-text("Deep research")',
        'li:has-text("Deep research")',
        '[role="option"]:has-text("Deep research")',
        // Text-based matching
        'div:text-is("Deep research")',
        'span:text-is("Deep research")',
      ];

      for (const opt of researchOptions) {
        try {
          if (await elementExists(this.page, opt, 2000)) {
            await safeClick(this.page, opt, { optional: true });
            console.log(`  🔬 Deep Research mode enabled`);
            await this.page.waitForTimeout(500);
            return true;
          }
        } catch (e) {
          continue;
        }
      }

      // Fallback: find by visible text
      try {
        const menuItems = await this.page.$$('[role="menuitem"], [role="option"], li, div[class*="menu"]');
        for (const item of menuItems) {
          const text = await item.textContent();
          if (text?.toLowerCase().includes('deep research')) {
            await item.click();
            console.log(`  🔬 Deep Research mode enabled (via text match)`);
            await this.page.waitForTimeout(500);
            return true;
          }
        }
      } catch (e) {}

      // Close dropdown if research not found
      await this.page.keyboard.press('Escape');
      console.log(`  ⚠️ Deep Research option not found in menu`);
      return false;
    } catch (e) {
      console.log(`  ⚠️ Could not enable Deep Research: ${e.message}`);
      return false;
    }
  }

  async waitForComplete(options = {}) {
    const { onProgress } = options;
    const startTime = Date.now();

    console.log(`  ⏳ Waiting for ChatGPT response...`);

    const thinkingSelectors = [
      '.result-streaming',
      '[data-message-author-role="assistant"].streaming',
      '.streaming-indicator',
      'button[aria-label="Stop generating"]'
    ];

    const responseSelectors = [
      '[data-message-author-role="assistant"] .markdown',
      '[data-message-author-role="assistant"]',
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

      // Check if streaming
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
        process.stdout.write(`\r  ⏳ ChatGPT: Generating... (${mins}m ${secs}s)     `);
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
      process.stdout.write(`\r  ⏳ ChatGPT: Checking ${stableCount}/${requiredStable} (${mins}m ${secs}s)     `);

      if (onProgress) {
        onProgress({ stage: 'checking', elapsed, stableCount, contentLength: content.length });
      }

      await this.page.waitForTimeout(this.timeouts.pollInterval);
    }
  }

  async extractResult() {
    try {
      const responseSelectors = [
        '[data-message-author-role="assistant"] .markdown',
        '[data-message-author-role="assistant"]',
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
      const citations = await this.page.$$eval('[data-message-author-role="assistant"] a[href^="http"]', els =>
        els.map(el => ({
          title: el.textContent?.trim() || '',
          url: el.href
        })).filter(c =>
          c.url &&
          !c.url.includes('chatgpt.com') &&
          !c.url.includes('openai.com')
        )
      );
      return citations.slice(0, 20);
    } catch (e) {
      return [];
    }
  }
}

module.exports = { ChatGPTPlatform };
