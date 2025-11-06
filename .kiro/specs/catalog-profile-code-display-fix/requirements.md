# Requirements Document

## Introduction

Bu özellik, katalog profillerinin arama sonuçlarında ve chat yanıtlarında profil kodlarının (A sütunu) doğru şekilde görüntülenmesini sağlar. Şu anda standart profillerde profil kodları görünürken, katalog profillerinde görünmüyor. Bu durum, `CatalogProfile` ve `Profile` sınıfları arasındaki alan adı tutarsızlığından kaynaklanmaktadır.

## Glossary

- **System**: Beymetal Alüminyum Profil Kataloğu Chat Sistemi
- **CatalogProfile**: Katalog Excel dosyasından parse edilen profil nesnesi (A sütununda `profile_no` alanı)
- **Profile**: Standart profil nesnesi (`code` alanı kullanır)
- **Text Formatter**: Profil bilgilerini kullanıcıya göstermek için formatlayan utility modülü
- **Chat Response**: Kullanıcıya dönen chat yanıtı mesajı
- **Profile Code**: A sütununda bulunan profil numarası/kodu

## Requirements

### Requirement 1

**User Story:** Kullanıcı olarak, katalog profillerini aradığımda profil kodlarını görmek istiyorum, böylece hangi profil hakkında bilgi aldığımı anlayabilirim.

#### Acceptance Criteria

1. WHEN kullanıcı katalog profillerini aradığında, THE System SHALL chat yanıtında profil kodunu (A sütunu) görüntüler
2. WHEN kullanıcı standart profilleri aradığında, THE System SHALL profil kodunu görüntülemeye devam eder
3. WHEN System profil bilgisini formatladığında, THE System SHALL hem `CatalogProfile` hem de `Profile` nesnelerini destekler
4. THE System SHALL profil kodu alanı için tutarlı bir isimlendirme kullanır

### Requirement 2

**User Story:** Geliştirici olarak, profil nesneleri arasında tutarlı bir veri modeli kullanmak istiyorum, böylece kod karmaşıklığı azalır ve bakım kolaylaşır.

#### Acceptance Criteria

1. THE System SHALL `CatalogProfile` ve `Profile` sınıfları için ortak bir interface tanımlar
2. WHEN profil bilgisi `to_dict()` metoduyla dönüştürüldüğünde, THE System SHALL profil kodu için tutarlı bir alan adı kullanır
3. THE System SHALL text formatter fonksiyonlarında her iki profil tipini destekler
4. THE System SHALL profil kodu alanına erişirken tip kontrolü yapar
