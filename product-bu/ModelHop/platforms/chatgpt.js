/**
 * ModelHop - ChatGPT Platform Adapter
 * Handles prompt extraction and injection for ChatGPT
 */

window.ModelHopPlatform = {
  name: 'chatgpt',
  
  // Selectors for ChatGPT (may need updates as UI changes)
  selectors: {
    input: '#prompt-textarea, textarea[data-id="root"]',
    sendButton: '[data-testid="send-button"], button[aria-label="Send prompt"]',
    userMessages: '[data-message-author-role="user"]',
    messageContent: '.markdown, .whitespace-pre-wrap'
  },
  
  /**
   * Get the input element
   */
  getInputElement() {
    return document.querySelector(this.selectors.input);
  },
  
  /**
   * Get the last prompt sent by the user
   */
  getLastPrompt() {
    // Try to get from the conversation
    const userMessages = document.querySelectorAll(this.selectors.userMessages);
    if (userMessages.length > 0) {
      const lastMessage = userMessages[userMessages.length - 1];
      const content = lastMessage.querySelector(this.selectors.messageContent);
      if (content) {
        return content.textContent.trim();
      }
    }
    
    // Fallback: get from input field
    const input = this.getInputElement();
    if (input) {
      return input.value || input.textContent || '';
    }
    
    return '';
  },
  
  /**
   * Check if an element is the send button
   */
  isSendButton(element) {
    const sendBtn = document.querySelector(this.selectors.sendButton);
    return sendBtn && (sendBtn === element || sendBtn.contains(element));
  },
  
  /**
   * Fill the input with a prompt (for incoming hops)
   */
  /**
   * Get the last AI response
   */
  getLastResponse() {
    const assistantMessages = document.querySelectorAll('[data-message-author-role="assistant"]');
    if (assistantMessages.length > 0) {
      const last = assistantMessages[assistantMessages.length - 1];
      const content = last.querySelector('.markdown');
      return content ? content.textContent.trim() : '';
    }
    return '';
  },

  fillInput(element, text) {
    if (!element) {
      element = this.getInputElement();
    }
    if (!element) return false;
    
    // Focus the element
    element.focus();
    
    // ChatGPT uses a textarea
    if (element.tagName === 'TEXTAREA') {
      // Use native setter to trigger React's event handlers
      const nativeSetter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, 
        'value'
      )?.set;
      
      if (nativeSetter) {
        nativeSetter.call(element, text);
      } else {
        element.value = text;
      }
    } else {
      // ContentEditable div
      element.textContent = text;
    }
    
    // Dispatch events to notify React
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
    
    // Also try dispatching a keyboard event
    element.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true }));
    element.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
    
    return true;
  }
};
