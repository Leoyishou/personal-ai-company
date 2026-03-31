---
name: browse-use
description: Headless browser automation with auth inheritance and session isolation. Default headless (no UI popup). Use for web scraping, form filling, screenshots, and any browser task that should run in background.
allowed-tools: Bash(browse-use:*), Write(/tmp/browse-*.js)
---

# browse-use - Background Browser Automation

Headless by default. Does NOT pop up a browser window or steal Mac focus.

## Quick Start

Write a script to `/tmp/browse-*.js`, then run it:

```bash
# Write script
cat > /tmp/browse-task.js << 'EOF'
await page.goto('https://example.com');
await page.screenshot({ path: '/tmp/example.png' });
console.log(await page.title());
EOF

# Run it
node ~/.claude/skills/browse-use/browse.js run /tmp/browse-task.js
```

## Script Format

Scripts receive pre-injected variables - just write Playwright code directly:

```javascript
// Available: browser, context, page, helpers
await page.goto('https://example.com');
const title = await page.title();
console.log(title);

// Use helpers from playwright-skill
await helpers.waitForPageReady(page);
await helpers.scrollPage(page, 'bottom');

// Screenshot
await page.screenshot({ path: '/tmp/result.png' });
```

## Commands

```bash
BROWSE=~/.claude/skills/browse-use/browse.js

# Run script file
node $BROWSE run /tmp/browse-task.js

# Run with auth (inherits Chrome login sessions via cookie snapshot)
node $BROWSE run /tmp/browse-task.js --debug

# Run with CDP direct (controls debug Chrome directly - full session auth)
node $BROWSE run /tmp/browse-task.js --cdp

# Run with visible browser
node $BROWSE run /tmp/browse-task.js --headed

# Run inline code
node $BROWSE run-inline 'await page.goto("https://example.com"); console.log(await page.title());'

# Named sessions (persist between runs)
node $BROWSE run /tmp/step1.js --session=myproject
node $BROWSE run /tmp/step2.js --session=myproject

# Session management
node $BROWSE sessions              # List active sessions
node $BROWSE close myproject       # Close specific session
node $BROWSE close --all           # Close all sessions

# Auth snapshot
node $BROWSE snapshot              # Refresh auth from debug Chrome
```

## Modes

### Normal Mode (default)
- Fresh headless Chromium
- No auth state
- Closes after script completes

### Debug Mode (`--debug`)
- Takes auth snapshot from debug Chrome (cookies + localStorage)
- Injects into fresh independent Chromium
- Does NOT connect to debug Chrome for automation
- Each run is fully isolated
- Requires: `chrome-debug` running with logged-in sessions

### Named Session (`--session=name`)
- Browser process persists between runs (skip launch overhead)
- Reconnect to same browser for multi-step workflows
- **Important**: Page URL/state resets between connections (Playwright server limitation). Each script step should re-navigate to its target URL.
- Cookies set during the session are shared across connections
- Must close manually when done

### CDP Direct Mode (`--cdp`)
- Connects directly to debug Chrome via Chrome DevTools Protocol
- Controls the actual debug Chrome process (not a copy)
- Full session auth — works for sites where cookie injection fails (e.g. Google CWS, Gmail)
- Script operates on existing tabs; `page` defaults to the first open tab
- Browser stays alive after script completes (only disconnects)
- Requires: `chrome-debug` running
- **Caution**: Script actions are visible in the debug Chrome window and affect real sessions

### Combined: `--debug --session=name`
- Persistent session with initial auth injection
- Best for multi-step authenticated workflows

## When to Use Which Mode

| Scenario | Mode |
|----------|------|
| Simple scraping, no login needed | Normal (default) |
| Site with standard cookie auth | `--debug` |
| Google services, complex auth | `--cdp` |
| Multi-step workflow, no auth | `--session=name` |
| Multi-step workflow, standard auth | `--debug --session=name` |

## Patterns

### Screenshot a page
```javascript
await page.goto('https://example.com');
await page.screenshot({ path: '/tmp/screenshot.png', fullPage: true });
```

### Extract page content
```javascript
await page.goto('https://example.com');
const text = await page.locator('article').textContent();
console.log(text);
```

### Fill and submit form
```javascript
await page.goto('https://example.com/form');
await page.fill('#name', 'John');
await page.fill('#email', 'john@example.com');
await page.click('button[type="submit"]');
await page.waitForURL('**/success');
```

### Scrape with auth (e.g. logged-in dashboard)
```javascript
// Run with: --debug
await page.goto('https://app.example.com/dashboard');
await page.waitForLoadState('networkidle');
const data = await page.locator('.metric').allTextContents();
console.log(JSON.stringify(data));
```

### CDP direct - automate logged-in Google service
```javascript
// Run with: --cdp
// Operates on the actual debug Chrome — full Google session available
const pages = context.pages();
// Find the tab you need, or navigate the current one
let target = pages.find(p => p.url().includes('webstore')) || page;
await target.goto('https://chrome.google.com/webstore/devconsole');
await target.waitForLoadState('networkidle');
await target.screenshot({ path: '/tmp/cws-dashboard.png' });
```

### Multi-step session
```bash
# Step 1: Navigate and login
node $BROWSE run /tmp/login.js --session=workflow --debug

# Step 2: Do something on the same browser (re-navigate to target URL)
node $BROWSE run /tmp/action.js --session=workflow

# Step 3: Cleanup
node $BROWSE close workflow
```

**Note**: Each step must navigate to its target URL - page state doesn't persist between connections. Cookies and browser-level state DO persist.

## Important Notes

- Scripts output goes to stdout/stderr - use `console.log()` for results
- Screenshots save to the path you specify (use `/tmp/` for temp files)
- Named sessions consume memory - always close when done
- Auth snapshots cache for 1 hour, then auto-refresh
- If debug Chrome is not running, falls back to expired snapshot with warning
