# Uygulama Planı

- [x] 1. Backend proje yapısını ve temel konfigürasyonu oluştur



  - Python sanal ortamı oluştur ve gerekli paketleri yükle (FastAPI, chromadb, sentence-transformers, openpyxl, httpx)
  - FastAPI uygulaması için main.py ve config.py dosyalarını oluştur
  - Environment variables için .env.example dosyası oluştur (LM_STUDIO_URL, GOOGLE_DRIVE_FILE_ID)
  - _Gereksinimler: 6.1, 6.2, 6.3, 6.4_

- [x] 2. Excel parsing ve profil veri modeli oluştur



  - Profile Pydantic modelini oluştur (code, category, dimensions, text_representation)
  - Excel parser utility'sini yaz (6 kategori için kolon mapping'leri)
  - Her profil için text formatına dönüştürme fonksiyonunu implement et
  - Parse edilen verileri validate et (boş değerleri filtrele)
  - _Gereksinimler: 1.4, 1.5_

- [ ]* 2.1 Excel parser için unit testler yaz
  - Her kategori için doğru parse edildiğini test et
  - Boş değerlerin filtrelendiğini test et
  - _Gereksinimler: 1.4_

- [x] 3. Google Drive entegrasyonu ve Excel indirme servisi oluştur



  - Google Drive'dan dosya indirme fonksiyonunu yaz
  - İndirilen dosyayı yerel cache'e kaydetme logic'i ekle
  - Hata durumunda cached version kullanma mekanizması implement et
  - Startup sırasında otomatik indirme tetikle
  - _Gereksinimler: 1.1, 1.2, 1.3_

- [x] 4. Embedding servisi ve ChromaDB entegrasyonu oluştur



  - sentence-transformers modelini yükle (paraphrase-multilingual-MiniLM-L12-v2)
  - ChromaDB collection'ını initialize et
  - Profil verilerini embedding'e çevirme fonksiyonunu yaz
  - Embedding'leri ChromaDB'ye batch insert et
  - _Gereksinimler: 2.1, 2.2_

- [ ]* 4.1 Embedding servisi için unit testler yaz
  - Model yükleme testleri
  - Embedding oluşturma testleri
  - _Gereksinimler: 2.1_

- [x] 5. RAG pipeline ve benzerlik araması implement et



  - Kullanıcı sorusunu embedding'e çevirme fonksiyonunu yaz
  - ChromaDB'de cosine similarity ile top-5 arama yap
  - Bulunan profilleri context formatına dönüştür
  - Context template'ini oluştur (system prompt + profiller + soru)
  - _Gereksinimler: 2.3, 2.4, 2.5_

- [ ] 6. LM Studio client ve API entegrasyonu oluştur
  - LMStudioClient class'ını yaz (OpenAI-compatible API)
  - Chat completion endpoint'ini implement et
  - Retry logic ve timeout mekanizması ekle
  - Connection health check fonksiyonu yaz
  - _Gereksinimler: 4.2, 4.3, 4.5_

- [x] 7. FastAPI endpoints oluştur



  - POST /api/chat endpoint'ini implement et (RAG + LM Studio)
  - GET /api/health endpoint'ini implement et
  - POST /api/refresh-data endpoint'ini implement et
  - CORS middleware ekle
  - Rate limiting middleware ekle
  - _Gereksinimler: 4.1, 4.4_

- [ ]* 7.1 API endpoints için integration testler yaz
  - Chat endpoint test et
  - Health endpoint test et
  - _Gereksinimler: 4.1_

- [ ] 8. Frontend proje yapısını oluştur (React + TypeScript)
  - React projesi oluştur (Vite veya Create React App)
  - TypeScript konfigürasyonu yap
  - Klasör yapısını oluştur (components, services, hooks, types)
  - Chat types interface'lerini tanımla (ChatMessage, ChatResponse, ProfileContext)
  - _Gereksinimler: 3.1_

- [ ] 9. Chat Widget temel bileşenlerini oluştur
  - ChatWidget.tsx ana container'ını oluştur (fixed position, sol alt)
  - ChatHeader.tsx başlık ve minimize butonunu oluştur
  - MessageList.tsx mesaj geçmişi listesini oluştur
  - MessageBubble.tsx tek mesaj bileşenini oluştur (user/assistant ayrımı)
  - ChatInput.tsx input alanı ve gönder butonunu oluştur
  - _Gereksinimler: 3.1, 3.4_

- [ ] 10. Chat Widget animasyonları ve stil oluştur
  - CSS dosyasını oluştur (Beymetal mavi tonları)
  - Açılma/kapanma animasyonları ekle (scale + fade, 300ms)
  - Mesaj gelişi animasyonları ekle (slide-up + fade, 200ms)
  - Typing indicator pulse animasyonu ekle
  - Responsive tasarım için media queries ekle
  - _Gereksinimler: 3.2, 3.3, 3.5_

- [ ] 11. Chat state management ve API client oluştur
  - useChat custom hook'unu yaz (mesaj gönderme, state yönetimi)
  - chatApi.ts API client'ını yaz (fetch ile backend'e istek)
  - Loading ve error state'lerini yönet
  - Typing indicator logic'ini implement et
  - _Gereksinimler: 4.1, 4.4_

- [ ] 12. LocalStorage ile sohbet geçmişi yönetimi ekle
  - useLocalStorage custom hook'unu yaz
  - Sohbet geçmişini kaydetme fonksiyonunu implement et
  - Uygulama açılışında geçmişi yükleme logic'i ekle
  - Geçmişi temizleme fonksiyonunu ekle
  - Maksimum 100 mesaj limiti uygula
  - _Gereksinimler: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 13. Hata yönetimi ve kullanıcı bildirimleri ekle
  - Frontend'de API hata mesajlarını göster
  - Retry butonu ekle (bağlantı hatası durumunda)
  - Timeout mekanizması ekle (30 saniye)
  - Backend'de try-catch blokları ve error logging ekle
  - LM Studio bağlantı hatası için özel mesaj göster
  - _Gereksinimler: 4.5_

- [ ] 14. Sistem entegrasyonu ve end-to-end akış testi
  - Backend'i başlat ve Excel indirme + embedding sürecini test et
  - LM Studio'nun çalıştığını doğrula
  - Frontend'i başlat ve chat widget'ı test et
  - Örnek sorular sor ve cevapları doğrula (örn: "AP0002 nedir?")
  - Sohbet geçmişi kaydetme/yükleme test et
  - _Gereksinimler: 1.1, 2.1, 4.1, 5.1_

- [ ]* 14.1 E2E testler yaz
  - Kullanıcı sorusu → cevap akışını test et
  - Chat geçmişi kaydetme/yükleme test et
  - _Gereksinimler: 4.1_

- [ ] 15. Performans optimizasyonları ve son rötuşlar
  - React.memo ile gereksiz render'ları önle
  - Debouncing ekle (typing indicator için 300ms)
  - Backend'de embedding cache mekanizması ekle
  - Frontend'de lazy loading uygula (chat widget)
  - Animasyonları 60fps'de çalıştığını doğrula
  - _Gereksinimler: 3.3_

- [ ] 16. Dokümantasyon ve deployment hazırlığı
  - README.md dosyası oluştur (kurulum, kullanım, konfigürasyon)
  - LM Studio kurulum ve model yükleme talimatları ekle
  - Environment variables dokümantasyonu yaz
  - Örnek .env dosyası oluştur
  - Troubleshooting bölümü ekle
  - _Gereksinimler: 6.1, 6.2, 6.3, 6.4_
