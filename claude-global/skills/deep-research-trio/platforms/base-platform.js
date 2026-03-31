/**
 * Base Platform class for Deep Research
 * Abstract interface that all platforms must implement
 */

const { waitForStableContent } = require('../lib/stability-detector');
const { takeScreenshot } = require('../lib/helpers');
const { REPORT_CONFIG } = require('../lib/config');

class BasePlatform {
  constructor(page, config) {
    this.page = page;
    this.config = config;
    this.selectors = config.selectors;
    this.timeouts = config.timeouts;
    this.name = config.name;
  }

  /**
   * Navigate to the platform's deep research page
   */
  async navigate() {
    console.log(`  📍 Navigating to ${this.config.deepResearchUrl}`);
    await this.page.goto(this.config.deepResearchUrl, {
      waitUntil: 'domcontentloaded',
      timeout: this.timeouts.navigation
    });
    await this.page.waitForTimeout(2000);
  }

  /**
   * Check if user is logged in
   * @returns {Promise<boolean>}
   */
  async checkLogin() {
    try {
      const indicator = await this.page.$(this.selectors.loginIndicator);
      const isLoggedIn = !!indicator;
      console.log(`  🔐 Login status: ${isLoggedIn ? '✅' : '❌'}`);
      return isLoggedIn;
    } catch (e) {
      console.log(`  🔐 Login check failed: ${e.message}`);
      return false;
    }
  }

  /**
   * Submit the research query
   * Must be implemented by subclass
   */
  async submitQuery(query) {
    throw new Error('submitQuery must be implemented by subclass');
  }

  /**
   * Wait for research to complete
   * Uses stability detection by default
   */
  async waitForComplete(options = {}) {
    const { onProgress } = options;

    console.log(`  ⏳ Waiting for ${this.name} to complete...`);

    const result = await waitForStableContent(this.page, {
      contentSelector: this.selectors.responseContainer,
      thinkingSelector: this.selectors.thinkingIndicator,
      maxTimeout: this.timeouts.researchComplete,
      pollInterval: this.timeouts.pollInterval,
      onProgress: (progress) => {
        if (onProgress) {
          onProgress({
            platform: this.name,
            ...progress
          });
        }

        // Log progress periodically
        const mins = Math.floor(progress.elapsed / 60000);
        const secs = Math.floor((progress.elapsed % 60000) / 1000);
        if (progress.stage === 'thinking') {
          process.stdout.write(`\r  ⏳ ${this.name}: Thinking... (${mins}m ${secs}s)     `);
        } else {
          process.stdout.write(`\r  ⏳ ${this.name}: Checking stability ${progress.stableCount}/3 (${mins}m ${secs}s)     `);
        }
      }
    });

    console.log(''); // New line after progress

    if (result.status === 'success') {
      console.log(`  ✅ ${this.name} completed successfully`);
    } else if (result.status === 'timeout') {
      console.log(`  ⚠️ ${this.name} timed out with partial results`);
    } else {
      console.log(`  ⚠️ ${this.name}: ${result.message}`);
    }

    return result;
  }

  /**
   * Extract the research result
   * @returns {Promise<{summary: string, fullText: string, citations: Array}>}
   */
  async extractResult() {
    try {
      // Get all response elements
      const elements = await this.page.$$(this.selectors.responseContainer);

      if (elements.length === 0) {
        return { summary: '', fullText: '', citations: [] };
      }

      // Get the last response (most recent)
      const lastElement = elements[elements.length - 1];
      const fullText = await lastElement.textContent() || '';

      // Extract first 500 chars as summary
      const summary = fullText.slice(0, 500) + (fullText.length > 500 ? '...' : '');

      // Try to extract citations/links
      const citations = await this.extractCitations();

      return { summary, fullText, citations };
    } catch (e) {
      console.log(`  ⚠️ Error extracting result: ${e.message}`);
      return { summary: '', fullText: '', citations: [], error: e.message };
    }
  }

  /**
   * Extract citations from the response
   * Can be overridden by subclass for platform-specific extraction
   */
  async extractCitations() {
    try {
      const links = await this.page.$$eval(`${this.selectors.responseContainer} a[href]`, els =>
        els.map(el => ({
          title: el.textContent?.trim() || '',
          url: el.href
        })).filter(l => l.url && !l.url.startsWith('javascript:'))
      );
      return links;
    } catch (e) {
      return [];
    }
  }

  /**
   * Take a screenshot of current state
   */
  async screenshot(name) {
    return takeScreenshot(this.page, `${this.name.toLowerCase()}-${name}`, REPORT_CONFIG.outputDir);
  }
}

module.exports = { BasePlatform };
