// API Configuration
const API_BASE_URL = 'http://localhost:8004';

// DOM Elements
const chatWidget = document.getElementById('chatWidget');
const chatMinimized = document.getElementById('chatMinimized');
const chatExpanded = document.getElementById('chatExpanded');
const closeBtn = document.getElementById('closeBtn');
const resetBtn = document.getElementById('resetBtn');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');

// State
let isExpanded = false;
let conversationHistory = []; // Konuşma geçmişini tut (OpenAI format)

// Message state management for load more functionality
const messageStates = new Map(); // messageId -> { messageId, profileData, displayedCount, totalCount, batchSize }

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
function addMessage(content, role = 'user', profileData = null) {
    console.log('addMessage called:', { role, profileDataLength: profileData ? profileData.length : 0 });
    
    const messageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.setAttribute('data-message-id', messageId);
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // Check if we have profile data and need load more functionality
    if (profileData && profileData.length > 15) {
        console.log('Creating load more button for', profileData.length, 'profiles');
        // Format message with only first 15 profiles
        const { formattedContent, displayedProfiles } = formatMessageWithLoadMore(
            content,
            profileData,
            15
        );
        messageContent.innerHTML = formattedContent;
        
        // Save state
        messageStates.set(messageId, {
            messageId,
            profileData,
            displayedCount: displayedProfiles,
            totalCount: profileData.length,
            batchSize: 15
        });
        
        // Add load more button inside message content
        const loadMoreBtn = createLoadMoreButton(messageId);
        messageContent.appendChild(document.createElement('br'));
        messageContent.appendChild(loadMoreBtn);
        
        messageDiv.appendChild(messageContent);
    } else {
        // Normal message or few profiles
        const formattedContent = formatMessage(content);
        messageContent.innerHTML = formattedContent;
        messageDiv.appendChild(messageContent);
    }
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to top of new message (not bottom)
    if (role === 'assistant') {
        // Assistant mesajı için mesajın başına scroll et
        messageDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
        // User mesajı için en alta scroll et
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Format message with basic markdown support
function formatMessage(text) {
    // Convert markdown images ![alt](url) to HTML img tags
    text = text.replace(/!\[(.*?)\]\((.*?)\)/g, '<img src="$2" alt="$1" class="chat-profile-image" />');
    
    // Convert **bold** to <strong>
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert bullet points
    text = text.replace(/^• /gm, '&bull; ');
    
    // Convert newlines to <br>
    text = text.replace(/\n/g, '<br>');
    
    return text;
}

// Format message with load more (show only first N profiles)
function formatMessageWithLoadMore(text, profileData, initialCount) {
    let profileIndex = 0;
    
    // Replace markdown images, but only show first N
    const formattedText = text.replace(
        /!\[(.*?)\]\((.*?)\)/g,
        (match, alt, url) => {
            if (profileIndex < initialCount) {
                profileIndex++;
                return `<img src="${url}" alt="${alt}" class="chat-profile-image" />`;
            }
            return ''; // Don't show remaining profiles
        }
    );
    
    // Apply other formatting
    let result = formattedText;
    result = result.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    result = result.replace(/^• /gm, '&bull; ');
    result = result.replace(/\n/g, '<br>');
    
    return {
        formattedContent: result,
        displayedProfiles: profileIndex
    };
}

// Create load more button
function createLoadMoreButton(messageId) {
    const state = messageStates.get(messageId);
    if (!state) return null;
    
    const remaining = state.totalCount - state.displayedCount;
    const nextBatch = Math.min(remaining, state.batchSize);
    
    const button = document.createElement('button');
    button.className = 'load-more-button';
    button.setAttribute('data-message-id', messageId);
    button.innerHTML = `
        <svg class="load-more-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
        <span class="load-more-text">
            ${nextBatch === remaining 
                ? `Son ${remaining} Profili Göster` 
                : `${nextBatch} Profil Daha Göster`}
        </span>
        <span class="load-more-count">(${remaining} kaldı)</span>
    `;
    
    button.onclick = () => loadMoreProfiles(messageId);
    
    return button;
}

// Load more profiles
function loadMoreProfiles(messageId) {
    const state = messageStates.get(messageId);
    if (!state) return;
    
    const button = document.querySelector(`button[data-message-id="${messageId}"]`);
    const messageDiv = document.querySelector(`div[data-message-id="${messageId}"]`);
    const messageContent = messageDiv.querySelector('.message-content');
    
    // Loading state
    button.disabled = true;
    button.innerHTML = `
        <div class="typing-indicator" style="display: inline-flex; gap: 4px;">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    
    // Simulate loading (instant in reality, but smooth UX)
    setTimeout(() => {
        // Get next batch
        const nextBatch = state.profileData.slice(
            state.displayedCount,
            state.displayedCount + state.batchSize
        );
        
        // Remove button temporarily (we'll add it back at the end)
        button.remove();
        
        // Save scroll position before adding new content
        const buttonPosition = button.offsetTop;
        
        // Render and append profiles with markdown format (same as backend)
        nextBatch.forEach((profile, index) => {
            const profileNumber = state.displayedCount + index + 1;
            
            // Get full image URL
            const imageUrl = getProfileImageUrl(profile.code);
            
            // Create markdown-style profile display with numbering
            const profileHTML = `
                <br><br><strong>${profileNumber}. ${profile.code}</strong><br>
                <img src="${imageUrl}" alt="${profile.code}" class="chat-profile-image" />
                ${profile.category ? `<br>Kategori: ${profile.category}` : ''}
                ${profile.customer ? `<br>Müşteri: ${profile.customer}` : ''}
                ${profile.mold_status ? `<br>Kalıp: ${profile.mold_status}` : ''}
            `;
            
            // Append to message content (before button)
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = profileHTML;
            while (tempDiv.firstChild) {
                messageContent.appendChild(tempDiv.firstChild);
            }
        });
        
        // Update state
        state.displayedCount += nextBatch.length;
        messageStates.set(messageId, state);
        
        // Update or remove button
        const remaining = state.totalCount - state.displayedCount;
        if (remaining > 0) {
            // Still more profiles, update button and add it back
            const nextBatchSize = Math.min(remaining, state.batchSize);
            button.disabled = false;
            button.innerHTML = `
                <svg class="load-more-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
                <span class="load-more-text">
                    ${nextBatchSize === remaining 
                        ? `Son ${remaining} Profili Göster` 
                        : `${nextBatchSize} Profil Daha Göster`}
                </span>
                <span class="load-more-count">(${remaining} kaldı)</span>
            `;
            
            // Add button back to the end of message content
            messageContent.appendChild(document.createElement('br'));
            messageContent.appendChild(button);
            
            // Scroll to button position (stay where we were, don't jump to bottom)
            setTimeout(() => {
                button.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 50);
        } else {
            // If no remaining profiles, scroll to end of message
            setTimeout(() => {
                messageDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
            }, 50);
        }
    }, 300);
}

// Profil görsel URL'ini oluştur
function getProfileImageUrl(profileCode) {
    if (window.location.hostname === 'localhost') {
        return `http://localhost:8002/api/profile-image/${profileCode}`;
    } else {
        return `https://beymetal-backend.onrender.com/api/profile-image/${profileCode}`;
    }
}

// Görsel modal'ını göster
function showImageModal(imageUrl, profileCode) {
    // Modal oluştur
    const modal = document.createElement('div');
    modal.className = 'image-modal';
    modal.innerHTML = `
        <div class="image-modal-content">
            <span class="image-modal-close" onclick="closeImageModal()">&times;</span>
            <img src="${imageUrl}" alt="${profileCode}" class="image-modal-img">
            <div class="image-modal-caption">${profileCode}</div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Modal'a tıklanınca kapat
    modal.onclick = function(e) {
        if (e.target === modal) {
            closeImageModal();
        }
    };
}

// Modal'ı kapat
function closeImageModal() {
    const modal = document.querySelector('.image-modal');
    if (modal) {
        modal.remove();
    }
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
    let API_URL;
    
    if (window.location.hostname === 'localhost') {
        API_URL = 'http://localhost:8002/api/chat';
    } else {
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
                conversation_history: conversationHistory.length > 0 ? conversationHistory : null
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update conversation history from backend
        if (data.conversation_history) {
            conversationHistory = data.conversation_history;
        }
        
        // Return full response object (including profile_data)
        return {
            message: data.message,
            profile_data: data.profile_data || null
        };
        
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
        // Get real API response (conversation history managed by backend)
        const response = await getAPIResponse(message);
        
        // Debug: Log response
        console.log('API Response:', response);
        console.log('Profile data:', response.profile_data);
        console.log('Profile data length:', response.profile_data ? response.profile_data.length : 0);
        
        // Remove typing indicator
        removeTypingIndicator();
        
        // Add assistant response with profile data
        addMessage(response.message, 'assistant', response.profile_data);
        
    } catch (error) {
        console.error('Send message error:', error);
        removeTypingIndicator();
        addMessage('Üzgünüm, sunucuya bağlanılamadı. Lütfen backend\'in çalıştığından emin olun.', 'assistant');
    }
}

// Reset Conversation
function resetConversation() {
    // Clear conversation history
    conversationHistory = [];
    
    // Clear chat messages
    chatMessages.innerHTML = `
        <div class="message assistant">
            <div class="message-content">
                Merhaba! Ben ALUNA, Beymetal'in alüminyum profil asistanıyım.
                Standart profilleri ölçü, kategori ve kalınlık bilgilerine göre arayabilirsiniz.
                <br><br>
                <strong>Örnek aramalar:</strong><br>
                • "100 kutu" - A veya B ölçüsü 100mm olan kutular<br>
                • "çap 28" - Çapı 28mm olan borular<br>
                • "30x30 lama" - 30x30mm lamalar<br>
                • "kalınlığı 2mm olan kutu" - 2mm et kalınlığındaki kutular
            </div>
        </div>
    `;
    
    console.log('Conversation reset');
}

// Event Listeners
chatMinimized.addEventListener('click', toggleChat);
closeBtn.addEventListener('click', toggleChat);
resetBtn.addEventListener('click', resetConversation);
sendBtn.addEventListener('click', sendMessage);

chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

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


// ============================================
// CATALOG FUNCTIONS
// ============================================

// Seçili şirketler (boş array = hepsi seçili)
let selectedCompanies = [];

async function loadCategories() {
    let API_URL;
    
    if (window.location.hostname === 'localhost') {
        API_URL = 'http://localhost:8002';
    } else {
        API_URL = 'https://beymetal-backend.onrender.com';
    }
    
    try {
        // Şirket filtresi ekle
        let url = `${API_URL}/api/catalog/categories`;
        if (selectedCompanies.length > 0) {
            url += `?companies=${selectedCompanies.join(',')}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        displayCategories(data.categories, data.stats);
    } catch (error) {
        console.error('Kategori yükleme hatası:', error);
        document.getElementById('categorySections').innerHTML = `
            <div class="loading" style="color: #e24a4a;">
                Kategoriler yüklenemedi. Backend çalışıyor mu?
            </div>
        `;
    }
}

function displayCategories(categories, stats) {
    const container = document.getElementById('categorySections');
    
    const categoryTypes = [
        { key: 'standard', title: 'STANDART PROFİLLER' },
        { key: 'shape', title: 'ŞEKİLSEL KATEGORİ' },
        { key: 'sector', title: 'SEKTÖREL PROFİLLER' }
    ];
    
    // Mobilde mi kontrol et
    const isMobile = window.innerWidth <= 1024;
    
    let html = '';
    
    categoryTypes.forEach(type => {
        const cats = categories[type.key] || [];
        
        if (cats.length > 0) {
            html += `
                <div class="category-group ${type.key} ${isMobile ? 'collapsed' : ''}">
                    <div class="category-group-title" onclick="toggleCategoryGroup('${type.key}')">
                        <span>${type.title}</span>
                        <span class="toggle-icon">${isMobile ? '▶' : '▼'}</span>
                    </div>
                    <div class="category-search-box">
                        <input 
                            type="text" 
                            class="category-search-input" 
                            id="search-${type.key}"
                            placeholder="Alt kategori ara..."
                            oninput="filterCategories('${type.key}')"
                            onclick="event.stopPropagation()"
                        />
                        <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"></circle>
                            <path d="m21 21-4.35-4.35"></path>
                        </svg>
                    </div>
                    <div class="category-list" id="category-list-${type.key}" style="${isMobile ? 'display: none;' : ''}">
            `;
            
            cats.forEach(cat => {
                html += `
                    <div class="category-item" onclick="openCategoryChat('${cat}')">
                        <div>${cat}</div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        }
    });
    
    container.innerHTML = html;
}

function toggleCategoryGroup(groupKey) {
    const categoryList = document.getElementById(`category-list-${groupKey}`);
    const groupElement = categoryList.parentElement;
    const toggleIcon = groupElement.querySelector('.toggle-icon');
    
    if (categoryList.style.display === 'none') {
        categoryList.style.display = 'grid';
        toggleIcon.textContent = '▼';
        groupElement.classList.remove('collapsed');
    } else {
        categoryList.style.display = 'none';
        toggleIcon.textContent = '▶';
        groupElement.classList.add('collapsed');
    }
}

function filterCategories(groupKey) {
    const searchInput = document.getElementById(`search-${groupKey}`);
    const searchTerm = searchInput.value.toLowerCase().trim();
    const categoryList = document.getElementById(`category-list-${groupKey}`);
    const categoryItems = categoryList.querySelectorAll('.category-item');
    
    let visibleCount = 0;
    
    categoryItems.forEach(item => {
        const categoryName = item.querySelector('div').textContent.toLowerCase();
        
        if (categoryName.includes(searchTerm)) {
            item.style.display = 'flex';
            visibleCount++;
        } else {
            item.style.display = 'none';
        }
    });
    
    // Eğer hiç sonuç yoksa bilgi göster
    const existingNoResult = categoryList.querySelector('.no-result-message');
    if (existingNoResult) {
        existingNoResult.remove();
    }
    
    if (visibleCount === 0 && searchTerm !== '') {
        const noResultDiv = document.createElement('div');
        noResultDiv.className = 'no-result-message';
        noResultDiv.textContent = 'Sonuç bulunamadı';
        categoryList.appendChild(noResultDiv);
    }
}

async function openCategoryChat(category) {
    // Ana sayfada profilleri göster
    showCategoryProfiles(category);
}

// Kategori profillerini ana sayfada göster
async function showCategoryProfiles(category) {
    // Ana içeriği gizle, profil görünümünü göster
    const mainContent = document.querySelector('.main-content');
    
    // Profil container oluştur
    const profileContainer = document.createElement('div');
    profileContainer.className = 'profile-view-container';
    profileContainer.innerHTML = `
        <div class="profile-view-header">
            <button class="back-button" onclick="closeProfileView()">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M19 12H5M12 19l-7-7 7-7"/>
                </svg>
                Geri
            </button>
            <h1>${category}</h1>
        </div>
        <div class="profile-view-body">
            <div class="loading">Profiller yükleniyor...</div>
        </div>
    `;
    
    mainContent.style.display = 'none';
    document.querySelector('.main-content').parentElement.appendChild(profileContainer);
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // API'den profilleri al
    try {
        let API_URL;
        if (window.location.hostname === 'localhost') {
            API_URL = `http://localhost:8002/api/catalog/category/${encodeURIComponent(category)}`;
        } else {
            API_URL = `https://beymetal-backend.onrender.com/api/catalog/category/${encodeURIComponent(category)}`;
        }
        
        const response = await fetch(API_URL);
        const data = await response.json();
        
        // Profilleri göster
        displayCategoryProfiles(data.profiles, category);
        
    } catch (error) {
        console.error('Profil yükleme hatası:', error);
        const viewBody = document.querySelector('.profile-view-body');
        if (viewBody) {
            viewBody.innerHTML = '<div class="error">Profiller yüklenemedi.</div>';
        }
    }
}

// Profil görünümünü kapat
function closeProfileView() {
    const profileContainer = document.querySelector('.profile-view-container');
    const mainContent = document.querySelector('.main-content');
    
    if (profileContainer) {
        profileContainer.remove();
    }
    
    if (mainContent) {
        mainContent.style.display = 'block';
    }
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Kategori profillerini göster
function displayCategoryProfiles(profiles, category) {
    const viewBody = document.querySelector('.profile-view-body');
    
    if (!profiles || profiles.length === 0) {
        viewBody.innerHTML = '<div class="no-results">Bu kategoride profil bulunamadı.</div>';
        return;
    }
    
    let html = `<div class="profile-grid">`;
    
    profiles.forEach(profile => {
        const imageUrl = getProfileImageUrl(profile.code);
        const categories = profile.categories ? profile.categories.join(', ') : '';
        const moldStatus = profile.mold_status || 'Bilgi yok';
        const customer = profile.customer || '';
        const description = profile.description || '';
        const similarityScore = profile.similarity_score;
        
        // Benzerlik skoru badge rengi
        let scoreBadge = '';
        if (similarityScore !== undefined) {
            const scorePercent = Math.round(similarityScore * 100);
            let badgeClass = 'similarity-low';
            if (similarityScore >= 0.8) badgeClass = 'similarity-high';
            else if (similarityScore >= 0.6) badgeClass = 'similarity-medium';
            
            scoreBadge = `<div class="similarity-badge ${badgeClass}">%${scorePercent} Benzer</div>`;
        }
        
        html += `
            <div class="profile-card">
                ${scoreBadge}
                <div class="profile-card-image profile-image-zoom">
                    <img src="${imageUrl}" 
                         alt="${profile.code}" 
                         onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22200%22%3E%3Crect fill=%22%23f0f0f0%22 width=%22200%22 height=%22200%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-family=%22sans-serif%22 font-size=%2216%22 fill=%22%23999%22%3EGörsel Yok%3C/text%3E%3C/svg%3E'">
                </div>
                <div class="profile-card-info">
                    <h3>${profile.code}</h3>
                    ${customer ? `<p><strong>Müşteri:</strong> ${customer}</p>` : ''}
                    ${description ? `<p><strong>Açıklama:</strong> ${description}</p>` : ''}
                    ${categories ? `<p><strong>Kategoriler:</strong> ${categories}</p>` : ''}
                    <p><strong>Kalıp:</strong> <span class="mold-status ${moldStatus.includes('Mevcut') ? 'available' : 'unavailable'}">${moldStatus}</span></p>
                </div>
            </div>
        `;
    });
    
    html += `</div>`;
    viewBody.innerHTML = html;
}

// Logo tıklama fonksiyonu
function toggleCompanyFilter(company) {
    const index = selectedCompanies.indexOf(company);
    
    if (index === -1) {
        // Şirket seçili değilse ekle
        selectedCompanies.push(company);
    } else {
        // Şirket seçiliyse çıkar
        selectedCompanies.splice(index, 1);
    }
    
    // Logo görünümünü güncelle
    updateLogoStates();
    
    // Kategorileri yeniden yükle
    loadCategories();
}

function updateLogoStates() {
    const logos = {
        'linearossa': document.querySelector('.linearossa-logo'),
        'beymetal': document.querySelector('.beymetal-logo'),
        'alfore': document.querySelector('.alfore-logo')
    };
    
    // Hiçbiri seçili değilse hepsi aktif görünsün
    const allActive = selectedCompanies.length === 0;
    
    Object.keys(logos).forEach(company => {
        const logo = logos[company];
        if (allActive || selectedCompanies.includes(company)) {
            logo.classList.add('active');
            logo.classList.remove('inactive');
        } else {
            logo.classList.remove('active');
            logo.classList.add('inactive');
        }
    });
}
// Görsel zoom toggle (tıklama ile)
document.addEventListener('click', (e) => {
    if (e.target.closest('.profile-image-zoom img')) {
        const imageContainer = e.target.closest('.profile-image-zoom');
        imageContainer.classList.toggle('active');
    } else {
        // Dışarı tıklanınca tüm zoom'ları kapat
        document.querySelectorAll('.profile-image-zoom.active').forEach(el => {
            el.classList.remove('active');
        });
    }
});

// Sayfa yüklendiğinde kategorileri yükle ve logo event listener'ları ekle
window.addEventListener('load', () => {
    loadCategories();
    updateLogoStates();
    
    // Logo tıklama event listener'ları
    document.querySelector('.linearossa-logo').addEventListener('click', () => toggleCompanyFilter('linearossa'));
    document.querySelector('.beymetal-logo').addEventListener('click', () => toggleCompanyFilter('beymetal'));
    document.querySelector('.alfore-logo').addEventListener('click', () => toggleCompanyFilter('alfore'));
});


// ============================================
// CONNECTION SIDEBAR
// ============================================

class ConnectionSidebar {
    constructor() {
        this.sidebar = document.getElementById('connectionSidebar');
        this.content = document.getElementById('sidebarContent');
        
        this.systems = [];
        this.filteredSystems = [];
        this.searchQuery = '';
        
        this.init();
    }
    
    async init() {
        // Load systems
        await this.loadSystems();
    }
    
    async loadSystems() {
        try {
            // API URL'ini belirle
            const apiUrl = window.location.hostname === 'localhost' 
                ? 'http://localhost:8002' 
                : 'https://beymetal-backend.onrender.com';
            
            const response = await fetch(`${apiUrl}/api/connections/systems`);
            const data = await response.json();
            
            if (data.success) {
                this.systems = data.data;
                this.filteredSystems = this.systems;
                this.render();
            } else {
                this.showError('Sistemler yüklenemedi');
            }
        } catch (error) {
            console.error('Failed to load systems:', error);
            this.showError('Bağlantı hatası');
        }
    }
    

    
    render() {
        if (!this.content) return;
        
        if (this.systems.length === 0) {
            this.content.innerHTML = '<div class="loading">Sistem bulunamadı</div>';
            return;
        }
        
        const html = this.systems.map(system => this.renderSystem(system)).join('');
        this.content.innerHTML = html;
        
        // Add click events
        this.content.querySelectorAll('.system-item').forEach(item => {
            item.addEventListener('click', () => {
                const systemName = item.getAttribute('data-system-name');
                this.openSystemModal(systemName);
            });
        });
    }
    
    renderSystem(system) {
        const profileCount = system.profiles.length;
        
        return `
            <div class="system-item" data-system-name="${system.name}" title="${system.name} - ${profileCount} profil">
                <div class="system-header">
                    <span class="system-name">${system.name}</span>
                </div>
            </div>
        `;
    }
    
    openSystemModal(systemName) {
        const system = this.systems.find(s => s.name === systemName);
        if (!system) return;
        
        const modal = document.getElementById('systemModal');
        const modalSystemName = document.getElementById('modalSystemName');
        const modalBody = document.getElementById('modalBody');
        
        modalSystemName.textContent = system.name;
        
        // Render profiles with transparent PNGs
        const profilesHTML = system.profiles.map(profile => this.renderProfileConnection(profile)).join('');
        modalBody.innerHTML = profilesHTML || '<p style="color: rgba(255,255,255,0.5);">Bu sistemde profil bulunamadı.</p>';
        
        modal.style.display = 'flex';
        
        // Profil detaylarını yükle
        this.loadProfileDetails();
    }
    
    async loadProfileDetails() {
        const profileCards = document.querySelectorAll('.profile-part-card[data-profile-code]');
        
        // API URL'ini belirle
        const apiUrl = window.location.hostname === 'localhost' 
            ? 'http://localhost:8001' 
            : 'https://beymetal-backend.onrender.com';
        
        for (const card of profileCards) {
            const profileCode = card.getAttribute('data-profile-code');
            const detailsDiv = card.querySelector('.profile-part-details');
            
            if (!detailsDiv) continue;
            
            try {
                // LR-3101-1 -> lr3101-1 (sadece ilk tire kaldır, küçük harf)
                let searchCode = profileCode.toLowerCase();
                if (searchCode.startsWith('lr-') || searchCode.startsWith('gl-')) {
                    searchCode = searchCode.substring(0, 2) + searchCode.substring(3);
                }
                const response = await fetch(`${apiUrl}/api/catalog/search?q=${encodeURIComponent(searchCode)}`);
                const data = await response.json();
                
                if (data.results && data.results.length > 0) {
                    const profile = data.results[0];
                    
                    let detailsHTML = '<div class="profile-details-list">';
                    
                    // Kategori (en üstte) - categories array'den al
                    if (profile.categories && profile.categories.length > 0) {
                        detailsHTML += `<div class="profile-detail-item"><strong>📁 ${profile.categories.join(', ')}</strong></div>`;
                    }
                    
                    // Müşteri
                    if (profile.customer) {
                        detailsHTML += `<div class="profile-detail-item">👤 Müşteri: ${profile.customer}</div>`;
                    }
                    
                    // Kalıp durumu
                    if (profile.mold_status) {
                        const moldIcon = profile.mold_status === 'Var' || profile.mold_status.includes('Mevcut') ? '✅' : '❌';
                        detailsHTML += `<div class="profile-detail-item">${moldIcon} Kalıp: ${profile.mold_status}</div>`;
                    }
                    
                    // Ölçüler
                    if (profile.dimensions) {
                        const dims = [];
                        if (profile.dimensions.A) dims.push(`A=${profile.dimensions.A}mm`);
                        if (profile.dimensions.B) dims.push(`B=${profile.dimensions.B}mm`);
                        if (profile.dimensions.K) dims.push(`K=${profile.dimensions.K}mm`);
                        
                        if (dims.length > 0) {
                            detailsHTML += `<div class="profile-detail-item">📏 ${dims.join(', ')}</div>`;
                        }
                    }
                    
                    detailsHTML += '</div>';
                    detailsDiv.innerHTML = detailsHTML;
                } else {
                    detailsDiv.innerHTML = '<div class="profile-detail-item">🔗 Sistem Profili</div>';
                }
            } catch (error) {
                console.error(`Error loading details for ${profileCode}:`, error);
                detailsDiv.innerHTML = '<div class="profile-detail-item">🔗 Sistem Profili</div>';
            }
        }
    }
    
    renderProfileConnection(profile) {
        const parts = [];
        
        if (profile.inner_profile) {
            parts.push({
                label: 'İç Profil',
                code: profile.inner_profile
            });
        }
        
        if (profile.middle_profile) {
            parts.push({
                label: 'Orta Profil',
                code: profile.middle_profile
            });
        }
        
        if (profile.outer_profile) {
            parts.push({
                label: 'Dış Profil',
                code: profile.outer_profile
            });
        }
        
        // Eğer hiç part yoksa (tek profil), connection_code'u göster
        const isSingleProfile = parts.length === 0;
        
        // API URL'ini belirle
        const apiUrl = window.location.hostname === 'localhost' 
            ? 'http://localhost:8001' 
            : 'https://beymetal-backend.onrender.com';
        
        return `
            <div class="profile-connection-item">
                <div class="profile-connection-header">
                    <div class="profile-connection-code">${profile.connection_code}</div>
                    <div class="profile-connection-name">${profile.name}</div>
                </div>
                ${isSingleProfile ? `
                    <div class="profile-parts-grid">
                        <div class="profile-part-card" data-profile-code="${profile.connection_code}">
                            <div class="profile-part-image">
                                <img src="${apiUrl}/api/profile-image/${profile.connection_code}" 
                                     alt="${profile.connection_code}"
                                     onerror="this.style.display='none'">
                            </div>
                            <div class="profile-part-info">
                                <div class="profile-part-label">Profil</div>
                                <div class="profile-part-code">${profile.connection_code}</div>
                                <div class="profile-part-details">Yükleniyor...</div>
                            </div>
                        </div>
                    </div>
                ` : `
                    <div class="profile-parts-grid">
                        ${parts.map(part => `
                            <div class="profile-part-card" data-profile-code="${part.code}">
                                <div class="profile-part-image">
                                    <img src="${apiUrl}/api/profile-image/${part.code}" 
                                         alt="${part.code}"
                                         onerror="this.style.display='none'">
                                </div>
                                <div class="profile-part-info">
                                    <div class="profile-part-label">${part.label}</div>
                                    <div class="profile-part-code">${part.code}</div>
                                    <div class="profile-part-details">Yükleniyor...</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `}
            </div>
        `;
    }
    
    renderProfile(profile) {
        // Birleşen profiller
        const parts = [];
        if (profile.inner_profile) parts.push(profile.inner_profile);
        if (profile.middle_profile) parts.push(profile.middle_profile);
        if (profile.outer_profile) parts.push(profile.outer_profile);
        
        return `
            <div class="profile-item">
                <span class="profile-code">${profile.connection_code}</span>
                <span class="profile-name">${profile.name}</span>
                ${parts.length > 0 ? `
                    <div class="profile-details">
                        <div class="profile-detail">
                            <span class="profile-detail-label">Birleşim:</span>
                            <span class="profile-detail-value">${parts.join(' + ')}</span>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }
    

    
    showError(message) {
        if (this.content) {
            this.content.innerHTML = `<div class="loading" style="color: #ff6b6b;">${message}</div>`;
        }
    }
}

// Initialize sidebar when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.connectionSidebar = new ConnectionSidebar();
        initModal();
    });
} else {
    window.connectionSidebar = new ConnectionSidebar();
    initModal();
}

// Modal close handlers
function initModal() {
    const modal = document.getElementById('systemModal');
    const modalClose = document.getElementById('modalClose');
    const modalOverlay = document.getElementById('modalOverlay');
    
    if (modalClose) {
        modalClose.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    if (modalOverlay) {
        modalOverlay.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    // ESC key to close
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'flex') {
            modal.style.display = 'none';
        }
    });
}


// ============================================
// SIMILARITY SEARCH MODULE
// ============================================

function initSimilaritySearch() {
    const similarityBtn = document.getElementById('similarityBtn');
    const similarityModal = document.getElementById('similarityModal');
    const similarityClose = document.getElementById('similarityClose');
    const similarityOverlay = document.getElementById('similarityOverlay');
    const similarityInput = document.getElementById('similarityInput');
    const similarityCount = document.getElementById('similarityCount');
    const similaritySearchBtn = document.getElementById('similaritySearchBtn');
    const similarityResults = document.getElementById('similarityResults');
    
    // Open modal
    if (similarityBtn) {
        similarityBtn.addEventListener('click', () => {
            similarityModal.style.display = 'flex';
            similarityInput.focus();
        });
    }
    
    // Close modal
    function closeSimilarityModal() {
        similarityModal.style.display = 'none';
    }
    
    if (similarityClose) {
        similarityClose.addEventListener('click', closeSimilarityModal);
    }
    
    if (similarityOverlay) {
        similarityOverlay.addEventListener('click', closeSimilarityModal);
    }
    
    // ESC key to close
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && similarityModal.style.display === 'flex') {
            closeSimilarityModal();
        }
    });
    
    // Search on button click
    if (similaritySearchBtn) {
        similaritySearchBtn.addEventListener('click', performSimilaritySearch);
    }
    
    // Search on Enter key
    if (similarityInput) {
        similarityInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                performSimilaritySearch();
            }
        });
    }
    
    async function performSimilaritySearch() {
        const profileCode = similarityInput.value.trim().toUpperCase();
        const count = parseInt(similarityCount.value) || 30;
        
        if (!profileCode) {
            alert('Lütfen bir profil kodu girin!');
            similarityInput.focus();
            return;
        }
        
        console.log('🔍 Benzerlik araması başlatılıyor:', profileCode, 'count:', count);
        
        // Show loading
        similarityResults.innerHTML = `
            <div class="similarity-loading">
                <div class="similarity-loading-spinner"></div>
                <p>Benzer profiller aranıyor...</p>
            </div>
        `;
        
        try {
            const url = `${API_BASE_URL}/api/similarity/${profileCode}?top_k=${count}`;
            console.log('📡 API URL:', url);
            
            const response = await fetch(url);
            console.log('📥 Response status:', response.status);
            
            const data = await response.json();
            console.log('📊 API Response:', data);
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            displaySimilarityResults(data.results || [], profileCode);
            
        } catch (error) {
            console.error('❌ Similarity search error:', error);
            similarityResults.innerHTML = `
                <div class="similarity-placeholder">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="8" x2="12" y2="12"></line>
                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                    </svg>
                    <p style="color: #ef4444;">Hata: ${error.message || 'Benzer profiller bulunamadı'}</p>
                    <p style="color: #9ca3af; font-size: 14px;">Backend: ${API_BASE_URL}</p>
                </div>
            `;
        }
    }
    
    function displaySimilarityResults(results, searchCode) {
        if (!results || results.length === 0) {
            similarityResults.innerHTML = `
                <div class="similarity-placeholder">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <circle cx="11" cy="11" r="8"></circle>
                        <path d="m21 21-4.35-4.35"></path>
                    </svg>
                    <p>Benzer profil bulunamadı</p>
                </div>
            `;
            return;
        }
        
        // Aranan profil görseli
        const queryImageUrl = getProfileImageUrl(searchCode);
        
        let html = `
            <!-- Aranan Profil -->
            <div class="similarity-query-card">
                <h3>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"></circle>
                        <path d="m21 21-4.35-4.35"></path>
                    </svg>
                    Aranan Profil: ${searchCode}
                </h3>
                <div class="similarity-query-content">
                    <div class="similarity-query-image">
                        <img src="${queryImageUrl}" 
                             alt="${searchCode}"
                             onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22200%22%3E%3Crect fill=%22%23f0f0f0%22 width=%22200%22 height=%22200%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-family=%22sans-serif%22 font-size=%2216%22 fill=%22%23999%22%3EGörsel Yok%3C/text%3E%3C/svg%3E'">
                    </div>
                    <div class="similarity-query-info">
                        <p>
                            📊 ${results.length} Benzer Profil Bulundu
                        </p>
                        <p>
                            Benzerlik skorlarına göre sıralanmıştır. Karta tıklayarak detayları görebilirsiniz.
                        </p>
                    </div>
                </div>
            </div>
            
            <!-- Benzer Profiller -->
            <h4 style="margin: 0 0 16px 0; color: #1e3c72; font-size: 18px; font-weight: 700;">
                🎯 Benzer Profiller
            </h4>
            <div class="similarity-results-grid">
        `;
        
        results.forEach(result => {
            const imageUrl = getProfileImageUrl(result.profile_code);
            const scorePercent = Math.round(result.similarity_score * 100);
            
            let scoreBadgeClass = 'similarity-low';
            let scoreBgColor = 'linear-gradient(135deg, #f87171 0%, #ef4444 100%)';
            
            if (result.similarity_score >= 0.8) {
                scoreBadgeClass = 'similarity-high';
                scoreBgColor = 'linear-gradient(135deg, #4ade80 0%, #22c55e 100%)';
            } else if (result.similarity_score >= 0.6) {
                scoreBadgeClass = 'similarity-medium';
                scoreBgColor = 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)';
            }
            
            html += `
                <div class="similarity-result-card" onclick="searchProfile('${result.profile_code}')">
                    <div class="similarity-result-score" style="background: ${scoreBgColor};">
                        %${scorePercent}
                    </div>
                    <img src="${imageUrl}" 
                         alt="${result.profile_code}"
                         onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22200%22%3E%3Crect fill=%22%23f0f0f0%22 width=%22200%22 height=%22200%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-family=%22sans-serif%22 font-size=%2216%22 fill=%22%23999%22%3EGörsel Yok%3C/text%3E%3C/svg%3E'">
                    <div class="similarity-result-info">
                        <h3>${result.profile_code}</h3>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        similarityResults.innerHTML = html;
    }
}

// Helper function to search a profile (reuse existing chat functionality)
function searchProfile(profileCode) {
    // Close similarity modal
    document.getElementById('similarityModal').style.display = 'none';
    
    // Open chat and search
    const chatWidget = document.getElementById('chatWidget');
    const chatMinimized = document.getElementById('chatMinimized');
    const chatExpanded = document.getElementById('chatExpanded');
    const chatInput = document.getElementById('chatInput');
    
    chatMinimized.style.display = 'none';
    chatExpanded.style.display = 'flex';
    chatWidget.classList.add('expanded');
    
    chatInput.value = profileCode;
    document.getElementById('sendBtn').click();
}

// ============================================
// CONNECTION SYSTEMS MODAL (Mobile/Tablet)
// ============================================

function initSystemsModal() {
    const systemsBtn = document.getElementById('systemsBtn');
    const systemsModal = document.getElementById('systemsModal');
    const systemsClose = document.getElementById('systemsClose');
    const systemsOverlay = document.getElementById('systemsOverlay');
    const systemsModalContent = document.getElementById('systemsModalContent');
    const sidebarContent = document.getElementById('sidebarContent');
    
    if (!systemsBtn || !systemsModal) return;
    
    // Open modal
    systemsBtn.addEventListener('click', () => {
        // Copy sidebar content to modal
        systemsModalContent.innerHTML = sidebarContent.innerHTML;
        systemsModal.style.display = 'flex';
        
        // Re-attach click events to system items in modal
        systemsModalContent.querySelectorAll('.system-item').forEach(item => {
            item.addEventListener('click', () => {
                const systemName = item.getAttribute('data-system-name');
                if (window.connectionSidebar) {
                    window.connectionSidebar.openSystemModal(systemName);
                    // Close systems modal after opening system detail
                    systemsModal.style.display = 'none';
                }
            });
        });
    });
    
    // Close modal
    const closeModal = () => {
        systemsModal.style.display = 'none';
    };
    
    systemsClose.addEventListener('click', closeModal);
    systemsOverlay.addEventListener('click', closeModal);
    
    // Close on ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && systemsModal.style.display === 'flex') {
            closeModal();
        }
    });
}

// Initialize on page load
initSimilaritySearch();
initSystemsModal();
