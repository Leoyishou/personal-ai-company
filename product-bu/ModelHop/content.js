/**
 * ModelHop Content Script - Main Controller
 * This file is loaded after platform-specific scripts
 */

(function() {
  'use strict';
  
  // Platform adapter should be defined by platform-specific script
  if (typeof window.ModelHopPlatform === 'undefined') {
    console.warn('[ModelHop] No platform adapter found');
    return;
  }
  
  const platform = window.ModelHopPlatform;
  let buttonsContainer = null;
  let lastDetectedPrompt = '';
  
  // ============================================
  // UI: Create hop buttons
  // ============================================
  function createHopButtons() {
    if (document.getElementById('modelhop-container')) return;
    
    buttonsContainer = document.createElement('div');
    buttonsContainer.id = 'modelhop-container';
    buttonsContainer.className = 'modelhop-container modelhop-hidden';
    
    const targets = getTargetPlatforms();
    
    targets.forEach(target => {
      const btn = document.createElement('button');
      btn.className = 'modelhop-btn';
      btn.dataset.target = target.key;
      btn.innerHTML = `
        <span class="modelhop-icon">${target.icon}</span>
        <span class="modelhop-label">Ask ${target.name}</span>
      `;
      btn.addEventListener('click', () => handleHop(target.key));
      buttonsContainer.appendChild(btn);
    });

    // Add Whiteboard button
    const wbBtn = document.createElement('button');
    wbBtn.className = 'modelhop-btn modelhop-whiteboard-btn';
    wbBtn.innerHTML = `
      <span class="modelhop-icon">🎨</span>
      <span class="modelhop-label">Whiteboard</span>
    `;
    wbBtn.addEventListener('click', handleWhiteboard);
    buttonsContainer.appendChild(wbBtn);
    
    document.body.appendChild(buttonsContainer);
  }
  
  function getTargetPlatforms() {
    const all = [
      { key: 'claude', name: 'Claude', icon: '🟣' },
      { key: 'gemini', name: 'Gemini', icon: '🔵' },
      { key: 'chatgpt', name: 'ChatGPT', icon: '🟢' }
    ];
    // Exclude current platform
    return all.filter(p => p.key !== platform.name);
  }
  
  function showButtons() {
    if (buttonsContainer) {
      buttonsContainer.classList.remove('modelhop-hidden');
    }
  }
  
  function hideButtons() {
    if (buttonsContainer) {
      buttonsContainer.classList.add('modelhop-hidden');
    }
  }
  
  // ============================================
  // Core: Handle hop action
  // ============================================
  async function handleHop(targetPlatform) {
    const prompt = lastDetectedPrompt || platform.getLastPrompt();
    
    if (!prompt || prompt.trim() === '') {
      showToast('No prompt detected. Type something first!', 'error');
      return;
    }
    
    try {
      // Send to background script to open new tab
      chrome.runtime.sendMessage({
        action: 'hop',
        target: targetPlatform,
        prompt: prompt.trim()
      }, (response) => {
        if (response && response.success) {
          showToast(`Opening ${targetPlatform}...`, 'success');
        } else {
          // Fallback: copy to clipboard
          fallbackCopy(prompt, targetPlatform);
        }
      });
    } catch (error) {
      console.error('[ModelHop] Error:', error);
      fallbackCopy(prompt, targetPlatform);
    }
  }
  
  function fallbackCopy(prompt, targetPlatform) {
    navigator.clipboard.writeText(prompt).then(() => {
      showToast('Copied to clipboard! Paste in the new tab.', 'info');
      const urls = {
        claude: 'https://claude.ai/new',
        gemini: 'https://gemini.google.com/app',
        chatgpt: 'https://chatgpt.com/'
      };
      window.open(urls[targetPlatform], '_blank');
    }).catch(() => {
      showToast('Could not copy. Please copy manually.', 'error');
    });
  }
  
  // ============================================
  // Toast notifications
  // ============================================
  function showToast(message, type = 'info') {
    const existing = document.querySelector('.modelhop-toast');
    if (existing) existing.remove();
    
    const toast = document.createElement('div');
    toast.className = `modelhop-toast modelhop-toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.classList.add('modelhop-toast-fade');
      setTimeout(() => toast.remove(), 300);
    }, 2500);
  }
  
  // ============================================
  // Whiteboard: Generate visual diagram from AI response
  // ============================================
  async function handleWhiteboard() {
    const responseText = platform.getLastResponse();
    if (!responseText) {
      showWhiteboardPanel('error', 'No AI response detected yet. Send a message first.');
      return;
    }

    const truncated = responseText.substring(0, 2000);
    showWhiteboardPanel('loading');

    try {
      chrome.runtime.sendMessage({
        action: 'generateWhiteboard',
        text: truncated
      }, (response) => {
        if (chrome.runtime.lastError) {
          showWhiteboardPanel('error', 'Failed to connect to extension.');
          return;
        }
        if (response && response.success && response.imageUrl) {
          showWhiteboardPanel('success', response.imageUrl);
        } else {
          showWhiteboardPanel('error', response?.error || 'Failed to generate whiteboard.');
        }
      });
    } catch (error) {
      console.error('[ModelHop] Whiteboard error:', error);
      showWhiteboardPanel('error', 'Error generating whiteboard.');
    }
  }

  function showWhiteboardPanel(state, data) {
    let panel = document.querySelector('.modelhop-panel');

    if (!panel) {
      panel = document.createElement('div');
      panel.className = 'modelhop-panel';
      panel.innerHTML = `
        <div class="modelhop-panel-header">
          <div class="modelhop-panel-title">
            <span class="modelhop-panel-icon">🎨</span>
            <span>Whiteboard</span>
          </div>
          <div class="modelhop-panel-actions">
            <button class="modelhop-panel-refresh" title="Regenerate">↻</button>
            <button class="modelhop-panel-close" title="Close">✕</button>
          </div>
        </div>
        <div class="modelhop-panel-body"></div>
      `;
      panel.querySelector('.modelhop-panel-close').addEventListener('click', () => {
        panel.classList.add('modelhop-panel-closing');
        setTimeout(() => panel.remove(), 250);
      });
      panel.querySelector('.modelhop-panel-refresh').addEventListener('click', () => {
        handleWhiteboard();
      });
      document.body.appendChild(panel);
      // Trigger slide-in
      requestAnimationFrame(() => panel.classList.add('modelhop-panel-open'));
    }

    const body = panel.querySelector('.modelhop-panel-body');

    if (state === 'loading') {
      body.innerHTML = `
        <div class="modelhop-panel-loading">
          <div class="modelhop-loading-spinner"></div>
          <div class="modelhop-loading-text">Generating...</div>
        </div>
      `;
    } else if (state === 'success') {
      body.innerHTML = `
        <div class="modelhop-panel-result">
          <img src="${data}" alt="Whiteboard diagram" />
          <div class="modelhop-panel-toolbar">
            <button class="modelhop-panel-copy" title="Copy image">📋 Copy</button>
            <button class="modelhop-panel-download" title="Download">⬇ Save</button>
          </div>
        </div>
      `;
      body.querySelector('.modelhop-panel-copy').addEventListener('click', async (e) => {
        try {
          const img = body.querySelector('img');
          const canvas = document.createElement('canvas');
          canvas.width = img.naturalWidth;
          canvas.height = img.naturalHeight;
          canvas.getContext('2d').drawImage(img, 0, 0);
          const blob = await new Promise(r => canvas.toBlob(r, 'image/png'));
          await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]);
          e.target.textContent = '✓ Copied!';
          setTimeout(() => { e.target.textContent = '📋 Copy'; }, 1500);
        } catch (err) {
          e.target.textContent = '✗ Failed';
          setTimeout(() => { e.target.textContent = '📋 Copy'; }, 1500);
        }
      });
      body.querySelector('.modelhop-panel-download').addEventListener('click', () => {
        const a = document.createElement('a');
        a.href = data;
        const ext = data.includes('image/png') ? 'png' : 'jpg';
        a.download = `whiteboard-${Date.now()}.${ext}`;
        a.click();
      });
    } else if (state === 'error') {
      body.innerHTML = `
        <div class="modelhop-panel-error">
          <div class="modelhop-error-icon">⚠</div>
          <div class="modelhop-error-text">${data}</div>
          <button class="modelhop-error-retry">Retry</button>
        </div>
      `;
      body.querySelector('.modelhop-error-retry').addEventListener('click', () => {
        handleWhiteboard();
      });
    }
  }

  // ============================================
  // Detection: Watch for user sending messages
  // ============================================
  function setupDetection() {
    // Observe DOM for new messages
    const observer = new MutationObserver((mutations) => {
      const prompt = platform.getLastPrompt();
      if (prompt && prompt !== lastDetectedPrompt) {
        lastDetectedPrompt = prompt;
        showButtons();
      }
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
    
    // Also listen for form submissions
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        setTimeout(() => {
          const prompt = platform.getLastPrompt();
          if (prompt) {
            lastDetectedPrompt = prompt;
            showButtons();
          }
        }, 500);
      }
    });
    
    // Check on click (for send button clicks)
    document.addEventListener('click', (e) => {
      if (platform.isSendButton && platform.isSendButton(e.target)) {
        setTimeout(() => {
          const prompt = platform.getLastPrompt();
          if (prompt) {
            lastDetectedPrompt = prompt;
            showButtons();
          }
        }, 500);
      }
    });
  }
  
  // ============================================
  // Injection: Fill prompt when arriving from hop
  // ============================================
  async function checkForIncomingPrompt() {
    try {
      chrome.runtime.sendMessage({ 
        action: 'getPendingPrompt',
        platform: platform.name 
      }, (response) => {
        if (response && response.prompt) {
          // Wait for page to be ready
          waitForInput().then((inputEl) => {
            if (inputEl) {
              platform.fillInput(inputEl, response.prompt);
              showToast('Prompt filled! Review and send.', 'success');
            } else {
              // Fallback: show prompt in alert
              fallbackShowPrompt(response.prompt);
            }
          });
        }
      });
    } catch (e) {
      console.log('[ModelHop] No pending prompt');
    }
  }
  
  function waitForInput(maxAttempts = 20) {
    return new Promise((resolve) => {
      let attempts = 0;
      const check = () => {
        const input = platform.getInputElement();
        if (input) {
          resolve(input);
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(check, 300);
        } else {
          resolve(null);
        }
      };
      check();
    });
  }
  
  function fallbackShowPrompt(prompt) {
    navigator.clipboard.writeText(prompt).then(() => {
      showToast('Prompt copied to clipboard. Paste with Ctrl+V / Cmd+V', 'info');
    });
  }
  
  // ============================================
  // Initialize
  // ============================================
  function init() {
    console.log(`[ModelHop] Initialized on ${platform.name}`);
    createHopButtons();
    setupDetection();
    
    // Check if we arrived here via a hop
    setTimeout(checkForIncomingPrompt, 1000);
  }
  
  // Wait for DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
