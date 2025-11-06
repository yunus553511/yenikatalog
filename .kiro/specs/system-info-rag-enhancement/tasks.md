# Implementation Plan

- [x] 1. RAG Service'e profil kodu normalizasyon fonksiyonu ekle


  - `_normalize_profile_code()` metodunu implement et
  - LR/GL profilleri için regex pattern kullan (LR3101-1 → LR-3101)
  - Farklı yazım şekillerini destekle (LR-3101-1, LR 3101-1)
  - Büyük/küçük harf duyarsız çalış
  - _Requirements: 4.2_



- [ ] 2. RAG Service'e sistem bilgisi alma fonksiyonu ekle
  - `_get_system_info_for_profile()` metodunu implement et
  - Profil kodunu normalize et
  - Connection service'ten profil birleşim bilgisini al
  - Sistem adını extract et ve döndür


  - Hata durumunda None döndür ve logla
  - _Requirements: 1.1, 1.3, 6.3_

- [ ] 3. format_direct_answer() metodunu güncelle - Tek profil sonucu
  - Tek profil bulunduğunda sistem bilgisini al


  - Sistem bilgisini cevabın üst kısmına ekle ("• Sistem: LR 3100 SİSTEMİ")
  - Sistem bilgisi bulunamazsa sadece logla, diğer bilgileri göstermeye devam et
  - Markdown formatında düzenli göster
  - _Requirements: 1.1, 1.2, 1.4, 2.1, 2.2, 2.3, 2.4_



- [ ] 4. format_direct_answer() metodunu güncelle - Çoklu profil sonuçları
  - Birden fazla profil bulunduğunda her profil için sistem bilgisini al
  - Her profil için sistem bilgisini göster


  - Performans için hata durumlarını handle et
  - _Requirements: 1.1, 1.5, 2.5, 5.2_

- [x] 5. _is_connection_query() metodunu güncelle


  - "hangi sistemde" anahtar kelimesini ekle
  - "sisteminde", "sistemdeki" kelimelerini kontrol et
  - Sistem bazlı sorguları tespit et
  - _Requirements: 3.1, 3.5_



- [ ] 6. _get_connection_context() metodunu güncelle
  - Sistem bazlı sorgular için sistem profillerini döndür
  - Profil bazlı sorgular için sistem bilgisini ekle
  - _format_connection_context() metodunda sistem bilgisini vurgula
  - _Requirements: 3.2, 3.3, 3.4_

- [ ] 7. Hata yönetimi ve logging ekle
  - Sistem bilgisi bulunamadığında warning logla
  - Connection service erişim hatalarını handle et
  - Profil kodu normalizasyon hatalarını handle et
  - Kullanıcıya hata gösterme, sadece logla
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 8. Performance optimizasyonu
  - In-memory cache kullanımını doğrula
  - Gereksiz API çağrılarından kaçın
  - Lazy loading uygula (sadece gerektiğinde sistem bilgisi al)
  - _Requirements: 5.1, 5.2, 5.3_



- [ ]* 9. Unit testleri yaz
  - test_normalize_profile_code() - farklı formatları test et
  - test_get_system_info_for_profile() - LR profili için sistem bilgisi
  - test_system_info_not_found() - geçersiz kod için None dönmeli
  - test_format_direct_answer_with_system() - cevap sistem bilgisini içermeli
  - test_multiple_profiles_with_systems() - çoklu profil için sistem bilgileri


  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ]* 10. Integration testleri yaz
  - test_single_profile_query() - "LR3101-1 nedir?" sorgusu
  - test_system_based_search() - "LR 3100 sistemindeki profiller" sorgusu
  - test_category_search_with_systems() - "KASA kategorisi" sorgusu
  - test_profile_without_system() - sistem bilgisi olmayan profil
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 11. Manuel test senaryolarını çalıştır
  - Tek profil sorgusu: "LR3101-1 nedir?"
  - Sistem bazlı arama: "LR 3100 sistemindeki profiller nelerdir?"
  - Kategori araması: "KASA kategorisindeki profiller"
  - Farklı profil kodu formatları: "LR-3101-1", "LR 3101-1"
  - Sistem bilgisi olmayan profil: "AP0001"
  - _Requirements: Tüm requirements_

- [ ] 12. Documentation ve cleanup
  - Kod yorumları ekle (docstring'ler)
  - README'ye yeni özelliği ekle
  - Kullanım örnekleri ekle
  - Gereksiz log mesajlarını temizle
  - _Requirements: Tüm requirements_
