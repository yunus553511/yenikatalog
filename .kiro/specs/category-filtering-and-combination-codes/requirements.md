# Requirements Document

## Introduction

Bu özellik, katalog arama sistemindeki üç kritik sorunu çözmektedir:
1. Birleşim kodları (örn. LR-3101) sorgulandığında, hangi profillerin birleşiminden oluştuğunu açıkça belirtmemesi
2. Genel kategori isimleri (örn. "kutu") sorgulandığında, yanlış kategorilerden (Dairesel Kutu, Köşebent vs.) sonuç göstermesi
3. Standart kategorilerde (Köşebent, Lama vs.) yakın değer aramasının çalışmaması

## Glossary

- **RAG Service**: Kullanıcı sorgularını işleyen ve ilgili profilleri getiren Retrieval-Augmented Generation servisi
- **Birleşim Kodu**: Birden fazla profilin bir araya gelerek oluşturduğu sistem kodu (örn. LR-3101)
- **Bileşen Profil**: Birleşim kodunu oluşturan tekil profiller (örn. LR-3101-1, LR-3101-2)
- **Kategori Filtresi**: Kullanıcının belirttiği kategoriye göre sonuçları filtreleme mekanizması
- **Standart Kategori**: Standart Kutu, Köşebent, Lama gibi temel profil kategorileri
- **Yakın Değer Araması**: Kullanıcının belirttiği boyuta yakın profilleri bulma özelliği (örn. "30 köşebent" → 30x30, 30x20 köşebentler)
- **Catalog Service**: Profil verilerini yöneten ve sorgulayan servis

## Requirements

### Requirement 1

**User Story:** Kullanıcı olarak, bir birleşim kodu (örn. LR-3101) sorguladığımda, bu kodun hangi profillerin birleşiminden oluştuğunu açıkça görmek istiyorum, böylece hangi profilleri kullanmam gerektiğini anlayabilirim.

#### Acceptance Criteria

1. WHEN kullanıcı bir birleşim kodu sorgular (örn. "LR3101 nedir"), THE RAG Service SHALL birleşim kodunu tespit etmeli
2. WHEN birleşim kodu tespit edilir, THE RAG Service SHALL bu kodu oluşturan bileşen profilleri (örn. LR-3101-1, LR-3101-2) belirlemeli
3. WHEN bileşen profiller belirlenir, THE RAG Service SHALL yanıtta "LR-3101, LR-3101-1 ve LR-3101-2 profillerinin birleşimidir" şeklinde açık bir açıklama içermeli
4. WHEN birleşim kodu birden fazla sistemde kullanılıyorsa, THE RAG Service SHALL tüm kullanım yerlerini listelemeli

### Requirement 2

**User Story:** Kullanıcı olarak, "kutu" gibi genel bir kategori adı sorguladığımda, sadece "Standart Kutu" kategorisinden sonuçlar görmek istiyorum, böylece Dairesel Kutu veya Köşebent gibi ilgisiz kategorilerden sonuç görmem.

#### Acceptance Criteria

1. WHEN kullanıcı "kutu" kelimesini sorgular, THE RAG Service SHALL sadece "Standart Kutu" kategorisini hedeflemeli
2. WHEN kategori filtresi uygulanır, THE RAG Service SHALL "Dairesel Kutu", "Köşebent", "Lama" gibi diğer kategorileri hariç tutmalı
3. WHEN kategori eşleştirmesi yapılır, THE RAG Service SHALL tam kategori adı eşleştirmesi yerine akıllı kategori eşleştirmesi kullanmalı
4. THE RAG Service SHALL kullanıcının sorgu dilini (Türkçe) ve doğal ifadelerini (kutu, köşebent vs.) doğru kategori adlarına (Standart Kutu, Köşebent vs.) dönüştürmeli

### Requirement 3

**User Story:** Kullanıcı olarak, "30 köşebent" gibi boyut içeren sorgular yaptığımda, 30x30, 30x20 gibi yakın boyutlardaki köşebentleri görmek istiyorum, böylece ihtiyacıma uygun profilleri bulabilirim.

#### Acceptance Criteria

1. WHEN kullanıcı bir standart kategoride (Köşebent, Lama vs.) boyut belirtir, THE RAG Service SHALL yakın değer araması yapmalı
2. WHEN yakın değer araması yapılır, THE RAG Service SHALL belirtilen boyutu içeren tüm profilleri bulmalı (örn. "30" → 30x30, 30x20, 30x40)
3. WHEN boyut araması yapılır, THE RAG Service SHALL kategori filtresini de uygulamalı (örn. "30 köşebent" → sadece Köşebent kategorisinden)
4. THE RAG Service SHALL yakın değer aramasını tüm standart kategorilerde (Standart Kutu, Köşebent, Lama, Boru vs.) desteklemeli

### Requirement 4

**User Story:** Kullanıcı olarak, kategori filtrelerinin tutarlı çalışmasını istiyorum, böylece hangi kategori adını kullansam doğru sonuçları alabilirim.

#### Acceptance Criteria

1. THE RAG Service SHALL kategori adlarını normalize etmeli (büyük/küçük harf, Türkçe karakter farklılıkları)
2. WHEN kullanıcı "kutu", "köşebent", "lama" gibi kısa adlar kullanır, THE RAG Service SHALL bunları tam kategori adlarına (Standart Kutu, Köşebent, Lama) dönüştürmeli
3. THE RAG Service SHALL kategori eşleştirmesinde öncelik sırası kullanmalı (tam eşleşme > kısmi eşleşme > genel arama)
4. WHEN birden fazla kategori eşleşmesi mümkünse, THE RAG Service SHALL en spesifik kategoriyi seçmeli

### Requirement 5

**User Story:** Geliştirici olarak, kategori filtreleme ve boyut arama mantığının tüm standart kategorilerde tutarlı çalışmasını istiyorum, böylece kod tekrarını önleyebilirim.

#### Acceptance Criteria

1. THE RAG Service SHALL kategori filtreleme mantığını merkezi bir fonksiyonda toplamalı
2. THE RAG Service SHALL boyut arama mantığını tüm standart kategoriler için genel bir fonksiyonda uygulamalı
3. WHEN yeni bir standart kategori eklendiğinde, THE RAG Service SHALL mevcut filtreleme ve arama mantığını otomatik olarak desteklemeli
4. THE RAG Service SHALL her kategori için özel kurallar yerine genel kurallar kullanmalı
