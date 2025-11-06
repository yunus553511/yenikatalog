# Requirements Document

## Introduction

Bu özellik, alüminyum profillerin birleşim sistemlerini görselleştirmek ve kullanıcıların hangi profillerin hangi fitillerle birleştiğini kolayca bulmasını sağlamak için geliştirilecektir. Sistem, Google Sheets'ten profil birleşim verilerini çekecek, arayüzde sol panelde görselleştirecek ve chat botuna RAG (Retrieval-Augmented Generation) ile entegre edecektir.

## Glossary

- **System**: Alüminyum profil birleşim sistemi (örn: LR-3100 SİSTEM)
- **Profile**: Alüminyum profil (örn: LR-3101, LR-3102)
- **Connection_Code**: Profil birleşim kodu - hangi profillerin birbirine bağlanabileceğini gösteren kod
- **Gasket**: Fitil/bariyer - profiller arasında kullanılan conta (örn: P200000, P148000)
- **Connection_Service**: Google Sheets'ten birleşim verilerini çeken ve yöneten servis
- **Sidebar**: Arayüzün sol tarafındaki panel - birleşim sistemlerini gösterir
- **RAG_Service**: Chat botunun birleşim bilgilerini kullanarak akıllı cevaplar vermesini sağlayan servis

## Requirements

### Requirement 1: Birleşim Verilerini Yükleme

**User Story:** Sistem yöneticisi olarak, profil birleşim verilerinin otomatik olarak Google Sheets'ten yüklenmesini istiyorum, böylece veriler her zaman güncel olur.

#### Acceptance Criteria

1. WHEN sistem başlatıldığında, THE Connection_Service SHALL Google Sheets'ten birleşim verilerini indirir
2. THE Connection_Service SHALL indirilen Excel dosyasını backend/data/cache klasörüne kaydeder
3. THE Connection_Service SHALL Excel verilerini parse ederek sistem, profil, birleşim kodu ve fitil bilgilerini extract eder
4. IF Excel indirme başarısız olursa, THEN THE Connection_Service SHALL cache'lenmiş veriyi kullanır
5. THE Connection_Service SHALL her 24 saatte bir otomatik olarak verileri günceller

### Requirement 2: Birleşim Verilerini API ile Sunma

**User Story:** Frontend geliştirici olarak, birleşim verilerine REST API üzerinden erişebilmek istiyorum, böylece arayüzde dinamik olarak gösterebilirim.

#### Acceptance Criteria

1. THE System SHALL `/api/connections/systems` endpoint'i ile tüm sistemleri listeler
2. THE System SHALL `/api/connections/system/{system_name}` endpoint'i ile belirli bir sistemin detaylarını döndürür
3. THE System SHALL `/api/connections/profile/{profile_code}` endpoint'i ile belirli bir profilin birleşim bilgilerini döndürür
4. THE System SHALL `/api/connections/search?query={query}` endpoint'i ile birleşim araması yapar
5. WHEN API çağrısı yapıldığında, THE System SHALL JSON formatında veri döndürür

### Requirement 3: Sidebar'da Birleşim Sistemlerini Görselleştirme

**User Story:** Son kullanıcı olarak, arayüzün sol tarafında profil birleşim sistemlerini görmek istiyorum, böylece hangi profillerin birbirine bağlanabileceğini kolayca anlayabilirim.

#### Acceptance Criteria

1. THE Sidebar SHALL arayüzün sol tarafında accordion/collapsible yapıda sistemleri gösterir
2. WHEN kullanıcı bir sisteme tıkladığında, THE Sidebar SHALL o sistemdeki profilleri ve birleşim kodlarını gösterir
3. THE Sidebar SHALL her profil için birleşim kodunu, fitil bilgilerini ve ağırlık bilgilerini gösterir
4. THE Sidebar SHALL responsive tasarıma sahip olur (mobilde gizlenebilir/açılabilir)
5. THE Sidebar SHALL arama özelliği ile sistemler ve profiller arasında filtreleme yapar

### Requirement 4: Chat Botuna RAG Entegrasyonu

**User Story:** Son kullanıcı olarak, chat botuna "LR-3101 hangi fitil ile birleşir?" gibi sorular sorabilmek istiyorum, böylece hızlıca bilgi alabilirim.

#### Acceptance Criteria

1. WHEN kullanıcı birleşim ile ilgili soru sorduğunda, THE RAG_Service SHALL birleşim verilerini context'e ekler
2. THE RAG_Service SHALL "hangi fitil", "birleşim kodu", "hangi profil ile birleşir" gibi anahtar kelimeleri tespit eder
3. THE RAG_Service SHALL ilgili profil ve birleşim bilgilerini LLM'e context olarak gönderir
4. THE System SHALL kullanıcıya profil birleşim bilgilerini, fitil kodlarını ve ağırlık bilgilerini içeren cevap verir
5. THE System SHALL birleşim bilgilerini markdown formatında düzenli bir şekilde gösterir

### Requirement 5: Veri Önbellekleme ve Performans

**User Story:** Sistem yöneticisi olarak, birleşim verilerinin önbelleklenmesini istiyorum, böylece sistem hızlı çalışır ve Google Sheets API limitlerini aşmaz.

#### Acceptance Criteria

1. THE Connection_Service SHALL indirilen Excel dosyasını local cache'e kaydeder
2. THE Connection_Service SHALL cache'lenmiş veriyi memory'de tutar (in-memory cache)
3. WHEN API çağrısı yapıldığında, THE System SHALL önce memory cache'i kontrol eder
4. IF cache geçerliyse, THEN THE System SHALL cache'ten veri döndürür
5. THE System SHALL cache'i 24 saatte bir otomatik olarak yeniler

### Requirement 6: Hata Yönetimi ve Logging

**User Story:** Sistem yöneticisi olarak, birleşim verisi yükleme hatalarını görmek istiyorum, böylece sorunları hızlıca çözebilirim.

#### Acceptance Criteria

1. IF Google Sheets indirme başarısız olursa, THEN THE System SHALL hata mesajını loglar ve cache'lenmiş veriyi kullanır
2. IF Excel parse hatası oluşursa, THEN THE System SHALL detaylı hata mesajı loglar
3. THE System SHALL her veri yükleme işlemini timestamp ile loglar
4. THE System SHALL API hatalarını kullanıcıya anlaşılır mesajlarla bildirir
5. THE System SHALL kritik hataları console'a ve log dosyasına yazar
