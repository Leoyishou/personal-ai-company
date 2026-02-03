# ModelHop Chrome Extension

Forward prompts between AI models in 1 click.

## Installation (Developer Mode)

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select this `extension` folder

## How It Works

1. **Ask a question** in ChatGPT, Claude, or Gemini
2. **Click "Ask Claude"** or "Ask Gemini" button that appears
3. **Continue** your conversation in the new tab with your prompt pre-filled

## Features

- **No Copy-Pasting**: Automatically extracts and fills prompts
- **Context Aware**: Carries over your latest query
- **Whiteboard Mode**: Generate hand-drawn style diagrams from AI responses (via OpenRouter / Gemini 3 Pro Image)
- **Fallback**: Copies to clipboard if auto-fill fails

## Supported Platforms

- ChatGPT (chatgpt.com, chat.openai.com)
- Claude (claude.ai)
- Gemini (gemini.google.com)

## Maintenance Note

AI platforms frequently update their UI, which may break selectors. 
If buttons don't appear or prompts aren't detected:

1. Check the browser console for errors
2. Update selectors in `platforms/*.js` files
3. Reload the extension

## Files Structure

```
extension/
├── manifest.json       # Extension manifest (MV3)
├── background.js       # Service worker for tab management
├── content.js          # Main content script
├── styles.css          # Button and toast styles
├── platforms/
│   ├── chatgpt.js     # ChatGPT adapter
│   ├── claude.js      # Claude adapter
│   └── gemini.js      # Gemini adapter
└── icons/             # Extension icons
```

## Privacy

ModelHop:
- Does NOT store conversation history
- Does NOT track user behavior
- Whiteboard feature sends AI response text (up to 2000 chars) to OpenRouter API for image generation
- All other processing happens locally in your browser
