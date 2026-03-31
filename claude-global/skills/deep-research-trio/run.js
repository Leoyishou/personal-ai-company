#!/usr/bin/env node
/**
 * Deep Research Trio - Universal Executor
 *
 * Usage:
 *   node run.js status                              # Check login status
 *   node run.js research "query"                    # Full research (all platforms)
 *   node run.js research "query" --platforms gemini # Single platform
 *   node run.js research "query" -p gemini,chatgpt  # Multiple platforms
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Change to skill directory for proper module resolution
process.chdir(__dirname);

/**
 * Check if Playwright is installed
 */
function checkPlaywrightInstalled() {
  try {
    require.resolve('playwright');
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Install dependencies if missing
 */
function installDependencies() {
  console.log('📦 Installing dependencies...');
  try {
    execSync('npm install', { stdio: 'inherit', cwd: __dirname });
    execSync('npx playwright install chromium', { stdio: 'inherit', cwd: __dirname });
    console.log('✅ Dependencies installed\n');
    return true;
  } catch (e) {
    console.error('❌ Failed to install dependencies:', e.message);
    return false;
  }
}

/**
 * Parse command line arguments
 */
function parseArgs() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    return { command: 'help' };
  }

  const command = args[0];

  if (command === 'status') {
    return { command: 'status' };
  }

  if (command === 'research') {
    const query = args[1];
    if (!query) {
      console.error('❌ Query is required for research command');
      return { command: 'help' };
    }

    // Parse platforms
    let platforms = ['gemini', 'chatgpt', 'claude'];
    const platformIndex = args.findIndex(a => a === '--platforms' || a === '-p');
    if (platformIndex !== -1 && args[platformIndex + 1]) {
      platforms = args[platformIndex + 1].split(',').map(p => p.trim().toLowerCase());
    }

    return { command: 'research', query, platforms };
  }

  return { command: 'help' };
}

/**
 * Print help message
 */
function printHelp() {
  console.log(`
🔬 Deep Research Trio

Parallel deep research across Gemini, ChatGPT, and Claude.

Usage:
  node run.js status                              Check login status for all platforms
  node run.js research "your query"               Run deep research on all platforms
  node run.js research "query" -p gemini          Single platform
  node run.js research "query" -p gemini,chatgpt  Multiple platforms

Prerequisites:
  1. Run 'chrome-debug' to start Chrome in debug mode
  2. Login to Gemini, ChatGPT, and Claude in that browser

Examples:
  node run.js status
  node run.js research "What are the latest developments in AI agents?"
  node run.js research "React vs Vue in 2025" -p gemini,chatgpt
`);
}

/**
 * Check login status
 */
async function checkStatus() {
  const { ParallelExecutor } = require('./lib/parallel-executor');

  const executor = new ParallelExecutor({
    platforms: ['gemini', 'chatgpt', 'claude']
  });

  try {
    await executor.initialize();
    console.log('\n📊 Login Status Check\n');
    await executor.checkLoginStatus();
  } finally {
    await executor.cleanup();
  }
}

/**
 * Run deep research
 */
async function runResearch(query, platforms) {
  const { ParallelExecutor } = require('./lib/parallel-executor');
  const { GeminiPlatform } = require('./platforms/gemini');
  const { ChatGPTPlatform } = require('./platforms/chatgpt');
  const { ClaudePlatform } = require('./platforms/claude');
  const { REPORT_CONFIG } = require('./lib/config');

  const platformClasses = {
    gemini: GeminiPlatform,
    chatgpt: ChatGPTPlatform,
    claude: ClaudePlatform
  };

  const executor = new ParallelExecutor({
    query,
    platforms,
    onProgress: (progress) => {
      // Progress is logged by platform handlers
    }
  });

  try {
    await executor.initialize();

    // Execute on all platforms in parallel
    const results = await executor.executeAll(platformClasses);

    // Print summary
    console.log('\n' + '═'.repeat(50));
    console.log('📊 Research Summary');
    console.log('═'.repeat(50));

    const summary = executor.getSummary();
    console.log(`Total: ${summary.total} platforms`);
    console.log(`Success: ${summary.success}`);
    console.log(`Partial: ${summary.partial}`);
    console.log(`Failed: ${summary.failed}\n`);

    for (const [key, info] of Object.entries(summary.platforms)) {
      const statusEmoji = info.status === 'success' ? '✅' :
                         info.status === 'timeout' ? '⚠️' : '❌';
      console.log(`${statusEmoji} ${info.name}: ${info.status}${info.duration ? ` (${info.duration} min)` : ''}`);
    }

    // Save results to file
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const outputFile = path.join(REPORT_CONFIG.outputDir, `research-${timestamp}.json`);

    fs.writeFileSync(outputFile, JSON.stringify({
      query,
      timestamp: new Date().toISOString(),
      summary,
      results
    }, null, 2));

    console.log(`\n📁 Results saved to: ${outputFile}`);

    // Generate markdown report
    await generateMarkdownReport(query, results, REPORT_CONFIG.outputDir, timestamp);

    return results;

  } finally {
    await executor.cleanup();
  }
}

/**
 * Generate markdown report
 */
async function generateMarkdownReport(query, results, outputDir, timestamp) {
  const reportFile = path.join(outputDir, `research-${timestamp}.md`);

  let md = `# Deep Research Trio Report

**Query**: ${query}
**Time**: ${new Date().toLocaleString()}

---

## Summary

| Platform | Status | Duration |
|----------|--------|----------|
`;

  for (const result of results) {
    const status = result.status === 'success' ? '✅ Success' :
                  result.status === 'timeout' ? '⚠️ Timeout' :
                  result.status === 'partial' ? '⚠️ Partial' : '❌ Failed';
    const duration = result.timing?.durationMinutes ?
                    `${result.timing.durationMinutes} min` : '-';
    md += `| ${result.name || result.platform} | ${status} | ${duration} |\n`;
  }

  md += '\n---\n\n## Detailed Results\n\n';

  for (const result of results) {
    md += `### ${result.name || result.platform}\n\n`;

    if (result.error) {
      md += `**Error**: ${result.error}\n\n`;
    } else if (result.content) {
      md += `**Summary** (first 500 chars):\n\n${result.content.summary}\n\n`;

      if (result.content.citations?.length > 0) {
        md += `**Citations** (${result.content.citations.length}):\n\n`;
        for (const cite of result.content.citations.slice(0, 10)) {
          md += `- [${cite.title || cite.url}](${cite.url})\n`;
        }
        md += '\n';
      }

      md += `<details>\n<summary>Full Response (${result.content.fullText?.length || 0} chars)</summary>\n\n`;
      md += '```\n' + (result.content.fullText || '(empty)') + '\n```\n\n';
      md += '</details>\n\n';
    }

    md += '---\n\n';
  }

  fs.writeFileSync(reportFile, md);
  console.log(`📄 Markdown report: ${reportFile}`);
}

/**
 * Send notification when complete
 */
async function sendNotification(query, summary) {
  try {
    // Try to use api-notify skill
    const notifyScript = path.join(__dirname, '..', 'api-notify', 'notify.js');
    if (fs.existsSync(notifyScript)) {
      const message = `🔬 Deep Research Complete\n\nQuery: ${query}\n\n` +
                     `✅ ${summary.success} success\n` +
                     `⚠️ ${summary.partial} partial\n` +
                     `❌ ${summary.failed} failed`;

      execSync(`node "${notifyScript}" --title "Deep Research" --message "${message}"`, {
        stdio: 'ignore'
      });
    }
  } catch (e) {
    // Notification is optional
  }
}

/**
 * Main entry point
 */
async function main() {
  console.log('🔬 Deep Research Trio\n');

  // Check dependencies
  if (!checkPlaywrightInstalled()) {
    if (!installDependencies()) {
      process.exit(1);
    }
  }

  const { command, query, platforms } = parseArgs();

  try {
    switch (command) {
      case 'status':
        await checkStatus();
        break;

      case 'research':
        const results = await runResearch(query, platforms);
        break;

      case 'help':
      default:
        printHelp();
    }
  } catch (error) {
    console.error('\n❌ Error:', error.message);
    if (error.stack && process.env.DEBUG) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

// Run
main().catch(e => {
  console.error('Fatal error:', e);
  process.exit(1);
});
