# ALUNA - Render Deployment Guide

## Render'da Deployment Adımları

### 1. Backend Deployment (Web Service)

1. Render Dashboard'a git: https://dashboard.render.com
2. "New +" butonuna tıkla → "Web Service" seç
3. GitHub repository'ni bağla
4. Ayarları yapılandır:
   - **Name**: `aluna-backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free` (veya istediğin plan)

5. Environment Variables ekle:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   EXCEL_URL=your_google_drive_excel_url
   CATALOG_EXCEL_URL=your_catalog_excel_url
   CONNECTION_EXCEL_URL=your_connection_excel_url
   ```

6. "Create Web Service" butonuna tıkla
7. Deploy tamamlanınca backend URL'ini not al (örn: `https://aluna-backend.onrender.com`)

### 2. Frontend Deployment (Static Site)

1. Render Dashboard'da "New +" → "Static Site" seç
2. Aynı repository'yi seç
3. Ayarları yapılandır:
   - **Name**: `aluna-frontend`
   - **Build Command**: (boş bırak)
   - **Publish Directory**: `prototype`

4. `prototype/script.js` dosyasında backend URL'ini güncelle:
   ```javascript
   // Satır 274 civarı
   } else {
       API_URL = 'https://aluna-backend.onrender.com'; // Kendi backend URL'inizi yazın
   }
   ```

5. "Create Static Site" butonuna tıkla

### 3. Google Drive Excel Dosyaları

Excel dosyalarını Google Drive'da paylaşılabilir yap:
1. Google Drive'da Excel dosyasını aç
2. "Paylaş" → "Bağlantıyı alan herkes" → "Görüntüleyici"
3. URL'yi kopyala ve şu formata çevir:
   ```
   https://docs.google.com/spreadsheets/d/DOSYA_ID/export?format=xlsx
   ```

### 4. Test

1. Frontend URL'ini aç (örn: `https://aluna-frontend.onrender.com`)
2. Chat widget'ı aç
3. Bir profil ara (örn: "30x30 kutu")
4. Sonuçların geldiğini kontrol et

## Notlar

- **Free Plan**: Render'ın free planında servis 15 dakika inaktif kalırsa uyur. İlk istek 30-60 saniye sürebilir.
- **Logs**: Render Dashboard'da "Logs" sekmesinden hataları görebilirsin
- **Auto Deploy**: GitHub'a push yaptığında otomatik deploy olur
- **Custom Domain**: Render'da kendi domain'ini bağlayabilirsin

## Sorun Giderme

### Backend başlamıyor
- Logs'u kontrol et
- Environment variables'ların doğru olduğundan emin ol
- `requirements.txt` dosyasının doğru olduğunu kontrol et

### Frontend backend'e bağlanamıyor
- CORS ayarlarını kontrol et (`backend/main.py`)
- Backend URL'inin doğru olduğunu kontrol et
- Browser console'da hataları kontrol et

### Excel dosyaları yüklenmiyor
- Google Drive URL'lerinin doğru formatda olduğunu kontrol et
- Dosyaların "Bağlantıyı alan herkes" ile paylaşıldığını kontrol et
