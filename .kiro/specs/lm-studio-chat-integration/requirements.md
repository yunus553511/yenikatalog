# Gereksinimler Dokümanı

## Giriş

Bu özellik, Beymetal Alüminyum profil kataloğu için akıllı bir sohbet asistanı sistemidir. Sistem, Google Drive'dan standart profil verilerini otomatik olarak indirecek, bu verileri embedding teknolojisi ile vektörleştirecek ve kullanıcıların LM Studio üzerinden yerel GPT modeli ile doğal dilde profil bilgilerini sorgulamasına olanak tanıyacaktır.

## Sözlük

- **Chat_Widget**: Web uygulamasının sol alt köşesinde konumlandırılan, animasyonlu sohbet arayüzü bileşeni
- **LM_Studio**: Kullanıcının bilgisayarında çalışan yerel GPT model sunucusu
- **Embedding_System**: Excel verilerini vektör formatına dönüştüren ve benzerlik araması yapan sistem
- **Vector_Database**: Embedding'lerin saklandığı ve sorgulandığı veritabanı (ChromaDB veya FAISS)
- **RAG_Pipeline**: Retrieval-Augmented Generation - Soru sorulduğunda ilgili verileri bulup GPT'ye context olarak gönderen sistem
- **Standart_Excel**: Google Drive'da bulunan, 6 kategori ve 92 satır profil verisi içeren Excel dosyası
- **Profil_Kategorileri**: STANDART BORU, STANDART KUTU, STANDART T, STANDART U, STANDART LAMA, STANDART KÖŞEBENT

## Gereksinimler

### Gereksinim 1

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, web uygulaması açıldığında standart profil verilerinin otomatik olarak güncellenmesini istiyorum, böylece her zaman en güncel bilgilere erişebilirim.

#### Kabul Kriterleri

1. WHEN Web_Uygulaması başlatıldığında, THE Embedding_System SHALL Google Drive'dan Standart_Excel dosyasını indirecek
2. WHILE Standart_Excel indirme işlemi devam ederken, THE Web_Uygulaması SHALL kullanıcıya yükleme durumu gösterecek
3. IF Standart_Excel indirme işlemi başarısız olursa, THEN THE Embedding_System SHALL son indirilen yerel kopyayı kullanacak
4. WHEN Standart_Excel başarıyla indirildikten sonra, THE Embedding_System SHALL dosya içeriğini parse edecek ve 6 Profil_Kategorisini tanımlayacak
5. THE Embedding_System SHALL her profil kaydını (profil kodu, kategori, ölçüler) text formatına dönüştürecek

### Gereksinim 2

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, profil verilerinin hızlı ve doğru bir şekilde aranabilmesini istiyorum, böylece GPT modeli sorularıma ilgili bilgilerle cevap verebilir.

#### Kabul Kriterleri

1. WHEN Standart_Excel verileri text formatına dönüştürüldüğünde, THE Embedding_System SHALL her kaydı embedding modeli ile vektörleştirecek
2. THE Embedding_System SHALL vektörleştirilmiş verileri Vector_Database içinde saklayacak
3. WHEN kullanıcı bir soru sorduğunda, THE RAG_Pipeline SHALL soruyu embedding'e çevirecek
4. THE RAG_Pipeline SHALL Vector_Database içinde en benzer 5 profil kaydını bulacak
5. THE RAG_Pipeline SHALL bulunan kayıtları context olarak formatlanmış text haline getirecek

### Gereksinim 3

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, web sitesinde modern ve kullanıcı dostu bir sohbet arayüzü görmek istiyorum, böylece profil bilgilerini kolayca sorgulayabilirim.

#### Kabul Kriterleri

1. THE Chat_Widget SHALL web uygulamasının sol alt köşesinde konumlandırılacak
2. THE Chat_Widget SHALL mavi tonları ve geometrik desenler içeren modern bir tasarıma sahip olacak
3. WHEN kullanıcı Chat_Widget'a tıkladığında, THE Chat_Widget SHALL yumuşak animasyonla açılacak ve genişleyecek
4. WHILE Chat_Widget açıkken, THE Chat_Widget SHALL mesaj geçmişini, input alanını ve gönder butonunu gösterecek
5. WHEN kullanıcı Chat_Widget'ı kapatmak istediğinde, THE Chat_Widget SHALL animasyonla küçülerek minimize olacak

### Gereksinim 4

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, sorularımı doğal dilde sorup anlamlı cevaplar almak istiyorum, böylece profil katalogunda aradığım bilgilere hızlıca ulaşabilirim.

#### Kabul Kriterleri

1. WHEN kullanıcı Chat_Widget'a bir mesaj yazdığında, THE Chat_Widget SHALL mesajı RAG_Pipeline'a gönderecek
2. THE RAG_Pipeline SHALL ilgili profil kayıtlarını bulup LM_Studio API'sine context ile birlikte gönderecek
3. THE LM_Studio SHALL kullanıcının sorusunu ve context'i kullanarak Türkçe cevap üretecek
4. WHEN LM_Studio cevap ürettiğinde, THE Chat_Widget SHALL cevabı mesaj geçmişine ekleyecek ve gösterecek
5. IF LM_Studio'ya bağlantı kurulamazsa, THEN THE Chat_Widget SHALL kullanıcıya hata mesajı gösterecek

### Gereksinim 5

**Kullanıcı Hikayesi:** Bir kullanıcı olarak, sohbet geçmişimin saklanmasını ve önceki konuşmalara dönebilmeyi istiyorum, böylece daha önce sorduğum soruları tekrar görebilirim.

#### Kabul Kriterleri

1. THE Chat_Widget SHALL her sohbet oturumunu tarayıcı local storage'da saklayacak
2. WHEN kullanıcı web uygulamasını yeniden açtığında, THE Chat_Widget SHALL önceki sohbet geçmişini yükleyecek
3. THE Chat_Widget SHALL kullanıcıya sohbet geçmişini temizleme seçeneği sunacak
4. WHEN kullanıcı sohbet geçmişini temizlediğinde, THE Chat_Widget SHALL tüm mesajları local storage'dan silecek
5. THE Chat_Widget SHALL maksimum 100 mesaj geçmişi saklayacak ve eski mesajları otomatik silecek

### Gereksinim 6

**Kullanıcı Hikayesi:** Bir sistem yöneticisi olarak, embedding ve LM Studio bağlantı ayarlarını yapılandırabilmek istiyorum, böylece sistemi farklı ortamlarda çalıştırabilirim.

#### Kabul Kriterleri

1. THE Embedding_System SHALL LM_Studio API endpoint'ini (örn: http://localhost:1234) yapılandırma dosyasından okuyacak
2. THE Embedding_System SHALL embedding model adını yapılandırma dosyasından okuyacak
3. THE Embedding_System SHALL Vector_Database tipini (ChromaDB veya FAISS) yapılandırma dosyasından okuyacak
4. THE Embedding_System SHALL Google Drive dosya ID'sini yapılandırma dosyasından okuyacak
5. IF yapılandırma dosyası bulunamazsa, THEN THE Embedding_System SHALL varsayılan ayarları kullanacak
