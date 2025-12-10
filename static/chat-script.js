// Global state
let currentUser = null;
let currentSessionId = null;
let isLoading = false;
let chatSessions = [];

// DOM elements
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const messages = document.getElementById('messages');
const welcomeScreen = document.getElementById('welcomeScreen');
const newChatBtn = document.getElementById('newChatBtn');
const modelSelect = document.getElementById('modelSelect');
const modelSearch = document.getElementById('modelSearch');
const chatContainer = document.getElementById('chatContainer');
const chatHistory = document.getElementById('chatHistory');
const logoutBtn = document.getElementById('logoutBtn');
const userInfo = document.getElementById('userInfo');
const menuToggle = document.getElementById('menuToggle');
const sidebar = document.getElementById('sidebar');
const sidebarClose = document.getElementById('sidebarClose');
const sidebarOverlay = document.getElementById('sidebarOverlay');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadUser();
    setupEventListeners();
    autoResizeTextarea();
    setupSidebarToggle();
    setupModelSearch();
    loadSessionFromUrl();
});

// Event Listeners
function setupEventListeners() {
    sendBtn.addEventListener('click', handleSendMessage);
    
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            if (e.shiftKey) {
                // Shift+Enter: Allow new line (default behavior)
                return;
            } else {
                // Enter only: Submit message
                e.preventDefault();
                handleSendMessage();
            }
        }
    });

    userInput.addEventListener('input', autoResizeTextarea);
    newChatBtn.addEventListener('click', startNewChat);
    logoutBtn.addEventListener('click', handleLogout);
}

// Setup sidebar toggle for mobile
function setupSidebarToggle() {
    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.add('open');
            sidebarOverlay.classList.add('active');
        });
    }
}

// Setup model search filter
function setupModelSearch() {
    if (modelSearch) {
        modelSearch.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase().trim();
            const optgroups = modelSelect.querySelectorAll('optgroup');
            
            if (!searchTerm) {
                // Show all options if search is empty
                optgroups.forEach(group => {
                    group.style.display = '';
                    group.querySelectorAll('option').forEach(opt => opt.style.display = '');
                });
                return;
            }
            
            // Filter options
            optgroups.forEach(group => {
                const options = group.querySelectorAll('option');
                let hasVisibleOptions = false;
                
                options.forEach(option => {
                    const modelName = option.textContent.toLowerCase();
                    const modelId = option.value.toLowerCase();
                    const groupName = group.label.toLowerCase();
                    
                    if (modelName.includes(searchTerm) || modelId.includes(searchTerm) || groupName.includes(searchTerm)) {
                        option.style.display = '';
                        hasVisibleOptions = true;
                    } else {
                        option.style.display = 'none';
                    }
                });
                
                // Show/hide optgroup based on visible options
                group.style.display = hasVisibleOptions ? '' : 'none';
            });
        });
    }

    if (sidebarClose) {
        sidebarClose.addEventListener('click', closeSidebar);
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeSidebar);
    }
}

function closeSidebar() {
    sidebar.classList.remove('open');
    sidebarOverlay.classList.remove('active');
}

// Load session from URL on page load
function loadSessionFromUrl() {
    // Check if initialSessionId and shareHash were passed from backend
    if (typeof window.initialSessionId !== 'undefined' && window.initialSessionId !== null) {
        const shareHash = typeof window.initialShareHash !== 'undefined' ? window.initialShareHash : null;
        // Wait a bit for user to be loaded
        setTimeout(() => {
            loadSession(window.initialSessionId, shareHash);
        }, 500);
    }
}

// Load current user
async function loadUser() {
    try {
        const response = await fetch('/api/user');
        if (response.ok) {
            currentUser = await response.json();
            document.querySelector('.user-name').textContent = currentUser.username;
            document.querySelector('.user-avatar').textContent = currentUser.username[0].toUpperCase();
            loadSessions();
        } else {
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Failed to load user:', error);
        window.location.href = '/';
    }
}

// Load chat sessions
async function loadSessions() {
    try {
        const response = await fetch('/api/sessions');
        if (response.ok) {
            chatSessions = await response.json();
            renderSessions();
        }
    } catch (error) {
        console.error('Failed to load sessions:', error);
    }
}

// Render sessions in sidebar
function renderSessions() {
    chatHistory.innerHTML = '';
    
    if (chatSessions.length === 0) {
        chatHistory.innerHTML = '<div style="padding: 12px; color: rgba(255,255,255,0.5); font-size: 13px; text-align: center;">No conversations yet</div>';
        return;
    }
    
    chatSessions.forEach(session => {
        const sessionEl = document.createElement('div');
        sessionEl.className = 'chat-session' + (session.id === currentSessionId ? ' active' : '');
        sessionEl.innerHTML = `
            <span class="chat-session-title">${session.title}</span>
            <button class="delete-session" onclick="deleteSession(event, ${session.id}, '${session.share_hash}')">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
            </button>
        `;
        sessionEl.addEventListener('click', (e) => {
            if (!e.target.closest('.delete-session')) {
                loadSession(session.id, session.share_hash);
            }
        });
        chatHistory.appendChild(sessionEl);
    });
}

// Load a specific session
async function loadSession(sessionId, shareHash) {
    try {
        const response = await fetch(`/api/sessions/${sessionId}`);
        if (response.ok) {
            const data = await response.json();
            currentSessionId = sessionId;
            
            // Clear and load messages
            messages.innerHTML = '';
            welcomeScreen.style.display = 'none';
            
            data.messages.forEach(msg => {
                addMessage(msg.content, msg.role);
            });
            
            renderSessions();
            
            // Update URL without reloading page using share_hash
            if (window.history && window.history.pushState && shareHash) {
                window.history.pushState(null, '', `/c/${shareHash}`);
            }
            
            // Close sidebar on mobile
            if (window.innerWidth <= 768) {
                closeSidebar();
            }
        }
    } catch (error) {
        console.error('Failed to load session:', error);
    }
}

// Delete session
async function deleteSession(event, sessionId) {
    event.stopPropagation();
    
    if (!confirm('Delete this conversation?')) return;
    
    try {
        const response = await fetch(`/api/sessions/${sessionId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            if (currentSessionId === sessionId) {
                startNewChat();
            }
            await loadSessions();
        }
    } catch (error) {
        console.error('Failed to delete session:', error);
    }
}

// Handle logout
async function handleLogout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
        window.location.href = '/';
    } catch (error) {
        console.error('Logout failed:', error);
        window.location.href = '/';
    }
}

// Auto-resize textarea
function autoResizeTextarea() {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 200) + 'px';
}

// Handle send message
async function handleSendMessage() {
    const message = userInput.value.trim();
    
    if (!message || isLoading) return;
    
    // Hide welcome screen
    if (welcomeScreen) {
        welcomeScreen.style.display = 'none';
    }
    
    // Add user message
    addMessage(message, 'user');
    
    // Clear input
    userInput.value = '';
    autoResizeTextarea();
    
    // Disable send button
    isLoading = true;
    sendBtn.disabled = true;
    
    // Show loading
    const loadingElement = showLoading();
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: currentSessionId,
                model: modelSelect.value
            })
        });
        
        if (!response.ok) {
            throw new Error('Request failed');
        }
        
        const data = await response.json();
        
        // Remove loading
        loadingElement.remove();
        
        // Add AI response
        addMessage(data.response, 'assistant');
        
        // Update session ID
        if (!currentSessionId) {
            currentSessionId = data.session_id;
            await loadSessions();
        }
        
    } catch (error) {
        console.error('Error:', error);
        loadingElement.remove();
        showError('Sorry, something went wrong. Please try again.');
    } finally {
        isLoading = false;
        sendBtn.disabled = false;
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
            <div class="message-avatar">${avatarLetter}</div>
            <div class="message-name">${name}</div>
        </div>
        <div class="message-content">${formatMessage(content)}</div>
    `;
    
    messages.appendChild(messageDiv);
    scrollToBottom();
}

// Format message
function formatMessage(content) {
    // Remove AI thinking/reasoning patterns (text before actual answer)
    // Patterns: <reasoning>...</reasoning>, "User wants...", "The user...", etc.
    content = content.replace(/<reasoning>[\s\S]*?<\/reasoning>/gi, '');
    content = content.replace(/^(User |The user |They ).*?\. (We|I) should.*?\n\n/gim, '');
    content = content.replace(/^.*?(User wants|They want|The user).*?\n\n/gim, '');
    
    // Store code blocks temporarily to prevent markdown parsing
    const codeBlocks = [];
    content = content.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
        const index = codeBlocks.length;
        codeBlocks.push({ lang: lang || 'text', code: code.trim() });
        return `__CODE_BLOCK_${index}__`;
    });
    
    // Configure marked for better rendering
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true,
            headerIds: false,
            mangle: false
        });
        content = marked.parse(content);
    }
    
    // Restore code blocks with execution buttons
    content = content.replace(/__CODE_BLOCK_(\d+)__/g, (match, index) => {
        const { lang, code } = codeBlocks[parseInt(index)];
        const language = lang || 'text';
        const canExecute = language === 'python' || language === 'javascript' || language === 'js';
        
        const executeBtn = canExecute ? 
            `<button class="code-execute-btn" onclick="executeCode('${escapeForAttribute(code)}', '${language === 'js' ? 'javascript' : language}')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="5 3 19 12 5 21 5 3"></polygon>
                </svg>
                Run Code
            </button>` : '';
        
        const copyBtn = `<button class="code-copy-btn" onclick="copyCode('${escapeForAttribute(code)}')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
            Copy
        </button>`;
        
        return `<div class="code-block">
            <div class="code-header">
                <span class="code-language">${language}</span>
                <div class="code-actions">
                    ${copyBtn}
                    ${executeBtn}
                </div>
            </div>
            <pre><code>${escapeHtml(code)}</code></pre>
        </div>`;
    });
    
    return content;
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Escape for HTML attribute
function escapeForAttribute(text) {
    return text.replace(/'/g, "\\'").replace(/"/g, "&quot;").replace(/\n/g, "\\n");
}

// Copy code to clipboard
async function copyCode(code) {
    try {
        // Unescape the code
        code = code.replace(/\\n/g, '\n').replace(/\\'/g, "'");
        await navigator.clipboard.writeText(code);
        
        // Show feedback
        const btn = event.target.closest('.code-copy-btn');
        const originalText = btn.innerHTML;
        btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"></polyline>
        </svg> Copied!`;
        
        setTimeout(() => {
            btn.innerHTML = originalText;
        }, 2000);
    } catch (error) {
        console.error('Failed to copy code:', error);
    }
}

// Execute code
async function executeCode(code, language) {
    const btn = event.target.closest('.code-execute-btn');
    const originalHTML = btn.innerHTML;
    
    try {
        // Unescape the code
        code = code.replace(/\\n/g, '\n').replace(/\\'/g, "'");
        
        // Show loading
        btn.disabled = true;
        btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spinning">
            <circle cx="12" cy="12" r="10"></circle>
        </svg> Running...`;
        
        const response = await fetch('/api/execute-code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                code: code,
                language: language
            })
        });
        
        if (!response.ok) {
            throw new Error('Execution failed');
        }
        
        const result = await response.json();
        
        // Create output message
        const outputDiv = document.createElement('div');
        outputDiv.className = 'code-output';
        
        if (result.success) {
            outputDiv.innerHTML = `
                <div class="output-header success">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    Execution Successful
                </div>
                <pre class="output-content">${escapeHtml(result.output)}</pre>
            `;
        } else {
            outputDiv.innerHTML = `
                <div class="output-header error">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="8" x2="12" y2="12"></line>
                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                    </svg>
                    Execution Failed
                </div>
                <pre class="output-content error">${escapeHtml(result.error)}</pre>
            `;
        }
        
        // Insert output after the code block
        const codeBlock = btn.closest('.code-block');
        codeBlock.parentNode.insertBefore(outputDiv, codeBlock.nextSibling);
        
        btn.innerHTML = originalHTML;
        btn.disabled = false;
        
    } catch (error) {
        console.error('Code execution error:', error);
        btn.innerHTML = originalHTML;
        btn.disabled = false;
        showError('Failed to execute code. Please try again.');
    }
}

// Show loading with typing indicator
function showLoading() {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant-message';
    loadingDiv.innerHTML = `
        <div class="message-header">
            <div class="message-avatar">Z</div>
            <div class="message-name">ZED</div>
            <div class="typing-indicator">
                <span>typing</span>
                <span class="typing-dots">
                    <span>.</span><span>.</span><span>.</span>
                </span>
            </div>
        </div>
        <div class="message-content">
            <div class="loading">
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
            </div>
        </div>
    `;
    messages.appendChild(loadingDiv);
    scrollToBottom();
    return loadingDiv;
}

// Show error
function showError(errorMessage) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = errorMessage;
    messages.appendChild(errorDiv);
    scrollToBottom();
}

// Scroll to bottom
function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Start new chat
function startNewChat() {
    currentSessionId = null;
    messages.innerHTML = '';
    if (welcomeScreen) {
        welcomeScreen.style.display = 'flex';
    }
    userInput.value = '';
    autoResizeTextarea();
    userInput.focus();
    renderSessions();
    
    // Update URL to root when starting new chat
    if (window.history && window.history.pushState) {
        window.history.pushState(null, '', '/chat');
    }
}

// Use example
function useExample(text) {
    userInput.value = text;
    autoResizeTextarea();
    userInput.focus();
    handleSendMessage();
}

// Make functions globally available
window.useExample = useExample;
window.deleteSession = deleteSession;
window.copyCode = copyCode;
window.executeCode = executeCode;
