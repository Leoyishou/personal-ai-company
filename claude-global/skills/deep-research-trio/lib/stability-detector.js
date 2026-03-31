/**
 * Stability Detector for Deep Research completion
 * Uses 3-consecutive-same pattern to detect completion
 */

const { STABILITY_CONFIG } = require('./config');

class StabilityDetector {
  constructor(options = {}) {
    this.requiredStableCount = options.requiredStableCount || STABILITY_CONFIG.requiredStableCount;
    this.pollInterval = options.pollInterval || STABILITY_CONFIG.pollInterval;
    this.maxIdleTime = options.maxIdleTime || STABILITY_CONFIG.maxIdleTime;

    this.lastContent = null;
    this.stableCount = 0;
    this.lastChangeTime = Date.now();
  }

  /**
   * Check if content is stable (3 consecutive same results)
   * @returns {boolean} true if stable, false if still changing
   */
  check(currentContent) {
    if (currentContent === this.lastContent) {
      this.stableCount++;

      if (this.stableCount >= this.requiredStableCount) {
        return true; // Stable!
      }
    } else {
      this.stableCount = 0;
      this.lastContent = currentContent;
      this.lastChangeTime = Date.now();
    }

    return false;
  }

  /**
   * Check if we've exceeded max idle time
   */
  isTimedOut() {
    return (Date.now() - this.lastChangeTime) > this.maxIdleTime;
  }

  /**
   * Reset the detector state
   */
  reset() {
    this.lastContent = null;
    this.stableCount = 0;
    this.lastChangeTime = Date.now();
  }

  /**
   * Get current stable count
   */
  getStableCount() {
    return this.stableCount;
  }
}

/**
 * Wait for content to stabilize with thinking state detection
 * @param {Object} page - Playwright page
 * @param {Object} options - Options including selectors and timeouts
 * @returns {Promise<{content: string, status: string}>}
 */
async function waitForStableContent(page, options) {
  const {
    contentSelector,
    thinkingSelector,
    maxTimeout = 3600000, // 60 minutes default
    pollInterval = 3000,
    onProgress
  } = options;

  const detector = new StabilityDetector({ pollInterval });
  const startTime = Date.now();

  while (true) {
    const elapsed = Date.now() - startTime;

    // Check max timeout
    if (elapsed > maxTimeout) {
      const content = await getContent(page, contentSelector);
      return {
        content,
        status: 'timeout',
        message: `Exceeded max timeout of ${maxTimeout / 60000} minutes`
      };
    }

    // Check if still thinking
    const isThinking = await isElementVisible(page, thinkingSelector);

    if (isThinking) {
      // Still processing, reset stability and wait
      detector.reset();
      if (onProgress) {
        onProgress({ stage: 'thinking', elapsed, stableCount: 0 });
      }
      await page.waitForTimeout(pollInterval);
      continue;
    }

    // Not thinking, check content stability
    const content = await getContent(page, contentSelector);

    if (!content) {
      // No content yet, wait
      await page.waitForTimeout(pollInterval);
      continue;
    }

    const isStable = detector.check(content);

    if (onProgress) {
      onProgress({
        stage: 'checking',
        elapsed,
        stableCount: detector.getStableCount(),
        contentLength: content.length
      });
    }

    if (isStable) {
      return {
        content,
        status: 'success',
        elapsed
      };
    }

    // Check idle timeout
    if (detector.isTimedOut()) {
      return {
        content,
        status: 'idle_timeout',
        message: 'Content stopped changing but stability not reached'
      };
    }

    await page.waitForTimeout(pollInterval);
  }
}

/**
 * Helper to get content from page
 */
async function getContent(page, selector) {
  try {
    const elements = await page.$$(selector);
    if (elements.length === 0) return '';

    // Get the last element (most recent response)
    const lastElement = elements[elements.length - 1];
    return await lastElement.textContent() || '';
  } catch (e) {
    return '';
  }
}

/**
 * Helper to check element visibility
 */
async function isElementVisible(page, selector) {
  try {
    const element = await page.$(selector);
    if (!element) return false;
    return await element.isVisible();
  } catch (e) {
    return false;
  }
}

module.exports = {
  StabilityDetector,
  waitForStableContent
};
