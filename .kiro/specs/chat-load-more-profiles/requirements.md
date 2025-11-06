# Requirements Document

## Introduction

Chat widget'ında çok sayıda profil bulunduğunda kullanıcı deneyimini iyileştirmek için "Daha Fazla Göster" özelliği. Şu anda chat 15'ten fazla profil bulduğunda sadece ilk 15'i gösterip "+ X tane daha var" mesajı veriyor. Bu özellik ile kullanıcı bir butona tıklayarak her seferinde 15 profil daha yükleyebilecek.

## Glossary

- **Chat Widget**: Kullanıcıların profil arama yapabildiği sohbet arayüzü
- **Profile Card**: Profil bilgilerini (kod, görsel, kategori, kalıp durumu) gösteren kart bileşeni
- **Load More Button**: Daha fazla profil yüklemek için kullanılan buton
- **Batch Size**: Her yüklemede gösterilecek profil sayısı (15)

## Requirements

### Requirement 1

**User Story:** Kullanıcı olarak, chat'te çok sayıda profil bulunduğunda tüm profilleri görebilmek için "Daha Fazla Göster" butonuna tıklayabilmek istiyorum, böylece sayfa kaydırarak tüm sonuçları inceleyebilirim.

#### Acceptance Criteria

1. WHEN chat response 15'ten fazla profil içerdiğinde, THE Chat Widget SHALL ilk 15 profili gösterir ve altına "Daha Fazla Göster" butonu ekler
2. WHEN kullanıcı "Daha Fazla Göster" butonuna tıkladığında, THE Chat Widget SHALL bir sonraki 15 profili mevcut profillerin altına ekler
3. WHEN tüm profiller gösterildiğinde, THE Chat Widget SHALL "Daha Fazla Göster" butonunu gizler
4. THE Chat Widget SHALL buton üzerinde kaç profil daha yüklenebileceğini gösterir (örn: "15 Profil Daha Göster" veya "Son 8 Profili Göster")
5. WHEN profiller yüklenirken, THE Chat Widget SHALL butonda loading göstergesi gösterir

### Requirement 2

**User Story:** Kullanıcı olarak, yeni bir arama yaptığımda önceki yükleme durumunun sıfırlanmasını istiyorum, böylece her aramada temiz bir başlangıç yapabilirim.

#### Acceptance Criteria

1. WHEN kullanıcı yeni bir mesaj gönderdiğinde, THE Chat Widget SHALL önceki mesajın yükleme durumunu sıfırlar
2. WHEN yeni chat response geldiğinde, THE Chat Widget SHALL profil sayacını baştan başlatır
3. THE Chat Widget SHALL her mesaj için bağımsız yükleme durumu tutar

### Requirement 3

**User Story:** Geliştirici olarak, backend'den gelen tüm profil verilerini frontend'de saklayabilmek istiyorum, böylece "Daha Fazla Göster" için tekrar API çağrısı yapmama gerek kalmaz.

#### Acceptance Criteria

1. THE Chat Widget SHALL backend'den gelen tüm profil verilerini message data içinde saklar
2. WHEN "Daha Fazla Göster" butonuna tıklandığında, THE Chat Widget SHALL saklanan verilerden bir sonraki batch'i render eder
3. THE Chat Widget SHALL her mesaj için profil verilerini ve gösterim durumunu ayrı ayrı tutar
4. THE Chat Widget SHALL profil verilerini DOM'da değil JavaScript state'inde saklar
