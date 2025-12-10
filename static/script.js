// Global state
let conversationHistory = [];
let isLoading = false;
let retryCount = 0;
const MAX_RETRIES = 3;

// DOM elements
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const messages = document.getElementById('messages');
const welcomeScreen = document.getElementById('welcomeScreen');
const newChatBtn = document.getElementById('newChatBtn');
const modelSelect = document.getElementById('modelSelect');
const chatContainer = document.getElementById('chatContainer');

// Configuration
const API_TIMEOUT = 60000; // 60 seconds
const RETRY_DELAY = 2000; // 2 seconds

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    autoResizeTextarea();
    loadSavedConversation();
    setupKeyboardShortcuts();
});

// Event Listeners
function setupEventListeners() {
    sendBtn.addEventListener('click', handleSendMessage);
    
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    userInput.addEventListener('input', autoResizeTextarea);
    
    newChatBtn.addEventListener('click', startNewChat);
}

// Auto-resize textarea
function autoResizeTextarea() {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 200) + 'px';
}

// Input validation
function validateInput(message) {
    if (!message || message.trim().length === 0) {
        return 'Message cannot be empty';
    }
    
    if (message.length > 4000) {
        return 'Message is too long (maximum 4000 characters)';
    }
    
    return null;
}

// Enhanced error handling with retry logic
async function sendWithRetry(requestData, attempt = 1) {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);
        
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }
        
        return await response.json();
        
    } catch (error) {
        if (attempt < MAX_RETRIES && !error.name === 'AbortError') {
            console.log(`Request failed (attempt ${attempt}/${MAX_RETRIES}), retrying...`);
            await new Promise(resolve => setTimeout(resolve, RETRY_DELAY * attempt));
            return sendWithRetry(requestData, attempt + 1);
        }
        throw error;
    }
}

// Handle send message with enhanced error handling
async function handleSendMessage() {
    const message = userInput.value.trim();
    
    // Validate input
    const validationError = validateInput(message);
    if (validationError) {
        showError(validationError);
        return;
    }
    
    if (isLoading) return;
    
    // Hide welcome screen if visible
    if (welcomeScreen) {
        welcomeScreen.style.display = 'none';
    }
    
    // Add user message to UI
    addMessage(message, 'user');
    
    // Clear input
    userInput.value = '';
    autoResizeTextarea();
    
    // Disable send button and show loading state
    isLoading = true;
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<div class="spinner"></div>';
    
    // Add user message to history
    conversationHistory.push({
        role: 'user',
        content: message
    });
    
    // Show loading indicator
    const loadingElement = showLoading();
    
    try {
        const requestData = {
            message: message,
            history: conversationHistory.slice(0, -1), // Don't include current message
            model: modelSelect.value
        };
        
        const data = await sendWithRetry(requestData);
        
        // Remove loading indicator
        loadingElement.remove();
        
        // Add AI response to UI
        addMessage(data.response, 'ai');
        
        // Add AI response to history
        conversationHistory.push({
            role: 'assistant',
            content: data.response
        });
        
        // Save conversation
        saveConversation();
        retryCount = 0; // Reset retry count on success
        
    } catch (error) {
        console.error('Error:', error);
        loadingElement.remove();
        
        let errorMessage = 'দুঃখিত, একটি সমস্যা হয়েছে। দয়া করে আবার চেষ্টা করুন।';
        
        // Enhanced error messages
        if (error.name === 'AbortError') {
            errorMessage = 'Request timed out. Please try again.';
        } else if (error.message.includes('Rate limit')) {
            errorMessage = 'Too many requests. Please wait a moment and try again.';
        } else if (error.message.includes('Service temporarily unavailable')) {
            errorMessage = 'Service is temporarily unavailable. Please try again later.';
        } else if (error.message.includes('Network')) {
            errorMessage = 'Network error. Please check your connection and try again.';
        }
        
        showError(errorMessage);
        
        // Remove the user message from history if it failed
        conversationHistory.pop();
        
    } finally {
        isLoading = false;
        sendBtn.disabled = false;
        sendBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
        `;
        userInput.focus();
    }
}

// Add message to UI
function addMessage(content, role) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const avatarLetter = role === 'user' ? 'U' : 'Z';
    const name = role === 'user' ? 'You' : 'ZED';
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <div class="message-avatar ${role}-avatar">${avatarLetter}</div>
            <div class="message-name">${name}</div>
        </div>
        <div class="message-content">${formatMessage(content)}</div>
    `;
    
    messages.appendChild(messageDiv);
    scrollToBottom();
}

// Format message with markdown-like syntax
function formatMessage(content) {
    // Convert markdown code blocks to HTML
    content = content.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre><code>${escapeHtml(code.trim())}</code></pre>`;
    });
    
    // Convert inline code
    content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Convert bold text
    content = content.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Convert italic text
    content = content.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
    // Convert line breaks to paragraphs
    const paragraphs = content.split('\n\n');
    content = paragraphs.map(p => {
        if (p.startsWith('<pre>')) return p;
        return `<p>${p.replace(/\n/g, '<br>')}</p>`;
    }).join('');
    
    return content;
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show loading indicator
function showLoading() {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message ai-message';
    loadingDiv.innerHTML = `
        <div class="message-header">
            <div class="message-avatar ai-avatar">Z</div>
            <div class="message-name">ZED</div>
        </div>
        <div class="loading">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
    `;
    messages.appendChild(loadingDiv);
    scrollToBottom();
    return loadingDiv;
}

// Show error message
function showError(errorMessage) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = errorMessage;
    messages.appendChild(errorDiv);
    scrollToBottom();
}

// Scroll to bottom of chat
function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Save conversation to localStorage
function saveConversation() {
    try {
        localStorage.setItem('bedrock_chat_history', JSON.stringify(conversationHistory));
    } catch (error) {
        console.warn('Failed to save conversation:', error);
    }
}

// Load saved conversation from localStorage
function loadSavedConversation() {
    try {
        const saved = localStorage.getItem('bedrock_chat_history');
        if (saved) {
            conversationHistory = JSON.parse(saved);
            
            // Restore messages if any
            if (conversationHistory.length > 0) {
                welcomeScreen.style.display = 'none';
                
                for (let i = 0; i < conversationHistory.length; i++) {
                    const msg = conversationHistory[i];
                    const role = msg.role === 'assistant' ? 'ai' : msg.role;
                    addMessage(msg.content, role);
                }
            }
        }
    } catch (error) {
        console.warn('Failed to load saved conversation:', error);
        conversationHistory = [];
    }
}

// Setup keyboard shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + Enter to send message
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && !isLoading) {
            e.preventDefault();
            handleSendMessage();
        }
        
        // Ctrl/Cmd + K to start new chat
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            startNewChat();
        }
        
        // Escape to focus input
        if (e.key === 'Escape') {
            userInput.focus();
        }
    });
}

// Enhanced error display with action buttons
function showError(errorMessage) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message enhanced';
    errorDiv.innerHTML = `
        <div class="error-content">
            <div class="error-icon">⚠️</div>
            <div class="error-text">${errorMessage}</div>
        </div>
        <div class="error-actions">
            <button onclick="this.parentElement.parentElement.remove()" class="error-btn">Dismiss</button>
            <button onclick="handleSendMessage()" class="error-btn retry-btn">Retry</button>
        </div>
    `;
    messages.appendChild(errorDiv);
    scrollToBottom();
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.remove();
        }
    }, 10000);
}

// Start new chat with confirmation if there's existing conversation
function startNewChat() {
    if (conversationHistory.length > 0) {
        if (!confirm('Are you sure you want to start a new chat? This will clear the current conversation.')) {
            return;
        }
    }
    
    conversationHistory = [];
    messages.innerHTML = '';
    if (welcomeScreen) {
        welcomeScreen.style.display = 'flex';
    }
    userInput.value = '';
    autoResizeTextarea();
    userInput.focus();
    
    // Clear saved conversation
    try {
        localStorage.removeItem('bedrock_chat_history');
    } catch (error) {
        console.warn('Failed to clear saved conversation:', error);
    }
}

// Enhanced example prompt with typing animation
function useExample(text) {
    if (isLoading) return;
    
    userInput.value = '';
    let i = 0;
    const typingSpeed = 50;
    
    function typeWriter() {
        if (i < text.length) {
            userInput.value += text.charAt(i);
            i++;
            setTimeout(typeWriter, typingSpeed);
            autoResizeTextarea();
        } else {
            userInput.focus();
            // Auto-send after a brief pause
            setTimeout(() => {
                if (userInput.value === text) {
                    handleSendMessage();
                }
            }, 1000);
        }
    }
    
    typeWriter();
}

// Copy message to clipboard
function copyMessage(button, text) {
    navigator.clipboard.writeText(text).then(() => {
        const originalText = button.innerHTML;
        button.innerHTML = '✓ Copied';
        button.style.color = '#10a37f';
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.color = '';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// Export conversation as text file
function exportConversation() {
    if (conversationHistory.length === 0) {
        alert('No conversation to export');
        return;
    }
    
    let exportText = 'Bedrock Chat Conversation\n';
    exportText += '='.repeat(30) + '\n\n';
    
    conversationHistory.forEach((msg, index) => {
        const role = msg.role === 'assistant' ? 'AI Assistant' : 'User';
        exportText += `${role}:\n${msg.content}\n\n`;
    });
    
    const blob = new Blob([exportText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bedrock-chat-${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Make functions available globally
window.useExample = useExample;
window.copyMessage = copyMessage;
window.exportConversation = exportConversation;
