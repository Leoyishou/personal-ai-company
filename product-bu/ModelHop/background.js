/**
 * ModelHop Background Service Worker
 * Handles message passing between tabs and storage
 */

const PLATFORM_URLS = {
  claude: 'https://claude.ai/new',
  gemini: 'https://gemini.google.com/app',
  chatgpt: 'https://chatgpt.com/'
};

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'hop') {
    const { target, prompt } = message;
    
    // Store the prompt KEYED BY TARGET to prevent hijacking by other tabs
    const storageKey = `pendingPrompt_${target}`;
    const storageData = {
      [storageKey]: prompt,
      [`${storageKey}_timestamp`]: Date.now(),
      [`${storageKey}_sourceTab`]: sender.tab?.id
    };
    
    chrome.storage.local.set(storageData, () => {
      // Open the target platform
      const url = PLATFORM_URLS[target];
      if (url) {
        chrome.tabs.create({ url }, (tab) => {
          // Store the target tab ID so we know which tab should receive the prompt
          chrome.storage.local.set({
            [`${storageKey}_targetTab`]: tab.id
          }, () => {
            sendResponse({ success: true, tabId: tab.id });
          });
        });
      } else {
        sendResponse({ success: false, error: 'Unknown platform' });
      }
    });
    
    return true; // Keep channel open for async response
  }
  
  if (message.action === 'getPendingPrompt') {
    const platform = message.platform;
    
    if (!platform) {
      sendResponse({ prompt: null });
      return true;
    }
    
    const storageKey = `pendingPrompt_${platform}`;
    
    chrome.storage.local.get([
      storageKey,
      `${storageKey}_timestamp`,
      `${storageKey}_targetTab`
    ], (result) => {
      const prompt = result[storageKey];
      const timestamp = result[`${storageKey}_timestamp`];
      const targetTabId = result[`${storageKey}_targetTab`];
      
      // Only return prompt if:
      // 1. It exists
      // 2. It's less than 60 seconds old
      // 3. This tab is the intended target (or targetTab wasn't set - backwards compat)
      const isRecent = timestamp && (Date.now() - timestamp < 60000);
      const isCorrectTab = !targetTabId || targetTabId === sender.tab?.id;
      
      if (prompt && isRecent && isCorrectTab) {
        sendResponse({ prompt: prompt });
        // Clear the stored prompt for this platform
        chrome.storage.local.remove([
          storageKey,
          `${storageKey}_timestamp`,
          `${storageKey}_sourceTab`,
          `${storageKey}_targetTab`
        ]);
      } else {
        sendResponse({ prompt: null });
      }
    });
    
    return true;
  }
  
  if (message.action === 'generateWhiteboard') {
    const { text } = message;

    const prompt = `手绘白板风格示意图，纯白背景，粗黑马克笔笔触，Excalidraw 手绘美感。

请根据以下内容，生成一张视觉摘要图：

---
${text}
---

要求：
- 所有文字标注必须使用中文
- 提取核心概念和逻辑关系，用关键词呈现
- 使用简笔画图标、箭头、流程连接线来表达关系
- 标题加粗加大，关键术语用蓝色高亮
- 配色极简：黑色为主 + 蓝色强调 + 少量红/绿点缀
- 禁止出现大段文字，只用关键词、图标、箭头
- 布局清晰，层次分明，适合一眼看懂
- 风格：像老师在白板上快速画的思维导图/流程图`;

    const OPENROUTER_API_KEY = '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';

    fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
        'HTTP-Referer': 'chrome-extension://modelhop',
        'X-Title': 'ModelHop'
      },
      body: JSON.stringify({
        model: 'google/gemini-3-pro-image-preview',
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ]
      })
    })
    .then(res => res.json())
    .then(data => {
      const choice = data.choices?.[0];
      if (!choice) {
        sendResponse({ success: false, error: data.error?.message || 'No response from API' });
        return;
      }

      // OpenRouter returns images in message.images array
      const images = choice.message?.images;
      if (images && images.length > 0) {
        const imageUrl = images[0].image_url?.url;
        if (imageUrl) {
          // imageUrl is a full data URI like "data:image/jpeg;base64,..."
          sendResponse({ success: true, imageUrl: imageUrl });
          return;
        }
      }

      sendResponse({ success: false, error: 'No image in response' });
    })
    .catch(err => {
      console.error('[ModelHop] API error:', err);
      sendResponse({ success: false, error: err.message });
    });

    return true; // Keep channel open for async response
  }

  // Clean up old prompts periodically
  if (message.action === 'cleanup') {
    chrome.storage.local.get(null, (items) => {
      const now = Date.now();
      const keysToRemove = [];
      
      for (const key in items) {
        if (key.includes('_timestamp')) {
          if (now - items[key] > 120000) { // 2 minutes
            const baseKey = key.replace('_timestamp', '');
            keysToRemove.push(
              baseKey,
              `${baseKey}_timestamp`,
              `${baseKey}_sourceTab`,
              `${baseKey}_targetTab`
            );
          }
        }
      }
      
      if (keysToRemove.length > 0) {
        chrome.storage.local.remove(keysToRemove);
      }
    });
  }
});

// Run cleanup every 2 minutes
setInterval(() => {
  chrome.runtime.sendMessage({ action: 'cleanup' }).catch(() => {});
}, 120000);
