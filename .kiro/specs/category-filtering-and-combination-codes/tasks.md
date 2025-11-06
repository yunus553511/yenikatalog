# Implementation Plan

- [ ] 1. Kategori eşleştirme mantığını iyileştir
  - [ ] 1.1 Kategori mapping dictionary'si oluştur
    - CATEGORY_MAPPING dictionary'si ekle (kutu → Standart Kutu, lama → Lama, köşebent → Köşebent)
    - Tüm standart, şekilsel ve özel kategoriler için mapping tanımla
    - Türkçe karakter varyasyonlarını destekle (köşebent, kosebent)
    - _Requirements: 2.4, 4.2_
  
  - [ ] 1.2 `_map_keyword_to_category()` metodunu implement et
    - Kullanıcı kelimelerini tam kategori adlarına dönüştür
    - CATEGORY_MAPPING kullanarak eşleştirme yap
    - Türkçe karakter normalizasyonu uygula
    - None döndür eğer mapping bulunamazsa
    - _Requirements: 2.4, 4.2_
  
  - [ ] 1.3 `_extract_all_categories()` metodunu iyileştir
    - Akıllı kategori eşleştirmesi ekle (tam eşleşme > keyword mapping > kısmi eşleşme)
    - Tek kelime sorguları için özel mantık ("kutu" → sadece "Standart Kutu")
    - Öncelik sırası uygula: tam eşleşme önce, sonra keyword mapping, en son kısmi eşleşme
    - Yanlış kategorileri filtrele (örn: "kutu" sorgusu "Köşebent" döndürmemeli)
    - _Requirements: 2.1, 2.2, 2.3, 4.1, 4.3, 4.4_

- [ ] 2. Ölçü ve kategori extraction mantığını ekle
  - [ ] 2.1 `_extract_dimension_and_category()` metodunu implement et
    - Sorgudan hem ölçü hem kategori bilgisini extract et
    - Pattern 1: "30 köşebent", "6 lama" formatını destekle
    - Pattern 2: "30x30 kutu", "100 a 100 lama" formatını destekle
    - `_map_keyword_to_category()` kullanarak kategori adını normalize et
    - (dimension, category) tuple döndür
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ] 2.2 `_profile_contains_dimension()` metodunu implement et
    - Profilin belirli bir ölçüyü içerip içermediğini kontrol et
    - Profil kodu ve açıklamasında regex ile ara
    - Pattern 1: "30x30", "30x20" formatı
    - Pattern 2: "30mm", "30 mm" formatı
    - Pattern 3: Sadece sayı "30"
    - Boolean döndür
    - _Requirements: 3.1, 3.2_

- [ ] 3. Kategoride ölçü araması fonksiyonunu implement et
  - [ ] 3.1 `_search_by_dimension_in_category()` metodunu implement et
    - Belirli bir kategoride ölçü araması yap
    - catalog_service.get_profiles_by_category() ile profilleri al
    - `_profile_contains_dimension()` ile filtrele
    - Sonuçları formatla ve döndür
    - Bulunamazsa yakın değer önerisi göster
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  
  - [ ] 3.2 `_suggest_nearby_search()` metodunu implement et
    - Yakın değer araması önerisi oluştur
    - "30 köşebent bulunamadı. ±3 aralığında aramak ister misiniz?" formatı
    - Kategori adını ve ölçüyü mesaja dahil et
    - _Requirements: 3.1, 3.3_
  
  - [ ] 3.3 `_format_dimension_search_results()` metodunu implement et
    - Ölçü araması sonuçlarını formatla
    - Profil görselleri ekle
    - Kategori, müşteri, açıklama bilgilerini göster
    - Yakın değer önerisi ekle (footer)
    - _Requirements: 3.1, 3.2, 3.3_

- [ ] 4. `format_direct_answer()` metodunu güncelle
  - [ ] 4.1 Ölçü ve kategori extraction entegrasyonu
    - `_extract_dimension_and_category()` çağrısı ekle
    - Eğer hem ölçü hem kategori varsa, `_search_by_dimension_in_category()` kullan
    - Mevcut yakın değer araması mantığını koru (fallback)
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  
  - [ ] 4.2 Kategori filtresi kontrolü ekle
    - Standart kategorilerde yakın değer önerisi göster
    - Şekilsel kategorilerde gösterme
    - CATEGORY_MAPPING kullanarak kategori tipini belirle
    - _Requirements: 3.4, 5.1, 5.2_

- [ ] 5. Birleşim kodu açıklamasını iyileştir





  - [x] 5.1 `_search_by_connection_code()` metodunu güncelle


    - Profil varyantları bulunduğunda açık açıklama ekle
    - Format: "LR-3101, LR-3101-1 ve LR-3101-2 profillerinin birleşimidir"
    - Variant kodlarını listele (join ile)
    - Sistem adını ve birleşim kodunu vurgula
    - _Requirements: 1.1, 1.2, 1.3, 1.4_


  
  - [ ] 5.2 Birleşim kodu mesaj formatını güncelle
    - Başlık: "**{connection_code}** bir birleşim kodudur."
    - Açıklama: "**{connection_code}**, {variant1} ve {variant2} profillerinin birleşimidir."
    - Sistem bilgisi: "**Sistem:** {system_name}"
    - Profil detayları (görseller, kategoriler)
    - _Requirements: 1.1, 1.2, 1.3_

- [ ] 6. Tüm standart kategorilerde yakın değer aramasını destekle
  - [ ] 6.1 `_search_nearby_dimensions()` metodunu güncelle
    - Kategori parametresi ekle
    - Sadece belirtilen kategoride ara
    - `_extract_dimension_and_category()` ile kategori belirle
    - Tüm standart kategorilerde çalışmasını sağla (Köşebent, Lama, Boru vs.)
    - _Requirements: 3.3, 3.4, 5.1, 5.2, 5.3, 5.4_
  
  - [ ] 6.2 Kategori filtresi mantığını genelleştir
    - Hardcoded "kutu" kontrolünü kaldır
    - CATEGORY_MAPPING kullanarak dinamik kontrol yap
    - Tüm standart kategoriler için yakın değer önerisi göster
    - _Requirements: 3.4, 5.1, 5.2, 5.3, 5.4_

- [ ]* 7. Test coverage ekle
  - [ ]* 7.1 Unit testler yaz
    - `_map_keyword_to_category()` için testler
    - `_extract_dimension_and_category()` için testler
    - `_profile_contains_dimension()` için testler
    - Kategori eşleştirme testleri
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 4.1, 4.2_
  
  - [ ]* 7.2 Integration testler yaz
    - "kutu" sorgusu → sadece Standart Kutu
    - "30 köşebent" sorgusu → 30x30, 30x20 köşebentler
    - "LR3101 nedir" sorgusu → birleşim açıklaması
    - Yakın değer önerisi testleri
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 3.3_

- [ ] 8. Manuel test ve doğrulama
  - [ ] 8.1 Kritik sorguları test et
    - "kutu" → Sadece Standart Kutu kategorisi
    - "30 köşebent" → 30x30, 30x20 köşebentler + yakın değer önerisi
    - "6 lama" → 6mm lamalar
    - "LR3101 nedir" → "LR-3101, LR-3101-1 ve LR-3101-2'nin birleşimidir"
    - "100 kutu" → 100x100, 100x50 kutular
    - Log çıktılarını kontrol et
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 3.3_
