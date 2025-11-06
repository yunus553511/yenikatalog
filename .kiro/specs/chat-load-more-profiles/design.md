# Design Document

## Overview

Chat widget'ında çok sayıda profil gösterildiğinde kullanıcı deneyimini iyileştirmek için "Daha Fazla Göster" özelliği tasarımı. Backend'den gelen tüm profil verileri frontend'de saklanacak ve kullanıcı butona her tıkladığında 15 profil daha gösterilecek.

## Architecture

### Current Flow
1. Kullanıcı mesaj gönderir
2. Backend LLM'den yanıt alır (tool calls ile profil arama)
3. Backend markdown formatında yanıt döner (profil görselleri `![code](url)` formatında)
4. Frontend `formatMessage()` ile markdown'ı HTML'e çevirir
5. Tüm profiller bir kerede gösterilir

### New Flow
1. Kullanıcı mesaj gönderir
2. Backend LLM'den yanıt alır
3. **Backend yanıta profil verilerini ekler** (yeni field: `profile_data`)
4. Frontend yanıtı parse eder ve profil sayısını kontrol eder
5. **15'ten fazla profil varsa:**
   - İlk 15 profili göster
   - "Daha Fazla Göster" butonu ekle
   - Kalan profil verilerini message state'inde sakla
6. **Kullanıcı butona tıkladığında:**
   - Saklanan verilerden sonraki 15 profili render et
   - Buton metnini güncelle (kalan profil sayısı)
   - Tüm profiller gösterildiyse butonu gizle

## Components and Interfaces

### 1. Backend Changes (main.py)

#### API Response Format
```python
{
    "message": "Markdown formatted response with images",
    "conversation_history": [...],
    "profile_data": [  # YENİ FIELD
        {
            "code": "AP0001",
            "image_url": "http://localhost:8001/api/profile-image/AP0001",
            "category": "STANDART KUTU",
            "dimensions": {"A": 30, "B": 30},
            "thickness": 2,
            "mold_status": "Var",
            "customer": "Müşteri Adı"
        },
        ...
    ]
}
```

#### Implementation
- `_execute_search_profiles()` fonksiyonunda profil verilerini topla
- LLM response'a `profile_data` field'ı ekle
- Markdown response'da profil görsellerini `![code](url)` formatında tut

### 2. Frontend Changes (script.js)

#### Message State Management
```javascript
// Her mesaj için state objesi
const messageStates = new Map(); // messageId -> state

// State structure
{
    messageId: "msg_123",
    profileData: [...],      // Tüm profil verileri
    displayedCount: 15,      // Şu ana kadar gösterilen profil sayısı
    totalCount: 45,          // Toplam profil sayısı
    batchSize: 15            // Her yüklemede gösterilecek sayı
}
```

#### New Functions

**1. `addMessage()` - Güncelleme**
```javascript
function addMessage(content, role = 'user', profileData = null) {
    const messageId = `msg_${Date.now()}_${Math.random()}`;
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.setAttribute('data-message-id', messageId);
    
    // Format message content
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    if (profileData && profileData.length > 15) {
        // Çok fazla profil var, load more butonu ekle
        const { formattedContent, displayedProfiles } = formatMessageWithLoadMore(
            content, 
            profileData, 
            15
        );
        messageContent.innerHTML = formattedContent;
        
        // State'i sakla
        messageStates.set(messageId, {
            messageId,
            profileData,
            displayedCount: displayedProfiles,
            totalCount: profileData.length,
            batchSize: 15
        });
        
        // Load more butonu ekle
        const loadMoreBtn = createLoadMoreButton(messageId);
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(loadMoreBtn);
    } else {
        // Normal mesaj veya az sayıda profil
        messageContent.innerHTML = formatMessage(content);
        messageDiv.appendChild(messageContent);
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
```

**2. `formatMessageWithLoadMore()` - Yeni**
```javascript
function formatMessageWithLoadMore(text, profileData, initialCount) {
    // İlk N profili göster
    const profilesToShow = profileData.slice(0, initialCount);
    
    // Markdown'daki profil görsellerini parse et
    // Sadece ilk N tanesini göster
    let profileIndex = 0;
    const formattedText = text.replace(
        /!\[(.*?)\]\((.*?)\)/g, 
        (match, alt, url) => {
            if (profileIndex < initialCount) {
                profileIndex++;
                return `<img src="${url}" alt="${alt}" class="chat-profile-image" onclick="showImageModal('${url}', '${alt}')" />`;
            }
            return ''; // Geri kalanları gösterme
        }
    );
    
    return {
        formattedContent: formattedText,
        displayedProfiles: profileIndex
    };
}
```

**3. `createLoadMoreButton()` - Yeni**
```javascript
function createLoadMoreButton(messageId) {
    const state = messageStates.get(messageId);
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
```

**4. `loadMoreProfiles()` - Yeni**
```javascript
function loadMoreProfiles(messageId) {
    const state = messageStates.get(messageId);
    if (!state) return;
    
    const button = document.querySelector(`button[data-message-id="${messageId}"]`);
    const messageDiv = document.querySelector(`div[data-message-id="${messageId}"]`);
    const messageContent = messageDiv.querySelector('.message-content');
    
    // Loading state
    button.disabled = true;
    button.innerHTML = `
        <div class="typing-indicator" style="display: inline-flex;">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    
    // Simulate loading (instant in reality, but smooth UX)
    setTimeout(() => {
        // Sonraki batch'i al
        const nextBatch = state.profileData.slice(
            state.displayedCount,
            state.displayedCount + state.batchSize
        );
        
        // Profilleri render et ve ekle
        nextBatch.forEach(profile => {
            const img = document.createElement('img');
            img.src = profile.image_url;
            img.alt = profile.code;
            img.className = 'chat-profile-image';
            img.onclick = () => showImageModal(profile.image_url, profile.code);
            messageContent.appendChild(img);
        });
        
        // State'i güncelle
        state.displayedCount += nextBatch.length;
        messageStates.set(messageId, state);
        
        // Buton durumunu güncelle
        const remaining = state.totalCount - state.displayedCount;
        if (remaining > 0) {
            // Hala profil var, butonu güncelle
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
        } else {
            // Tüm profiller gösterildi, butonu kaldır
            button.remove();
        }
        
        // Scroll to new content
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 300);
}
```

**5. `sendMessage()` - Güncelleme**
```javascript
async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;
    
    // Add user message
    addMessage(message, 'user');
    chatInput.value = '';
    
    showTypingIndicator();
    
    try {
        const response = await getAPIResponse(message);
        removeTypingIndicator();
        
        // Backend'den profile_data geliyorsa kullan
        const profileData = response.profile_data || null;
        addMessage(response.message, 'assistant', profileData);
        
    } catch (error) {
        removeTypingIndicator();
        addMessage('Üzgünüm, sunucuya bağlanılamadı.', 'assistant');
    }
}
```

### 3. CSS Styling (style.css)

```css
/* Load More Button */
.load-more-button {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    width: 100%;
    margin-top: 12px;
    padding: 12px 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    border-radius: 8px;
    color: white;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
}

.load-more-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.load-more-button:active {
    transform: translateY(0);
}

.load-more-button:disabled {
    opacity: 0.7;
    cursor: not-allowed;
    transform: none;
}

.load-more-icon {
    animation: bounce 2s infinite;
}

@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-4px); }
}

.load-more-text {
    font-weight: 600;
}

.load-more-count {
    opacity: 0.8;
    font-size: 12px;
}
```

## Data Models

### Profile Data Structure
```typescript
interface ProfileData {
    code: string;              // Profil kodu (AP0001)
    image_url: string;         // Görsel URL'i
    category?: string;         // Kategori
    dimensions?: {             // Ölçüler
        A?: number;
        B?: number;
        K?: number;
    };
    thickness?: number;        // Kalınlık
    mold_status?: string;      // Kalıp durumu
    customer?: string;         // Müşteri
    system?: string;           // Sistem bilgisi
}

interface MessageState {
    messageId: string;         // Unique message ID
    profileData: ProfileData[]; // Tüm profil verileri
    displayedCount: number;    // Gösterilen profil sayısı
    totalCount: number;        // Toplam profil sayısı
    batchSize: number;         // Batch boyutu (15)
}
```

## Error Handling

### Frontend Errors
1. **State bulunamadı**: Butona tıklandığında state yoksa butonu gizle
2. **Profil verisi eksik**: profileData null/undefined ise normal mesaj göster
3. **Render hatası**: Try-catch ile yakala, console'a log, kullanıcıya bilgi verme

### Backend Errors
1. **Profil verisi toplanamadı**: Boş array dön, normal markdown response gönder
2. **Tool execution hatası**: Mevcut error handling devam etsin

## Testing Strategy

### Unit Tests (Frontend)
1. `formatMessageWithLoadMore()` - İlk N profili doğru parse ediyor mu?
2. `createLoadMoreButton()` - Buton metni doğru mu?
3. `loadMoreProfiles()` - State doğru güncelleniyor mu?
4. Message state management - Map doğru çalışıyor mu?

### Integration Tests
1. Backend'den profile_data geliyor mu?
2. 15'ten az profil olduğunda buton gösterilmiyor mu?
3. Tüm profiller gösterildikten sonra buton kaldırılıyor mu?
4. Yeni mesaj geldiğinde önceki state temizleniyor mu?

### Manual Tests
1. 5 profil - Buton gösterilmemeli
2. 20 profil - İlk 15 gösterilmeli, buton "Son 5 Profili Göster" demeli
3. 50 profil - İlk 15, sonra +15, sonra +15, sonra "Son 5"
4. Buton tıklama - Smooth loading animation
5. Scroll behavior - Yeni profiller yüklenince scroll aşağı kaymalı

## Performance Considerations

1. **Memory**: Her mesaj için state saklanıyor, eski mesajları temizle (son 10 mesaj)
2. **DOM**: Profilleri batch batch ekle, tek seferde 50 profil render etme
3. **Image Loading**: Lazy loading için `loading="lazy"` attribute ekle
4. **Smooth UX**: 300ms loading animation, kullanıcı hemen görsün

## Migration Plan

1. **Phase 1**: Backend'e `profile_data` field ekle (opsiyonel, geriye uyumlu)
2. **Phase 2**: Frontend'e load more logic ekle (profile_data yoksa normal davran)
3. **Phase 3**: CSS styling ekle
4. **Phase 4**: Test ve deploy

## Alternative Approaches Considered

### 1. Pagination (Reddedildi)
- Backend'den sayfa sayfa veri çek
- **Neden reddedildi**: Ekstra API çağrısı, daha yavaş, backend değişikliği fazla

### 2. Infinite Scroll (Reddedildi)
- Scroll'da otomatik yükle
- **Neden reddedildi**: Chat widget'ında scroll karmaşık, buton daha açık

### 3. "Tümünü Göster" Butonu (Reddedildi)
- Tek buton, tüm profilleri bir kerede göster
- **Neden reddedildi**: 100+ profil olduğunda performans sorunu

## Future Enhancements

1. **Virtualization**: 100+ profil için virtual scrolling
2. **Filter**: Profilleri kategori/kalınlık'a göre filtrele
3. **Sort**: Profilleri sırala (kod, kategori, vb.)
4. **Export**: Profilleri Excel/PDF olarak indir
