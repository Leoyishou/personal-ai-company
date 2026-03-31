/**
 * Parallel Executor for Deep Research Trio
 * Manages concurrent execution across multiple platforms
 */

const { connectToChrome, createTab } = require('./helpers');
const { PLATFORMS, REPORT_CONFIG } = require('./config');
const fs = require('fs');
const path = require('path');

class ParallelExecutor {
  constructor(options = {}) {
    this.platforms = options.platforms || ['gemini', 'chatgpt', 'claude'];
    this.query = options.query;
    this.browser = null;
    this.context = null;
    this.results = new Map();
    this.startTime = null;
    this.onProgress = options.onProgress || (() => {});
  }

  /**
   * Initialize browser connection and create tabs
   */
  async initialize() {
    console.log('🔌 Connecting to Chrome...');
    const { browser, context } = await connectToChrome();
    this.browser = browser;
    this.context = context;

    // Ensure output directory exists
    if (!fs.existsSync(REPORT_CONFIG.outputDir)) {
      fs.mkdirSync(REPORT_CONFIG.outputDir, { recursive: true });
    }

    console.log('✅ Connected successfully\n');
  }

  /**
   * Check login status for all platforms
   */
  async checkLoginStatus() {
    const statuses = {};

    for (const platformKey of this.platforms) {
      const config = PLATFORMS[platformKey];
      if (!config) continue;

      const page = await createTab(this.context);

      try {
        await page.goto(config.url, { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        // Check for login indicator
        const isLoggedIn = await page.$(config.selectors.loginIndicator);
        statuses[platformKey] = {
          name: config.name,
          loggedIn: !!isLoggedIn,
          url: config.url
        };

        console.log(`${config.name}: ${isLoggedIn ? '✅ Logged in' : '❌ Not logged in'}`);
      } catch (e) {
        statuses[platformKey] = {
          name: config.name,
          loggedIn: false,
          error: e.message
        };
        console.log(`${config.name}: ❌ Error - ${e.message}`);
      } finally {
        await page.close();
      }
    }

    return statuses;
  }

  /**
   * Execute deep research on a single platform
   */
  async executePlatform(platformKey, PlatformClass) {
    const config = PLATFORMS[platformKey];
    const page = await createTab(this.context);

    const platform = new PlatformClass(page, config);

    try {
      console.log(`\n🚀 Starting ${config.name}...`);

      // Navigate to platform
      await platform.navigate();

      // Check login
      const isLoggedIn = await platform.checkLogin();
      if (!isLoggedIn) {
        return {
          platform: platformKey,
          status: 'not_logged_in',
          error: `Not logged in to ${config.name}. Please login in the Debug Chrome.`
        };
      }

      // Submit query
      await platform.submitQuery(this.query);

      // Wait for completion with progress updates
      const result = await platform.waitForComplete({
        onProgress: (progress) => {
          this.onProgress({ platform: platformKey, ...progress });
        }
      });

      // Extract result
      const extracted = await platform.extractResult();

      return {
        platform: platformKey,
        name: config.name,
        status: result.status,
        timing: {
          startTime: this.startTime,
          endTime: Date.now(),
          durationMinutes: Math.round((Date.now() - this.startTime) / 60000)
        },
        content: extracted
      };

    } catch (e) {
      console.error(`❌ ${config.name} error:`, e.message);

      // Take error screenshot
      try {
        const screenshotPath = path.join(REPORT_CONFIG.outputDir, `error-${platformKey}-${Date.now()}.png`);
        await page.screenshot({ path: screenshotPath });
        console.log(`📸 Error screenshot: ${screenshotPath}`);
      } catch (se) {
        // Ignore screenshot errors
      }

      return {
        platform: platformKey,
        name: config.name,
        status: 'failed',
        error: e.message
      };
    } finally {
      // Don't close page yet - might need for debugging
    }
  }

  /**
   * Execute deep research on all platforms in parallel
   */
  async executeAll(platformClasses) {
    this.startTime = Date.now();

    console.log('═'.repeat(50));
    console.log(`🔬 Deep Research Trio`);
    console.log(`📝 Query: "${this.query}"`);
    console.log(`🎯 Platforms: ${this.platforms.join(', ')}`);
    console.log('═'.repeat(50));

    // Filter to only available platforms
    const availablePlatforms = this.platforms.filter(p => platformClasses[p]);

    if (availablePlatforms.length === 0) {
      throw new Error('No platform classes provided');
    }

    // Execute all platforms in parallel using Promise.allSettled
    const promises = availablePlatforms.map(platformKey =>
      this.executePlatform(platformKey, platformClasses[platformKey])
    );

    const results = await Promise.allSettled(promises);

    // Process results
    const processedResults = results.map((result, index) => {
      const platformKey = availablePlatforms[index];

      if (result.status === 'fulfilled') {
        this.results.set(platformKey, result.value);
        return result.value;
      } else {
        const errorResult = {
          platform: platformKey,
          name: PLATFORMS[platformKey]?.name || platformKey,
          status: 'failed',
          error: result.reason?.message || 'Unknown error'
        };
        this.results.set(platformKey, errorResult);
        return errorResult;
      }
    });

    return processedResults;
  }

  /**
   * Get summary of results
   */
  getSummary() {
    const summary = {
      total: this.results.size,
      success: 0,
      partial: 0,
      failed: 0,
      platforms: {}
    };

    for (const [key, result] of this.results) {
      summary.platforms[key] = {
        name: result.name,
        status: result.status,
        duration: result.timing?.durationMinutes
      };

      if (result.status === 'success') summary.success++;
      else if (result.status === 'partial' || result.status === 'timeout') summary.partial++;
      else summary.failed++;
    }

    return summary;
  }

  /**
   * Clean up resources
   */
  async cleanup() {
    if (this.browser) {
      // Just disconnect, don't close user's browser
      await this.browser.close();
      console.log('\n📤 Disconnected from Chrome');
    }
  }
}

module.exports = { ParallelExecutor };
