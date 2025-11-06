# Implementation Plan

- [x] 1. Backend: Profile data extraction ve API response update

  - [x] 1.1 `_execute_search_profiles()` fonksiyonunu güncelle


    - Tool execution sonucunda profil verilerini array olarak topla
    - Her profil için: code, image_url, category, dimensions, thickness, mold_status, customer, system
    - Return value'ya profile_data ekle
    - _Requirements: 3.1, 3.2_


  
  - [ ] 1.2 `main.py` chat endpoint'ini güncelle
    - Tool execution sonucundan profile_data'yı al

    - API response'a `profile_data` field'ı ekle


    - Geriye uyumlu olmalı (profile_data opsiyonel)
    - _Requirements: 3.1, 3.3_



- [ ] 2. Frontend: Message state management sistemi
  - [ ] 2.1 Global state yapısını oluştur
    - `messageStates` Map objesi ekle (messageId -> state)
    - State structure: messageId, profileData, displayedCount, totalCount, batchSize

    - _Requirements: 3.3, 3.4_


  
  - [ ] 2.2 `addMessage()` fonksiyonunu güncelle
    - profileData parametresi ekle (opsiyonel)
    - Unique messageId oluştur (timestamp + random)

    - messageDiv'e data-message-id attribute ekle
    - profileData varsa ve 15'ten fazlaysa load more logic çalıştır
    - _Requirements: 1.1, 2.1, 3.4_

- [ ] 3. Frontend: Load more functionality
  - [ ] 3.1 `formatMessageWithLoadMore()` fonksiyonunu yaz
    - Markdown'daki profil görsellerini parse et

    - İlk N profili göster, geri kalanını sakla
    - formattedContent ve displayedProfiles return et
    - _Requirements: 1.1, 3.2_
  
  - [ ] 3.2 `createLoadMoreButton()` fonksiyonunu yaz
    - Buton elementi oluştur
    - Kalan profil sayısını hesapla
    - Buton metnini dinamik oluştur ("15 Profil Daha" veya "Son 8 Profili Göster")

    - SVG icon ve count badge ekle


    - onclick handler bağla
    - _Requirements: 1.4, 1.5_
  
  - [x] 3.3 `loadMoreProfiles()` fonksiyonunu yaz

    - messageId ile state'i al
    - Loading animation göster (buton disabled)
    - Sonraki batch'i profileData'dan al


    - Profilleri DOM'a ekle (img elementleri)


    - State'i güncelle (displayedCount)
    - Buton metnini güncelle veya kaldır
    - Smooth scroll to bottom
    - _Requirements: 1.2, 1.3, 1.4, 1.5_


- [ ] 4. Frontend: API integration
  - [ ] 4.1 `sendMessage()` fonksiyonunu güncelle
    - API response'dan profile_data field'ını al
    - addMessage() çağrısına profileData parametresi ekle
    - Geriye uyumlu (profile_data yoksa null)
    - _Requirements: 2.1, 3.1_
  
  - [ ] 4.2 `getAPIResponse()` return type'ını kontrol et
    - response.profile_data field'ını handle et
    - Error handling ekle (profile_data undefined/null)
    - _Requirements: 3.1_

- [ ] 5. CSS: Load more button styling
  - [ ] 5.1 `.load-more-button` stillerini ekle
    - Gradient background (purple theme)
    - Flexbox layout (icon + text + count)
    - Hover effects (transform, shadow)
    - Disabled state styling
    - _Requirements: 1.4_
  
  - [ ] 5.2 Loading animation ekle
    - Bounce animation for icon
    - Typing indicator for loading state
    - Smooth transitions
    - _Requirements: 1.5_

- [ ] 6. Testing ve bug fixes
  - [ ] 6.1 Edge case testleri
    - 15'ten az profil (buton gösterilmemeli)
    - Tam 15 profil (buton gösterilmemeli)
    - 16-30 profil (bir kez load more)
    - 50+ profil (multiple load more)
    - _Requirements: 1.1, 1.3_
  
  - [ ] 6.2 State management testleri
    - Yeni mesaj geldiğinde önceki state korunuyor mu?
    - Multiple messages ile state karışıyor mu?
    - Memory leak var mı? (eski state'ler temizleniyor mu?)
    - _Requirements: 2.2, 3.4_
  
  - [ ] 6.3 UX testleri
    - Scroll behavior smooth mu?
    - Loading animation çalışıyor mu?
    - Buton metni doğru mu?
    - Görseller doğru yükleniyor mu?
    - _Requirements: 1.4, 1.5_

- [ ] 7. Deployment ve monitoring
  - [ ] 7.1 Backend deploy
    - Config değişikliği yok
    - API response format değişti (geriye uyumlu)
    - Test et: localhost ve Render
    - _Requirements: 3.1_
  
  - [ ] 7.2 Frontend deploy
    - script.js ve style.css güncellemeleri
    - Browser cache clear gerekebilir
    - Test et: localhost:3000 ve production
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
