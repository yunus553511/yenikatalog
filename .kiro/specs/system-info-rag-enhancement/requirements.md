# Requirements Document

## Introduction

Bu özellik, chat botunun profil kodlarını sorgularken hangi sistemde (örn: LR 3100 SİSTEMİ, LR 3200 SİSTEMİ) olduğunu da bilmesini ve kullanıcıya bu bilgiyi sunmasını sağlayacaktır. Şu anda chatbot profil kodu, kategori, müşteri ve kalıp durumu bilgilerini gösteriyor ancak profilin hangi sistemde yer aldığı bilgisi eksik.

## Glossary

- **System**: Alüminyum profil sistemi (örn: LR 3100 SİSTEMİ, LR 3200 SİSTEMİ)
- **Profile_Code**: Profil kodu (örn: LR3101-1, LR3102-1)
- **RAG_Service**: Chat botunun akıllı cevaplar vermesini sağlayan Retrieval-Augmented Generation servisi
- **Connection_Service**: Profil birleşim ve sistem bilgilerini yöneten servis
- **Category**: Profil kategorisi (örn: KASA, KANAT, PERVAZ)
- **Chatbot**: ALUNA - Alüminyum Profil Asistanı

## Requirements

### Requirement 1: Sistem Bilgisini RAG Context'ine Ekleme

**User Story:** Son kullanıcı olarak, chat botuna bir profil kodu sorduğumda hangi sistemde olduğunu da öğrenmek istiyorum, böylece profil hakkında daha kapsamlı bilgi sahibi olurum.

#### Acceptance Criteria

1. WHEN kullanıcı bir profil kodu sorduğunda, THE RAG_Service SHALL Connection_Service'ten o profilin sistem bilgisini alır
2. THE RAG_Service SHALL profil bilgilerine sistem adını ekler
3. THE RAG_Service SHALL sistem bilgisini LLM'e context olarak gönderir
4. THE Chatbot SHALL kullanıcıya profil kodu ile birlikte sistem adını gösterir
5. IF profil birden fazla sistemde kullanılıyorsa, THEN THE Chatbot SHALL tüm sistem isimlerini listeler

### Requirement 2: Sistem Bilgisini Görselleştirme

**User Story:** Son kullanıcı olarak, chat botunun cevabında sistem bilgisinin net ve okunabilir şekilde gösterilmesini istiyorum, böylece bilgiyi kolayca anlayabilirim.

#### Acceptance Criteria

1. THE Chatbot SHALL sistem bilgisini profil bilgilerinin üst kısmında gösterir
2. THE Chatbot SHALL sistem adını vurgulu (bold veya başlık) şekilde gösterir
3. THE Chatbot SHALL sistem bilgisini Türkçe olarak gösterir
4. THE Chatbot SHALL sistem bilgisini markdown formatında düzenli gösterir
5. WHEN birden fazla profil gösterildiğinde, THE Chatbot SHALL her profil için sistem bilgisini ayrı ayrı gösterir

### Requirement 3: Sistem Bazlı Arama Desteği

**User Story:** Son kullanıcı olarak, "LR 3100 sistemindeki profiller nelerdir?" gibi sorular sorabilmek istiyorum, böylece belirli bir sistemdeki tüm profilleri görebilirim.

#### Acceptance Criteria

1. WHEN kullanıcı sistem adı ile soru sorduğunda, THE RAG_Service SHALL sistem adını tespit eder
2. THE RAG_Service SHALL Connection_Service'ten o sistemdeki tüm profilleri alır
3. THE Chatbot SHALL sistemdeki profilleri kategorilere göre gruplandırarak gösterir
4. THE Chatbot SHALL her profil için kategori, müşteri ve kalıp durumu bilgilerini gösterir
5. THE RAG_Service SHALL "LR 3100", "LR-3100", "3100 sistemi" gibi farklı yazım şekillerini tanır

### Requirement 4: Mevcut Profil Verisi ile Entegrasyon

**User Story:** Sistem yöneticisi olarak, mevcut profil veritabanı (Excel) ile birleşim sistemi verilerinin tutarlı olmasını istiyorum, böylece kullanıcılar doğru bilgi alır.

#### Acceptance Criteria

1. THE RAG_Service SHALL hem profil veritabanından hem de Connection_Service'ten veri alır
2. THE RAG_Service SHALL profil kodunu normalize eder (LR3101-1, LR-3101-1, LR 3101-1 aynı kabul edilir)
3. IF profil her iki kaynakta da bulunursa, THEN THE RAG_Service SHALL bilgileri birleştirir
4. IF profil sadece bir kaynakta bulunursa, THEN THE RAG_Service SHALL mevcut bilgiyi gösterir
5. THE RAG_Service SHALL veri tutarsızlıklarını loglar

### Requirement 5: Performans ve Cache Yönetimi

**User Story:** Sistem yöneticisi olarak, sistem bilgisi sorgularının hızlı çalışmasını istiyorum, böylece kullanıcı deneyimi olumsuz etkilenmez.

#### Acceptance Criteria

1. THE RAG_Service SHALL Connection_Service'in in-memory cache'ini kullanır
2. THE RAG_Service SHALL sistem bilgisi sorgularını 500ms içinde tamamlar
3. THE RAG_Service SHALL gereksiz API çağrılarından kaçınır
4. THE RAG_Service SHALL profil-sistem eşleşmelerini cache'ler
5. THE RAG_Service SHALL cache'i Connection_Service ile senkronize tutar

### Requirement 6: Hata Yönetimi

**User Story:** Son kullanıcı olarak, sistem bilgisi bulunamadığında anlaşılır bir mesaj görmek istiyorum, böylece ne olduğunu anlayabilirim.

#### Acceptance Criteria

1. IF sistem bilgisi bulunamazsa, THEN THE Chatbot SHALL "Sistem bilgisi bulunamadı" mesajı gösterir
2. THE Chatbot SHALL diğer profil bilgilerini (kategori, müşteri, kalıp) göstermeye devam eder
3. THE RAG_Service SHALL sistem bilgisi hatalarını loglar
4. THE Chatbot SHALL kullanıcıya alternatif arama önerileri sunar
5. IF Connection_Service erişilemezse, THEN THE RAG_Service SHALL sadece profil veritabanı bilgilerini gösterir
