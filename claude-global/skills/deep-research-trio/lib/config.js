/**
 * Platform configurations for Deep Research Trio
 */

const PLATFORMS = {
  gemini: {
    name: 'Gemini',
    url: 'https://gemini.google.com/app',
    deepResearchUrl: 'https://gemini.google.com/app',
    selectors: {
      // Input area
      input: 'rich-textarea, [contenteditable="true"], textarea',
      submitButton: 'button[aria-label*="Send"], button[data-test-id="send-button"]',

      // Deep Research trigger
      deepResearchButton: '[data-test-id="deep-research"], button:has-text("Deep research")',
      deepResearchToggle: 'button[aria-label*="Deep research"]',

      // Status indicators
      thinkingIndicator: '.thinking-indicator, [data-research-status="running"], .loading-spinner',
      responseContainer: '.response-container, .model-response, [data-message-author="model"]',

      // Login check
      loginIndicator: 'img[src*="googleusercontent"], bard-sidenav-content'
    },
    timeouts: {
      navigation: 30000,
      inputReady: 10000,
      researchStart: 60000,    // Time to wait for research to start
      researchComplete: 3600000, // Max 60 minutes
      pollInterval: 5000       // Check every 5 seconds
    }
  },

  chatgpt: {
    name: 'ChatGPT',
    url: 'https://chatgpt.com',
    deepResearchUrl: 'https://chatgpt.com/?model=gpt-4o-research',
    selectors: {
      // Input area
      input: '#prompt-textarea, textarea[data-id="root"]',
      submitButton: 'button[data-testid="send-button"], button[aria-label="Send prompt"]',

      // Deep Research trigger (model selector)
      modelSelector: 'button[data-testid="model-selector"]',
      researchOption: '[data-testid="model-option-research"]',

      // Status indicators
      thinkingIndicator: '.streaming-indicator, .result-streaming, [data-message-author-role="assistant"].streaming',
      responseContainer: '[data-message-author-role="assistant"]',

      // Login check
      loginIndicator: 'nav, .text-token-text-secondary'
    },
    timeouts: {
      navigation: 30000,
      inputReady: 10000,
      researchStart: 60000,
      researchComplete: 1800000, // Max 30 minutes
      pollInterval: 5000
    }
  },

  claude: {
    name: 'Claude',
    url: 'https://claude.ai',
    deepResearchUrl: 'https://claude.ai/new',
    selectors: {
      // Input area
      input: '[contenteditable="true"].ProseMirror, div[data-placeholder]',
      submitButton: 'button[aria-label="Send Message"], button:has(svg[data-icon="arrow-up"])',

      // Research mode trigger
      researchToggle: 'button[aria-label*="Research"], button:has-text("Research")',
      extendedThinkingToggle: 'button[aria-label*="Extended thinking"]',

      // Status indicators
      thinkingIndicator: '.thinking-indicator, [data-is-streaming="true"]',
      responseContainer: '[data-is-streaming="false"] .prose, .message-content',

      // Login check
      loginIndicator: '.ProseMirror, fieldset'
    },
    timeouts: {
      navigation: 30000,
      inputReady: 10000,
      researchStart: 30000,
      researchComplete: 900000, // Max 15 minutes
      pollInterval: 3000
    }
  }
};

const CDP_URL = process.env.CHROME_CDP_URL || 'http://127.0.0.1:9222';

const STABILITY_CONFIG = {
  requiredStableCount: 3,  // 3 consecutive same results = complete
  pollInterval: 3000,      // Default poll interval
  maxIdleTime: 120000      // Max time without changes before timeout
};

const REPORT_CONFIG = {
  outputDir: require('path').join(__dirname, '..', 'reports'),
  timestampFormat: 'YYYY-MM-DD_HH-mm-ss'
};

module.exports = {
  PLATFORMS,
  CDP_URL,
  STABILITY_CONFIG,
  REPORT_CONFIG
};
