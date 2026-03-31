/**
 * Gemini Deep Research Platform Handler
 */

const { BasePlatform } = require('./base-platform');
const { safeClick, safeType, elementExists } = require('../lib/helpers');

class GeminiPlatform extends BasePlatform {
  constructor(page, config) {
    super(page, config);
  }

  async navigate() {
    console.log(`  📍 Navigating to Gemini...`);
    await this.page.goto('https://gemini.google.com/app', {
      waitUntil: 'domcontentloaded',
      timeout: this.timeouts.navigation
    });
    await this.page.waitForTimeout(3000);
  }

  async checkLogin() {
    try {
      // Look for Google account avatar or profile button
      const loginSelectors = [
        'img[src*="googleusercontent"]',  // User avatar image
        'bard-sidenav-content',           // Logged-in sidebar
        'img[alt*="Google Account"]',
        'button[aria-label*="Google Account"]',
      ];

      for (const selector of loginSelectors) {
        if (await elementExists(this.page, selector, 3000)) {
          console.log(`  🔐 Gemini: ✅ Logged in`);
          return true;
        }
      }

      console.log(`  🔐 Gemini: ❌ Not logged in`);
      return false;
    } catch (e) {
      return false;
    }
  }

  async submitQuery(query) {
    console.log(`  📝 Submitting query to Gemini...`);

    // Wait for page to be ready
    await this.page.waitForTimeout(2000);

    // Step 1: Enable Deep Research mode FIRST (before typing)
    await this.enableDeepResearch();

    // Step 2: Find and fill the input area
    const inputSelectors = [
      'rich-textarea',
      '[contenteditable="true"]',
      'textarea[aria-label*="prompt"]',
      '.ql-editor'
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
      throw new Error('Could not find Gemini input field');
    }

    // Step 3: Submit
    await this.page.waitForTimeout(500);
    await this.page.keyboard.press('Enter');

    console.log(`  ✅ Query submitted to Gemini`);

    // Step 4: If Deep Research shows a plan, click "Start research" button
    await this.clickStartResearchIfNeeded();
  }

  async clickStartResearchIfNeeded() {
    try {
      // Check if page is still valid
      if (!this.page || this.page.isClosed()) {
        console.log(`  ⚠️ Page closed, skipping Start Research check`);
        return false;
      }

      // Wait for potential research plan to appear
      await this.page.waitForTimeout(5000);

      // Look for "Start research" / "开始研究" button
      const startResearchSelectors = [
        'button:has-text("开始研究")',
        'button:has-text("Start research")',
        'button:has-text("Start Research")',
        'button[aria-label*="Start research"]',
        // Blue primary button in the plan dialog
        'button[class*="primary"]:has-text("研究")',
        'button[class*="primary"]:has-text("research")',
      ];

      for (const selector of startResearchSelectors) {
        try {
          if (await elementExists(this.page, selector, 3000)) {
            await safeClick(this.page, selector, { optional: true });
            console.log(`  🚀 Clicked "Start Research" button`);
            await this.page.waitForTimeout(1000);
            return true;
          }
        } catch (e) {
          continue;
        }
      }

      // Fallback: find by visible text
      try {
        const buttons = await this.page.$$('button');
        for (const btn of buttons) {
          const text = await btn.textContent();
          if (text?.includes('开始研究') || text?.toLowerCase().includes('start research')) {
            await btn.click();
            console.log(`  🚀 Clicked "Start Research" button (via text match)`);
            await this.page.waitForTimeout(1000);
            return true;
          }
        }
      } catch (e) {}

      // No start button found - might be in normal mode
      return false;
    } catch (e) {
      console.log(`  ⚠️ Could not find Start Research button: ${e.message}`);
      return false;
    }
  }

  async enableDeepResearch() {
    try {
      // Step 1: Click "Tools" button to open the tools menu
      const toolsButtonSelectors = [
        'button:has-text("Tools")',
        'button[aria-label*="Tools"]',
        'div[role="button"]:has-text("Tools")',
        // Look for button with tools icon
        'button:has(mat-icon)',
      ];

      let menuOpened = false;
      for (const selector of toolsButtonSelectors) {
        try {
          if (await elementExists(this.page, selector, 2000)) {
            await safeClick(this.page, selector, { optional: true });
            await this.page.waitForTimeout(1000);
            menuOpened = true;
            break;
          }
        } catch (e) {
          continue;
        }
      }

      // Fallback: find by visible text "Tools"
      if (!menuOpened) {
        try {
          const buttons = await this.page.$$('button, div[role="button"]');
          for (const btn of buttons) {
            const text = await btn.textContent();
            if (text?.trim() === 'Tools' || text?.includes('Tools')) {
              await btn.click();
              await this.page.waitForTimeout(1000);
              menuOpened = true;
              break;
            }
          }
        } catch (e) {}
      }

      if (!menuOpened) {
        console.log(`  ⚠️ Could not find Tools button`);
        return false;
      }

      // Step 2: Click "Deep Research" in the dropdown menu
      const deepResearchSelectors = [
        'button:has-text("Deep Research")',
        'div[role="menuitem"]:has-text("Deep Research")',
        'li:has-text("Deep Research")',
        '[role="option"]:has-text("Deep Research")',
        // Partial match
        'button:has-text("Deep")',
        'div:text-is("Deep Research")',
      ];

      for (const selector of deepResearchSelectors) {
        try {
          if (await elementExists(this.page, selector, 2000)) {
            await safeClick(this.page, selector, { optional: true });
            console.log(`  🔬 Deep Research mode enabled`);
            await this.page.waitForTimeout(1000);
            return true;
          }
        } catch (e) {
          continue;
        }
      }

      // Fallback: find by visible text in menu
      try {
        const menuItems = await this.page.$$('[role="menuitem"], [role="option"], li, button');
        for (const item of menuItems) {
          const text = await item.textContent();
          if (text?.includes('Deep Research')) {
            await item.click();
            console.log(`  🔬 Deep Research mode enabled (via text match)`);
            await this.page.waitForTimeout(1000);
            return true;
          }
        }
      } catch (e) {}

      // Close menu if not found
      await this.page.keyboard.press('Escape');
      console.log(`  ⚠️ Deep Research option not found in Tools menu`);
      return false;
    } catch (e) {
      console.log(`  ⚠️ Could not enable Deep Research: ${e.message}`);
      return false;
    }
  }

  async waitForComplete(options = {}) {
    const { onProgress } = options;
    const startTime = Date.now();

    console.log(`  ⏳ Waiting for Gemini response...`);

    // Gemini-specific thinking indicators
    const thinkingSelectors = [
      '[data-research-status="running"]',
      '.loading-spinner',
      '.thinking-indicator',
      'model-response:has(.loading)'
    ];

    // Response container selectors
    const responseSelectors = [
      'model-response .response-content',
      '[data-message-author="model"]',
      '.model-response-text',
      'message-content'
    ];

    let lastContent = '';
    let stableCount = 0;
    const requiredStable = 3;

    while (true) {
      const elapsed = Date.now() - startTime;

      // Check timeout
      if (elapsed > this.timeouts.researchComplete) {
        console.log('');
        return { status: 'timeout', elapsed };
      }

      // Check if still thinking
      let isThinking = false;
      for (const selector of thinkingSelectors) {
        if (await elementExists(this.page, selector, 500)) {
          isThinking = true;
          break;
        }
      }

      if (isThinking) {
        stableCount = 0;
        const mins = Math.floor(elapsed / 60000);
        const secs = Math.floor((elapsed % 60000) / 1000);
        process.stdout.write(`\r  ⏳ Gemini: Processing... (${mins}m ${secs}s)     `);
        await this.page.waitForTimeout(this.timeouts.pollInterval);
        continue;
      }

      // Try to get content
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
      process.stdout.write(`\r  ⏳ Gemini: Checking ${stableCount}/${requiredStable} (${mins}m ${secs}s)     `);

      if (onProgress) {
        onProgress({ stage: 'checking', elapsed, stableCount, contentLength: content.length });
      }

      await this.page.waitForTimeout(this.timeouts.pollInterval);
    }
  }

  async extractResult() {
    try {
      const responseSelectors = [
        'model-response .response-content',
        '[data-message-author="model"]',
        '.model-response-text'
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
      // Gemini shows citations in a specific format
      const citations = await this.page.$$eval('a[href^="http"]', els =>
        els.map(el => ({
          title: el.textContent?.trim() || el.title || '',
          url: el.href
        })).filter(c =>
          c.url &&
          !c.url.includes('google.com/app') &&
          !c.url.includes('gemini.google.com')
        )
      );
      return citations.slice(0, 20); // Limit to 20 citations
    } catch (e) {
      return [];
    }
  }
}

module.exports = { GeminiPlatform };
