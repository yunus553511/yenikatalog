# 🚀 Render.com Manuel Deployment - Adım Adım

## BÖLÜM 1: BACKEND DEPLOY

### Adım 1: Render.com'a Giriş
1. https://render.com adresine git
2. **"Get Started"** veya **"Sign In"** tıkla
3. **GitHub** ile giriş yap

### Adım 2: Backend Web Service Oluştur
1. Dashboard'da sağ üstte **"New +"** butonuna tıkla
2. **"Web Service"** seç

### Adım 3: Repository Seç
1. GitHub repository listesinde **"beymetal-chat"** bul
2. Sağındaki **"Connect"** butonuna tıkla

### Adım 4: Backend Ayarları Yap

**Name (İsim):**
```
beymetal-backend
```

**Region (Bölge):**
```
Frankfurt (EU Central)
```

**Branch:**
```
main
```

**Root Directory:**
```
backend
```
(ÖNEMLİ: "backend" yazın, boş bırakmayın!)

**Runtime:**
```
Python 3
```

**Build Command:**
```
pip install -r requirements.txt
```

**Start Command:**
```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Instance Type:**
```
Free
```

### Adım 5: Environment Variables Ekle

Aşağıya kaydır, **"Environment Variables"** bölümünü bul.

**"Add Environment Variable"** butonuna tıkla ve şunları ekle:

**1. GOOGLE_DRIVE_FILE_ID**
```
Key: GOOGLE_DRIVE_FILE_ID
Value: 1RcUAmXf7VNqzh7Pv1Zo8zoQ7zuf2_t3FJXkT_tCLixw
```

**2. CORS_ORIGINS**
```
Key: CORS_ORIGINS
Value: *
```

**3. RAG_SIMILARITY_THRESHOLD**
```
Key: RAG_SIMILARITY_THRESHOLD
Value: 0.15
```

**4. PYTHON_VERSION**
```
Key: PYTHON_VERSION
Value: 3.11.0
```

### Adım 6: Deploy Et!
1. En altta **"Create Web Service"** butonuna tıkla
2. Deploy başlayacak (5-10 dakika sürer)
3. Logs'u izle - yeşil "Live" yazısını bekle

### Adım 7: Backend URL'ini Kopyala
Deploy tamamlandığında üstte URL göreceksin:
```
https://beymetal-backend-XXXX.onrender.com
```
Bu URL'i kopyala! Frontend'de kullanacağız.

---

## BÖLÜM 2: FRONTEND DEPLOY

### Adım 1: Frontend URL'ini Güncelle

**ÖNEMLİ:** Önce backend URL'ini frontend'e yazalım.

Backend URL'inizi kopyalayın (örnek):
```
https://beymetal-backend-abc123.onrender.com
```

### Adım 2: script.js'i Güncelle

`prototype/script.js` dosyasını aç ve şu satırı bul (yaklaşık 98. satır):
```javascript
API_URL = 'https://beymetal-backend.onrender.com/api/chat';
```

Bunu backend URL'iniz ile değiştir:
```javascript
API_URL = 'https://beymetal-backend-abc123.onrender.com/api/chat';
```

### Adım 3: GitHub'a Push Et

Terminal'de:
```bash
git add prototype/script.js
git commit -m "Update backend URL"
git push
```

### Adım 4: Frontend Static Site Oluştur

1. Render.com dashboard'da tekrar **"New +"** tıkla
2. **"Static Site"** seç

### Adım 5: Repository Seç
1. **"beymetal-chat"** repository'sini bul
2. **"Connect"** tıkla

### Adım 6: Frontend Ayarları Yap

**Name:**
```
beymetal-frontend
```

**Branch:**
```
main
```

**Root Directory:**
```
(boş bırak)
```

**Build Command:**
```
(boş bırak)
```

**Publish Directory:**
```
prototype
```

### Adım 7: Deploy Et!
1. **"Create Static Site"** tıkla
2. Deploy başlayacak (2-3 dakika)
3. "Published" yazısını bekle

### Adım 8: Frontend URL'ini Aç
```
https://beymetal-frontend-XXXX.onrender.com
```

---

## BÖLÜM 3: TEST

### 1. Backend Test
Browser'da aç:
```
https://beymetal-backend-XXXX.onrender.com/api/health
```

Görmek istediğin:
```json
{
  "status": "healthy",
  "profiles_count": 225,
  "vector_db_ready": true
}
```

### 2. Frontend Test
```
https://beymetal-frontend-XXXX.onrender.com
```

Chat widget'a tıkla ve test et:
- "100 kutu"
- "çap 28"
- "30x30 lama"

---

## ⚠️ Önemli Notlar

### İlk İstek Yavaş
Free tier 15 dakika sonra uyur. İlk istek 30-60 saniye sürebilir. Normal!

### CORS Hatası Alırsan
Backend'de CORS ayarlarını kontrol et. Environment variable'da `CORS_ORIGINS=*` olmalı.

### Build Hatası Alırsan
Logs'a bak. Genelde:
- `requirements.txt` eksik paket
- Python version uyumsuzluğu
- Root directory yanlış

---

## 🎯 Özet Checklist

Backend:
- [ ] Web Service oluştur
- [ ] Root Directory: `backend`
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Environment Variables ekle (4 tane)
- [ ] Deploy et
- [ ] URL'i kopyala

Frontend:
- [ ] Backend URL'ini script.js'e yaz
- [ ] GitHub'a push et
- [ ] Static Site oluştur
- [ ] Publish Directory: `prototype`
- [ ] Deploy et
- [ ] Test et

---

Başarılar! 🚀
