/**
 * ModelHop - Claude Platform Adapter
 * Handles prompt extraction and injection for Claude.ai
 */

window.ModelHopPlatform = {
  name: 'claude',
  
  // Selectors for Claude (may need updates as UI changes)
  selectors: {
    input: '[contenteditable="true"].ProseMirror, div[contenteditable="true"]',
    sendButton: 'button[aria-label="Send Message"], button[type="submit"]',
    userMessages: '[data-testid="user-message"], .font-user-message',
    conversationTurn: '.font-claude-message'
  },
  
  /**
   * Get the input element
   */
  getInputElement() {
    // Claude uses a contenteditable div with ProseMirror
    const inputs = document.querySelectorAll(this.selectors.input);
    for (const input of inputs) {
      if (input.offsetParent !== null) { // visible
        return input;
      }
    }
    return inputs[0] || null;
  },
  
  /**
   * Get the last prompt sent by the user
   */
  getLastPrompt() {
    // Try to get from conversation
    const userMessages = document.querySelectorAll(this.selectors.userMessages);
    if (userMessages.length > 0) {
      const lastMessage = userMessages[userMessages.length - 1];
      return lastMessage.textContent.trim();
    }
    
    // Alternative: look for human turns in the conversation
    const allTurns = document.querySelectorAll('[data-testid]');
    const humanTurns = Array.from(allTurns).filter(el => 
      el.getAttribute('data-testid')?.includes('human') ||
      el.getAttribute('data-testid')?.includes('user')
    );
    
    if (humanTurns.length > 0) {
      return humanTurns[humanTurns.length - 1].textContent.trim();
    }
    
    // Fallback: get from input
    const input = this.getInputElement();
    if (input) {
      return input.textContent || input.innerText || '';
    }
    
    return '';
  },
  
  /**
   * Check if an element is the send button
   */
  isSendButton(element) {
    const buttons = document.querySelectorAll(this.selectors.sendButton);
    for (const btn of buttons) {
      if (btn === element || btn.contains(element)) {
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
    const claudeMessages = document.querySelectorAll('.font-claude-message, [data-testid="assistant-message"]');
    if (claudeMessages.length > 0) {
      return claudeMessages[claudeMessages.length - 1].textContent.trim();
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
    
    // Claude uses contenteditable with ProseMirror
    // We need to properly set the content
    
    // Clear existing content
    element.innerHTML = '';
    
    // Create a paragraph element (ProseMirror structure)
    const p = document.createElement('p');
    p.textContent = text;
    element.appendChild(p);
    
    // Also set innerText as fallback
    if (element.childNodes.length === 0) {
      element.innerText = text;
    }
    
    // Dispatch input event
    element.dispatchEvent(new InputEvent('input', {
      bubbles: true,
      cancelable: true,
      inputType: 'insertText',
      data: text
    }));
    
    // Move cursor to end
    const range = document.createRange();
    const sel = window.getSelection();
    range.selectNodeContents(element);
    range.collapse(false);
    sel.removeAllRanges();
    sel.addRange(range);
    
    return true;
  }
};
