/**
 * ModelHop - Gemini Platform Adapter
 * Handles prompt extraction and injection for Gemini
 */

window.ModelHopPlatform = {
  name: 'gemini',
  
  // Selectors for Gemini (may need updates as UI changes)
  selectors: {
    input: '.ql-editor, [contenteditable="true"], textarea.text-input',
    sendButton: 'button.send-button, button[aria-label="Send message"]',
    userMessages: '.query-text, .user-query, [data-message-id] .query-content',
    richTextarea: '.rich-textarea'
  },
  
  /**
   * Get the input element
   */
  getInputElement() {
    // Try multiple selectors
    const selectors = [
      '.ql-editor',
      '[contenteditable="true"][role="textbox"]',
      'textarea',
      '.rich-textarea [contenteditable="true"]'
    ];
    
    for (const selector of selectors) {
      const el = document.querySelector(selector);
      if (el && el.offsetParent !== null) {
        return el;
      }
    }
    
    return document.querySelector(this.selectors.input);
  },
  
  /**
   * Get the last prompt sent by the user
   */
  getLastPrompt() {
    // Gemini has various UI versions, try multiple approaches
    const selectors = [
      '.query-text',
      '.user-query',
      '[data-message-author="user"]',
      '.conversation-turn.user .message-content'
    ];
    
    for (const selector of selectors) {
      const messages = document.querySelectorAll(selector);
      if (messages.length > 0) {
        const lastMessage = messages[messages.length - 1];
        const text = lastMessage.textContent.trim();
        if (text) return text;
      }
    }
    
    // Fallback: get from input
    const input = this.getInputElement();
    if (input) {
      return input.value || input.textContent || input.innerText || '';
    }
    
    return '';
  },
  
  /**
   * Check if an element is the send button
   */
  isSendButton(element) {
    // Check if element or parent is a send button
    const selectors = [
      '.send-button',
      'button[aria-label="Send message"]',
      'button[aria-label="Submit"]'
    ];
    
    for (const selector of selectors) {
      const btn = document.querySelector(selector);
      if (btn && (btn === element || btn.contains(element))) {
        return true;
      }
    }
    return false;
  },
  
  /**
   * Fill the input with a prompt (for incoming hops)
   */
  /**
   * Get the last AI response
   */
  getLastResponse() {
    const selectors = ['.model-response-text', '.response-content', '[data-message-author="model"]'];
    for (const sel of selectors) {
      const msgs = document.querySelectorAll(sel);
      if (msgs.length > 0) return msgs[msgs.length - 1].textContent.trim();
    }
    return '';
  },

  fillInput(element, text) {
    if (!element) {
      element = this.getInputElement();
    }
    if (!element) return false;
    
    element.focus();
    
    // Handle different input types
    if (element.tagName === 'TEXTAREA') {
      const nativeSetter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype,
        'value'
      )?.set;
      
      if (nativeSetter) {
        nativeSetter.call(element, text);
      } else {
        element.value = text;
      }
    } else if (element.classList.contains('ql-editor')) {
      // Quill editor
      element.innerHTML = `<p>${text}</p>`;
    } else {
      // ContentEditable
      element.innerText = text;
    }
    
    // Dispatch events
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
    element.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
    
    return true;
  }
};
