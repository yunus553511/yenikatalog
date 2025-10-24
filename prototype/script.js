// DOM Elements
const chatWidget = document.getElementById('chatWidget');
const chatMinimized = document.getElementById('chatMinimized');
const chatExpanded = document.getElementById('chatExpanded');
const closeBtn = document.getElementById('closeBtn');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');

// State
let isExpanded = false;

// Toggle Chat Widget
function toggleChat() {
    isExpanded = !isExpanded;
    
    if (isExpanded) {
        chatMinimized.style.display = 'none';
        chatExpanded.style.display = 'flex';
        chatInput.focus();
    } else {
        chatExpanded.style.display = 'none';
        chatMinimized.style.display = 'flex';
    }
}

// Add Message
function addMessage(content, role = 'user') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // Format message (convert markdown-like syntax to HTML)
    const formattedContent = formatMessage(content);
    messageContent.innerHTML = formattedContent;
    
    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Format message with basic markdown support
function formatMessage(text) {
    // Convert **bold** to <strong>
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert bullet points
    text = text.replace(/^• /gm, '&bull; ');
    
    // Convert newlines to <br>
    text = text.replace(/\n/g, '<br>');
    
    return text;
}

// Show Typing Indicator
function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant';
    typingDiv.id = 'typingIndicator';
    
    const typingContent = document.createElement('div');
    typingContent.className = 'typing-indicator';
    typingContent.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;
    
    typingDiv.appendChild(typingContent);
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Remove Typing Indicator
function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Real API Response
async function getAPIResponse(userMessage) {
    // Otomatik olarak doğru API URL'i seç
    let API_URL;
    
    if (window.location.hostname === 'localhost') {
        // Lokal geliştirme
        API_URL = 'http://localhost:8001/api/chat';
    } else {
        // Production - Render.com backend URL'i
        // Backend deploy edince bu URL'i güncelleyin
        API_URL = 'https://beymetal-backend.onrender.com/api/chat';
    }
    
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: userMessage,
                conversation_history: []
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        return data.message;
        
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Send Message
async function sendMessage() {
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    // Add user message
    addMessage(message, 'user');
    chatInput.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        // Get real API response
        const response = await getAPIResponse(message);
        
        // Remove typing indicator
        removeTypingIndicator();
        
        // Add assistant response
        addMessage(response, 'assistant');
    } catch (error) {
        removeTypingIndicator();
        addMessage('Üzgünüm, sunucuya bağlanılamadı. Lütfen backend\'in çalıştığından emin olun.', 'assistant');
    }
}

// Event Listeners
chatMinimized.addEventListener('click', toggleChat);
closeBtn.addEventListener('click', toggleChat);
sendBtn.addEventListener('click', sendMessage);

chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Sayfa yenilendiğinde sohbet geçmişi otomatik temizlenir
// localStorage kullanılmıyor - her seferinde temiz başlangıç

// Add more animated lines dynamically
function addDynamicLines() {
    const background = document.querySelector('.animated-background');
    const lineCount = 8;
    
    for (let i = 5; i <= lineCount; i++) {
        const line = document.createElement('div');
        line.className = 'line';
        line.style.width = Math.random() > 0.5 ? '2px' : '1px';
        line.style.left = `${(i / lineCount) * 100}%`;
        line.style.animationDelay = `${Math.random() * 8}s`;
        background.appendChild(line);
    }
}

// Initialize dynamic lines
addDynamicLines();
