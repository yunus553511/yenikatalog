# 🚀 Render.com'a İki Ayrı Servis ile Deployment

## ⚠️ ÖNEMLİ: İki Ayrı API Var!
Bu projede **2 ayrı backend servisi** var:
1. **Ana Backend** (Chat, Catalog, vb.) - Port 8004
2. **Benzerlik API** (Similarity Search) - Port 8003

## Deployment Stratejisi
İki seçenek var:

### 🎯 Seçenek 1: İki Ayrı Render Service (Önerilen)
- Ana Backend → Render Web Service
- Benzerlik API → Ayrı Render Web Service
- Frontend → Render Static Site

### 🔧 Seçenek 2: Tek Container (Docker)
- Tüm servisler bir Docker image'da
- Nginx reverse proxy
- Daha karmaşık ama tek URL

---

## 📋 Ön Hazırlık

### 1. GitHub'a Yükle
Projenizi GitHub'a push edin:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/KULLANICI_ADINIZ/beymetal-chat.git
git push -u origin main
```

### 2. Dosya Yapısını Kontrol Et
```
beymetal-chat/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── config.py
│   ├── services/
│   ├── models/
│   └── utils/
├── prototype/
│   ├── index.html
│   ├── style.css
│   └── script.js
└── render.yaml  ← Önemli!
```

---

## 🎯 Deployment Adımları

### Adım 1: Render.com'a Giriş
1. https://render.com adresine git
2. "Get Started" tıkla
3. GitHub ile giriş yap

### Adım 2: Blueprint ile Deploy
1. Dashboard'da **"New +"** tıkla
2. **"Blueprint"** seç
3. GitHub repo'nuzu seç
4. `render.yaml` dosyasını otomatik bulacak
5. **"Apply"** tıkla

**O kadar!** 🎉 Render.com otomatik olarak:
- Backend'i deploy eder
- Frontend'i deploy eder
- URL'leri oluşturur

### Adım 3: URL'leri Güncelle

Deploy tamamlandıktan sonra:

1. **Backend URL'ini kopyala:**
   - Örnek: `https://beymetal-backend.onrender.com`

2. **script.js'i güncelle:**
   ```javascript
   API_URL = 'https://beymetal-backend.onrender.com/api/chat';
   ```

3. **GitHub'a push et:**
   ```bash
   git add prototype/script.js
   git commit -m "Update API URL"
   git push
   ```

4. Render.com otomatik yeniden deploy eder!

---

## 🔧 Seçenek 1: İki Ayrı Render Service (Önerilen)

### 1️⃣ Ana Backend Deploy

1. **"New +"** → **"Web Service"**
2. GitHub repo seç
3. Ayarlar:
   - **Name:** `beymetal-backend`
   - **Runtime:** Python 3
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free

4. **Environment Variables** ekle:
   ```
   PORT=8004
   GOOGLE_DRIVE_FILE_ID=1RcUAmXf7VNqzh7Pv1Zo8zoQ7zuf2_t3FJXkT_tCLixw
   CORS_ORIGINS=*
   SUPABASE_URL=https://your-project.supabase.co
   SIMILARITY_API_URL=https://beymetal-similarity.onrender.com
   ```

5. **Create Web Service** → URL'i kopyala (örn: `https://beymetal-backend.onrender.com`)

### 2️⃣ Benzerlik API Deploy

1. **"New +"** → **"Web Service"**
2. Aynı GitHub repo seç
3. Ayarlar:
   - **Name:** `beymetal-similarity`
   - **Runtime:** Python 3
   - **Root Directory:** `YENİ BENZERLİK`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Plan:** Free (veya Starter $7/ay - daha hızlı)

4. **Environment Variables** ekle:
   ```
   PORT=8003
   IMAGE_DIR=/opt/render/project/src/YENİPNGLER
   ```

5. **Create Web Service** → URL'i kopyala (örn: `https://beymetal-similarity.onrender.com`)

### 3️⃣ Frontend Deploy

1. **"New +"** → **"Static Site"**
2. GitHub repo seç
3. Ayarlar:
   - **Name:** `beymetal-frontend`
   - **Build Command:** (boş bırak)
   - **Publish Directory:** `prototype`

4. **Create Static Site**

### 4️⃣ URL'leri Bağla

Ana backend'in environment variables'ına dön ve güncelle:
```
SIMILARITY_API_URL=https://beymetal-similarity.onrender.com
```

Frontend'in `script.js`'ini güncelle:
```javascript
const API_BASE_URL = 'https://beymetal-backend.onrender.com';
```

GitHub'a push et → Otomatik deploy!

---

## ✅ Test Et

### 1. Backend Test
```bash
curl https://beymetal-backend.onrender.com/api/health
```

Cevap:
```json
{
  "status": "healthy",
  "profiles_count": 225,
  "vector_db_ready": true
}
```

### 2. Frontend Test
Tarayıcıda aç:
```
https://beymetal-frontend.onrender.com
```

Chat widget'a tıkla ve test et:
- "çap 28"
- "30x30 kutu"
- "AP0002"

---

## 🔄 Excel Güncelleme

### Manuel Güncelleme
Backend URL'ine POST isteği:
```bash
curl -X POST https://beymetal-backend.onrender.com/api/refresh-data
```

### Admin Panel Ekle
`prototype/admin.html` oluştur:

```html
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Beymetal Admin</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
        }
        button {
            padding: 15px 30px;
            font-size: 16px;
            background: #4a90e2;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }
        button:hover {
            background: #2e5c8a;
        }
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            background: #f5f5f5;
        }
    </style>
</head>
<body>
    <h1>🔧 Beymetal Admin Panel</h1>
    
    <button onclick="refreshData()">
        📥 Excel Verilerini Yenile
    </button>
    
    <div id="status" class="status"></div>

    <script>
        const BACKEND_URL = 'https://beymetal-backend.onrender.com';
        
        async function refreshData() {
            const statusDiv = document.getElementById('status');
            statusDiv.innerHTML = '⏳ Yenileniyor...';
            
            try {
                const response = await fetch(`${BACKEND_URL}/api/refresh-data`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                statusDiv.innerHTML = `
                    ✅ <strong>Başarılı!</strong><br>
                    📊 ${data.profiles_updated} profil güncellendi<br>
                    🕐 ${new Date(data.last_update).toLocaleString('tr-TR')}
                `;
            } catch (error) {
                statusDiv.innerHTML = `❌ Hata: ${error.message}`;
            }
        }
    </script>
</body>
</html>
```

Admin paneline eriş:
```
https://beymetal-frontend.onrender.com/admin.html
```

---

## ⚠️ Önemli Notlar

### 1. Cold Start
Render.com free tier 15 dakika sonra uyur:
- İlk istek 30-60 saniye sürebilir
- Sonraki istekler hızlı

**Çözüm:** Ücretli tier ($7/ay) veya keep-alive ping

### 2. CORS
Şu an `CORS_ORIGINS=*` (herkese açık)

**Güvenli hale getir:**
```python
CORS_ORIGINS=https://beymetal-frontend.onrender.com
```

### 3. Rate Limiting
Kötüye kullanımı önle (opsiyonel):
```python
# main.py'ye ekle
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/chat")
@limiter.limit("20/minute")
async def chat(request: dict):
    ...
```

---

## 📊 Maliyet

### Ücretsiz Tier
- **Backend:** 750 saat/ay (yeterli)
- **Frontend:** Sınırsız
- **Bandwidth:** 100GB/ay
- **Build Minutes:** 500/ay

**Toplam: 0 TL/ay** ✅

### Ücretli Tier (İhtiyaç olursa)
- **Backend Starter:** $7/ay
  - Always-on (uyumaz)
  - Daha hızlı
  - Daha fazla RAM

---

## 🐛 Sorun Giderme

### "Service Unavailable"
Backend uyumuş olabilir:
- İlk isteği bekle (30-60 saniye)
- Veya health endpoint'e ping at

### "CORS Error"
Backend'de CORS ayarlarını kontrol et:
```python
CORS_ORIGINS=https://beymetal-frontend.onrender.com
```

### "Excel Güncellenmiyor"
1. Backend logs'a bak (Render dashboard)
2. Google Drive file ID'yi kontrol et
3. Manuel refresh dene

### "Slow Response"
Normal! Free tier:
- Cold start: 30-60 saniye
- Warm: <1 saniye

---

## 🎯 Sonraki Adımlar

1. ✅ Deploy et
2. ✅ Test et
3. ✅ Admin panel ekle
4. ✅ Custom domain bağla (opsiyonel)
5. ✅ Analytics ekle (opsiyonel)

---

## 📞 Destek

Sorun yaşarsan:
1. Render.com logs'a bak
2. GitHub Issues aç
3. Render.com community forum

**Başarılar!** 🚀
