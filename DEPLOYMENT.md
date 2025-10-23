# 🚀 Deployment Rehberi

## Sistem Mimarisi

```
┌─────────────────┐         ┌──────────────────┐
│   Netlify       │  HTTPS  │   Render.com     │
│   (Frontend)    │ ──────> │   (Backend API)  │
│                 │         │                  │
│ - HTML/CSS/JS   │         │ - Python FastAPI │
│ - Chat Widget   │         │ - Excel Parser   │
└─────────────────┘         │ - Search Engine  │
                            └──────────────────┘
                                     │
                                     ▼
                            ┌──────────────────┐
                            │  Google Drive    │
                            │  (Excel Data)    │
                            └──────────────────┘
```

## 1. Backend Deployment (Render.com)

### Adım 1: Render.com'a Kayıt Ol
- https://render.com adresine git
- GitHub ile giriş yap

### Adım 2: Backend'i Hazırla

**requirements.txt oluştur:**
```txt
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
python-dotenv>=1.0.0
openpyxl>=3.1.0
httpx>=0.24.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
gdown>=4.7.0
scikit-learn>=1.3.0
```

**render.yaml oluştur:**
```yaml
services:
  - type: web
    name: beymetal-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GOOGLE_DRIVE_FILE_ID
        value: 1RcUAmXf7VNqzh7Pv1Zo8zoQ7zuf2_t3FJXkT_tCLixw
      - key: CORS_ORIGINS
        value: https://beymetal.netlify.app,http://localhost:8000
      - key: RAG_SIMILARITY_THRESHOLD
        value: 0.15
```

### Adım 3: Deploy Et
1. Render.com'da "New Web Service" tıkla
2. GitHub repo'nu bağla
3. `backend` klasörünü seç
4. Deploy'a bas
5. URL'i not al: `https://beymetal-api.onrender.com`

---

## 2. Frontend Deployment (Netlify)

### Adım 1: Frontend'i Hazırla

**script.js'de API URL'i güncelle:**
```javascript
// Geliştirme
const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8001/api/chat'
    : 'https://beymetal-api.onrender.com/api/chat';
```

**netlify.toml oluştur:**
```toml
[build]
  publish = "prototype"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

### Adım 2: Deploy Et
1. Netlify'a git: https://netlify.com
2. "Add new site" → "Import from Git"
3. GitHub repo'nu seç
4. Build settings:
   - Base directory: `prototype`
   - Publish directory: `prototype`
5. Deploy'a bas

---

## 3. Excel Güncelleme Sistemi

### Manuel Güncelleme (Basit)

**Admin paneli ekle (admin.html):**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Beymetal Admin</title>
</head>
<body>
    <h1>Admin Panel</h1>
    <button onclick="refreshData()">Excel Verilerini Yenile</button>
    <div id="status"></div>
    
    <script>
        async function refreshData() {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = 'Yenileniyor...';
            
            try {
                const response = await fetch('https://beymetal-api.onrender.com/api/refresh-data', {
                    method: 'POST'
                });
                const data = await response.json();
                statusDiv.textContent = `Başarılı! ${data.profiles_updated} profil güncellendi.`;
            } catch (error) {
                statusDiv.textContent = 'Hata: ' + error.message;
            }
        }
    </script>
</body>
</html>
```

### Otomatik Güncelleme (İleri Seviye)

**Backend'e scheduler ekle:**

1. **requirements.txt'e ekle:**
```txt
apscheduler>=3.10.0
```

2. **main.py'ye ekle:**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Beymetal Chat API...")
    
    # ... mevcut kod ...
    
    # Scheduler başlat
    scheduler.add_job(
        excel_service.refresh_data,
        'cron',
        hour=6,  # Her sabah 6'da
        minute=0,
        id='daily_refresh'
    )
    scheduler.start()
    logger.info("Scheduler started: Daily refresh at 6:00 AM")
    
    yield
    
    scheduler.shutdown()
    logger.info("Shutting down...")
```

---

## 4. Güvenlik ve Optimizasyon

### Environment Variables
Backend'de hassas bilgileri gizle:
```bash
# Render.com'da Environment Variables bölümünde ayarla
GOOGLE_DRIVE_FILE_ID=xxx
API_KEY=xxx  # Gelecekte eklenebilir
```

### Rate Limiting
Kötüye kullanımı önle:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/chat")
@limiter.limit("10/minute")  # Dakikada 10 istek
async def chat(request: dict):
    ...
```

### Caching
Sık sorulan soruları cache'le:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_response(query: str):
    return search_service.search(query)
```

---

## 5. Monitoring ve Bakım

### Health Check
Render.com otomatik health check yapar:
- Endpoint: `/api/health`
- Interval: 30 saniye

### Logs
Render.com dashboard'da logları izle:
- Errors
- API requests
- Excel refresh durumu

### Backup
Google Drive zaten backup görevi görüyor, ama:
- Embedding'leri periyodik kaydet
- Database backup (gelecekte)

---

## 6. Maliyet

### Ücretsiz Tier (Başlangıç)
- **Netlify**: Ücretsiz (100GB bandwidth)
- **Render.com**: Ücretsiz (750 saat/ay)
- **Google Drive**: Ücretsiz (15GB)

**Toplam: 0 TL/ay** ✅

### Ücretli Tier (Büyüme)
- **Netlify Pro**: $19/ay
- **Render.com Starter**: $7/ay
- **Google Workspace**: $6/ay

**Toplam: ~$32/ay** (yaklaşık 1000 TL/ay)

---

## 7. Deployment Checklist

### Backend (Render.com)
- [ ] requirements.txt hazır
- [ ] Environment variables ayarlandı
- [ ] CORS origins güncellendi
- [ ] Health check çalışıyor
- [ ] Excel indirme test edildi

### Frontend (Netlify)
- [ ] API URL production'a ayarlandı
- [ ] CORS testi yapıldı
- [ ] Chat widget çalışıyor
- [ ] Responsive tasarım kontrol edildi

### Test
- [ ] Production'da chat testi
- [ ] Excel refresh testi
- [ ] Farklı cihazlarda test
- [ ] Performans testi

---

## 8. Sorun Giderme

### "CORS Error"
Backend'de CORS origins'e frontend URL'ini ekle:
```python
CORS_ORIGINS=https://beymetal.netlify.app
```

### "Backend Slow"
Render.com free tier 15 dakika sonra uyur:
- İlk istek yavaş olabilir (cold start)
- Çözüm: Ücretli tier veya keep-alive ping

### "Excel Güncellenmiyor"
Manuel refresh endpoint'ini çağır:
```bash
curl -X POST https://beymetal-api.onrender.com/api/refresh-data
```

---

## 9. Gelecek İyileştirmeler

- [ ] LM Studio entegrasyonu (opsiyonel)
- [ ] Kullanıcı authentication
- [ ] Analytics (kaç soru soruldu)
- [ ] A/B testing
- [ ] Multi-language support
- [ ] Mobile app

---

## İletişim ve Destek

Sorularınız için:
- GitHub Issues
- Email: support@beymetal.com
- Dokümantasyon: /docs
