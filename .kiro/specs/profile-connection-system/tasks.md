# Implementation Plan

- [ ] 1. Backend: Connection Service oluştur
  - [x] 1.1 ConnectionService class'ını oluştur


    - `backend/services/connection_service.py` dosyasını oluştur
    - `__init__`, `initialize`, `load_data` metodlarını implement et
    - Google Sheets URL'ini environment variable'dan oku
    - Cache klasörü yönetimini ekle
    - _Requirements: 1.1, 1.2, 1.3, 5.1, 5.2_



  - [ ] 1.2 Excel parse fonksiyonunu implement et
    - `parse_excel()` metodunu yaz
    - Excel header'larını doğru şekilde parse et (2. satırdan başla)
    - Sistem, profil, birleşim kodu, fitil bilgilerini extract et
    - Ağırlık ve mekanik özellikleri parse et


    - Veriyi yapılandırılmış dictionary'ye dönüştür
    - _Requirements: 1.3, 5.1_

  - [ ] 1.3 Arama ve filtreleme metodlarını implement et
    - `get_all_systems()` - tüm sistemleri döndür
    - `get_system_by_name()` - belirli sistemi döndür

    - `get_profile_connections()` - profil birleşim bilgilerini döndür
    - `search_connections()` - arama fonksiyonu (sistem, profil, fitil kodlarında ara)
    - Türkçe karakter normalizasyonu ekle
    - _Requirements: 2.4, 5.3_

  - [x] 1.4 Cache yönetimini implement et

    - In-memory cache (_data attribute)
    - Cache timestamp yönetimi (_last_update)
    - 24 saatlik cache expiration kontrolü
    - Cache refresh fonksiyonu
    - _Requirements: 1.4, 5.1, 5.2, 5.4, 5.5_

  - [x] 1.5 Hata yönetimi ve logging ekle


    - Custom exception class'ları (ConnectionServiceError, DataLoadError, ParseError)
    - Try-catch blokları ekle
    - Detaylı logging (info, warning, error)



    - Fallback mekanizması (cache'lenmiş veri kullan)
    - _Requirements: 1.4, 6.1, 6.2, 6.3, 6.5_

- [ ] 2. Backend: REST API endpoint'lerini ekle
  - [x] 2.1 Connection service'i main.py'a entegre et

    - `connection_service` global instance oluştur
    - Startup event'inde `initialize()` çağır
    - _Requirements: 2.1_

  - [x] 2.2 API endpoint'lerini implement et

    - `GET /api/connections/systems` - tüm sistemleri listele
    - `GET /api/connections/system/{system_name}` - sistem detayı
    - `GET /api/connections/profile/{profile_code}` - profil birleşim bilgisi
    - `GET /api/connections/search?query={query}` - arama
    - Response formatını standardize et (success, data, error)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_



  - [ ] 2.3 Pydantic model'lerini oluştur
    - `backend/models/connection.py` dosyası oluştur
    - GasketInfo, WeightInfo, MechanicalInfo, ProfileConnection, ConnectionSystem model'lerini tanımla


    - Validation kuralları ekle
    - _Requirements: 2.5_



  - [ ] 2.4 Error handling ve CORS ayarları
    - Endpoint'lerde try-catch blokları
    - HTTP status code'ları (200, 404, 500)
    - CORS middleware ayarları (eğer gerekiyorsa)
    - _Requirements: 6.4_




- [ ] 3. Backend: RAG Service'e birleşim entegrasyonu
  - [x] 3.1 Birleşim sorgusu tespit fonksiyonu

    - `_is_connection_query()` metodunu ekle
    - Anahtar kelime listesi ('fitil', 'birleşim', 'bağlan', 'hangi profil', vb.)
    - Türkçe karakter normalizasyonu ile kontrol
    - _Requirements: 4.2_

  - [x] 3.2 Profil kodu extraction fonksiyonu


    - `_extract_profile_code()` metodunu ekle
    - Regex ile profil kodlarını tespit et (LR-XXXX formatı)
    - _Requirements: 4.2_

  - [x] 3.3 Connection context oluşturma


    - `_get_connection_context()` metodunu ekle
    - Connection service'ten veri çek
    - Context'i markdown formatında formatla
    - Fitil kodları, ağırlık bilgileri, mekanik özellikler ekle
    - _Requirements: 4.1, 4.3_



  - [ ] 3.4 RAG pipeline'ına entegre et
    - `prepare_context()` metodunu güncelle
    - Birleşim sorgusu ise connection context ekle
    - Normal profil araması ile birleştir
    - _Requirements: 4.1, 4.3_


  - [ ] 3.5 Cevap formatlama
    - `format_direct_answer()` metodunu güncelle
    - Birleşim bilgilerini düzenli göster
    - Markdown formatında tablo veya liste kullan
    - _Requirements: 4.4, 4.5_


- [ ] 4. Frontend: Sidebar component'ini oluştur
  - [ ] 4.1 HTML yapısını oluştur
    - `prototype/index.html`'e sidebar section ekle
    - Arama input'u
    - Accordion/collapsible yapı için container

    - Toggle button (mobil için)
    - _Requirements: 3.1, 3.4_

  - [ ] 4.2 CSS styling
    - `prototype/style.css`'e sidebar stilleri ekle
    - Grid layout (sidebar + main content)
    - Accordion animasyonları

    - Responsive tasarım (mobil breakpoint)
    - Sticky positioning
    - _Requirements: 3.1, 3.4_

  - [x] 4.3 JavaScript component'i

    - `prototype/components/sidebar.js` dosyası oluştur (veya script.js'e ekle)
    - ConnectionSidebar class'ı
    - `init()`, `loadSystems()`, `render()` metodları
    - Event listener'lar (toggle, search, accordion)
    - _Requirements: 3.1, 3.2_


  - [ ] 4.4 Sistem listesini render et
    - API'den sistemleri çek
    - Accordion yapısında sistemleri göster
    - Her sistem için profil listesi
    - Profil detayları (birleşim kodu, fitil, ağırlık)
    - _Requirements: 3.2, 3.3_


  - [ ] 4.5 Arama fonksiyonalitesi
    - Search input'a event listener ekle
    - Debounce (300ms)
    - Sistemleri ve profilleri filtrele

    - Sonuçları highlight et
    - _Requirements: 3.5_

  - [ ] 4.6 Responsive ve animasyonlar
    - Mobilde sidebar toggle button

    - Slide-in/slide-out animasyonu
    - Accordion açılma/kapanma animasyonu
    - Loading state göster
    - _Requirements: 3.4_

- [x] 5. Frontend: Chat bot entegrasyonu


  - [ ] 5.1 Chat bot'a birleşim sorgusu desteği ekle
    - Mevcut chat widget'ı güncelle
    - Birleşim cevaplarını düzgün göster
    - Markdown rendering (eğer yoksa)
    - _Requirements: 4.4, 4.5_


  - [ ] 5.2 Örnek sorular ekle
    - Chat widget'ın başlangıç mesajına birleşim örnekleri ekle
    - "LR-3101 hangi fitil ile birleşir?"
    - "Çift ray sürme kasa birleşim kodu nedir?"
    - _Requirements: 4.4_


- [ ] 6. Testing ve validation
  - [ ] 6.1 Backend unit testleri
    - Connection service test dosyası oluştur
    - Excel parse testleri
    - Arama fonksiyonu testleri
    - Cache yönetimi testleri


    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ] 6.2 API endpoint testleri
    - Her endpoint için test case'ler
    - Success ve error senaryoları
    - Response format validation
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ] 6.3 RAG entegrasyon testleri
    - Birleşim sorgusu tespiti testleri
    - Context oluşturma testleri
    - Cevap formatlama testleri
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 6.4 Frontend testleri
    - Sidebar render testleri
    - Arama fonksiyonu testleri
    - Responsive testleri
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 7. Manual testing ve polish
  - [ ] 7.1 End-to-end test senaryoları
    - Sidebar'ı aç/kapa
    - Sistemler arasında gezin
    - Arama yap ve sonuçları kontrol et
    - Chat bot'a birleşim soruları sor
    - Mobil responsive kontrol et
    - _Requirements: Tüm requirements_

  - [ ] 7.2 Performance optimizasyonu
    - API response sürelerini ölç
    - Frontend render performansını kontrol et
    - Cache'in çalıştığını doğrula
    - Memory leak kontrolü
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ] 7.3 UI/UX iyileştirmeleri
    - Loading state'leri ekle
    - Error mesajlarını kullanıcı dostu yap
    - Animasyonları smooth hale getir
    - Accessibility kontrolleri (keyboard navigation, ARIA labels)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ] 7.4 Documentation
    - README'ye yeni özelliği ekle
    - API endpoint'lerini dokümante et
    - Kullanım örnekleri ekle
    - _Requirements: Tüm requirements_
