# 🚀 Render.com Deploy Adımları

## ✅ Ön Hazırlık Tamamlandı
- ✅ Backend hazır
- ✅ Frontend hazır
- ✅ Benzerlik API ayrı klasörde
- ✅ .gitignore hazır
- ✅ requirements.txt hazır

---

## 📝 ADIM 1: GitHub'a Push Et

### 1.1 Git Başlat (İlk defa ise)
```bash
cd "C:\Users\yunus.hezer\Desktop\YENİ KATALOG WİNDSURF\yani katalog"
git init
```

### 1.2 Dosyaları Ekle
```bash
git add .
```

### 1.3 Commit Yap
```bash
git commit -m "Initial commit - Backend, Frontend, Similarity API ready"
```

### 1.4 GitHub Repository Oluştur
1. https://github.com adresine git
2. Sağ üstte **"+"** → **"New repository"**
3. Repository adı: `beymetal-catalog` (veya istediğin isim)
4. **Public** seç
5. **"Create repository"** tıkla

### 1.5 GitHub'a Push Et
GitHub'da gösterilen komutları kullan:
```bash
git remote add origin https://github.com/KULLANICI_ADIN/beymetal-catalog.git
git branch -M main
git push -u origin main
```

---

## 🌐 ADIM 2: Render.com'da Ana Backend Deploy Et

### 2.1 Render.com'a Git
1. https://render.com adresine git
2. **"Sign Up"** veya **"Log In"** (GitHub ile giriş yap)

### 2.2 Ana Backend Oluştur
1. Dashboard'da **"New +"** → **"Web Service"**
2. GitHub repo'nu bağla (beymetal-catalog)
3. Ayarlar:

**Name:** `beymetal-backend`

**Runtime:** `Python 3`

**Root Directory:** `backend`

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Instance Type:** `Free`

### 2.3 Environment Variables Ekle
**"Environment"** sekmesinde:

```
PORT=8004
CORS_ORIGINS=*
GOOGLE_DRIVE_FILE_ID=1RcUAmXf7VNqzh7Pv1Zo8zoQ7zuf2_t3FJXkT_tCLixw
SUPABASE_URL=https://xxxxxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SIMILARITY_API_URL=https://beymetal-similarity.onrender.com
```

⚠️ **ÖNEMLİ:** Supabase bilgilerini kendininkilerle değiştir!

### 2.4 Deploy Et
1. **"Create Web Service"** tıkla
2. Build başlayacak (5-10 dakika sürer)
3. URL'i kopyala: `https://beymetal-backend.onrender.com`

---

## 🔍 ADIM 3: Benzerlik API Deploy Et

### 3.1 Yeni Web Service Oluştur
1. Dashboard'da **"New +"** → **"Web Service"**
2. Aynı GitHub repo'yu seç

### 3.2 Benzerlik API Ayarları
**Name:** `beymetal-similarity`

**Runtime:** `Python 3`

**Root Directory:** `YENİ BENZERLİK`

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
python main.py
```

**Instance Type:** `Free` (yavaş olabilir) veya `Starter $7/ay` (önerilen)

### 3.3 Environment Variables
```
PORT=8003
IMAGE_DIR=/opt/render/project/src/YENİPNGLER
```

### 3.4 Deploy Et
1. **"Create Web Service"** tıkla
2. Build başlayacak
3. URL'i kopyala: `https://beymetal-similarity.onrender.com`

---

## 🔗 ADIM 4: Backend'i Benzerlik API'ye Bağla

### 4.1 Ana Backend'in Environment'ını Güncelle
1. Render.com → `beymetal-backend` → **"Environment"**
2. `SIMILARITY_API_URL` değerini güncelle:
```
SIMILARITY_API_URL=https://beymetal-similarity.onrender.com
```
3. **"Save Changes"** → Otomatik yeniden deploy olur

---

## 🎨 ADIM 5: Frontend Deploy Et

### 5.1 Static Site Oluştur
1. Dashboard'da **"New +"** → **"Static Site"**
2. Aynı GitHub repo'yu seç

### 5.2 Frontend Ayarları
**Name:** `beymetal-frontend`

**Build Command:** (Boş bırak)

**Publish Directory:** `prototype`

### 5.3 Deploy Et
1. **"Create Static Site"** tıkla
2. URL'i kopyala: `https://beymetal-frontend.onrender.com`

---

## 🔧 ADIM 6: Frontend'i Backend'e Bağla

### 6.1 script.js'i Güncelle
Lokal bilgisayarında:

```javascript
// prototype/script.js - 2. satır
const API_BASE_URL = 'https://beymetal-backend.onrender.com';
```

### 6.2 GitHub'a Push Et
```bash
git add prototype/script.js
git commit -m "Update API URL for production"
git push
```

### 6.3 Otomatik Deploy
Render.com frontend'i otomatik yeniden deploy eder (2-3 dakika)

---

## ✅ ADIM 7: Test Et!

### 7.1 Backend Test
Tarayıcıda aç:
```
https://beymetal-backend.onrender.com/api/health
```

Görmeli:
```json
{
  "status": "healthy",
  "profiles_count": 3497
}
```

### 7.2 Benzerlik API Test
```
https://beymetal-similarity.onrender.com/health
```

Görmeli:
```json
{
  "status": "healthy",
  "indexed_profiles": 3607
}
```

### 7.3 Frontend Test
Tarayıcıda aç:
```
https://beymetal-frontend.onrender.com
```

1. ✅ Kategorileri gör
2. ✅ Chat'i test et
3. ✅ Benzerlik aramayı test et
4. ✅ Sistemleri gör

---

## 🐛 Sorun Giderme

### Backend 503 Error
- İlk istekte 30-60 saniye bekle (cold start)
- Logs'a bak: Render Dashboard → Service → Logs

### Görseller Yüklenmiyor
- Supabase URL ve Key doğru mu?
- Bucket public mi?

### Benzerlik API Çalışmıyor
- PNG dosyaları Render'da yok (Supabase'de olmalı)
- Environment variables doğru mu?

### Frontend Backend'e Bağlanamıyor
- `script.js` içinde API_BASE_URL doğru mu?
- CORS ayarları kontrol et

---

## 💰 Maliyet

**Free Plan:**
- Ana Backend: $0/ay (750 saat)
- Benzerlik API: $0/ay (yavaş)
- Frontend: $0/ay (sınırsız)
**Toplam: $0/ay**

**Önerilen:**
- Ana Backend: $0/ay
- Benzerlik API: $7/ay (Starter - hızlı)
- Frontend: $0/ay
**Toplam: $7/ay**

---

## 🎉 Başarılı Deployment!

Artık canlıdasınız! 🚀

**Frontend:** https://beymetal-frontend.onrender.com
**Backend:** https://beymetal-backend.onrender.com
**Similarity:** https://beymetal-similarity.onrender.com

---

## 📞 Yardım

Sorun olursa:
1. Render.com Logs'u kontrol et
2. Browser Console'u kontrol et (F12)
3. Network tab'ı kontrol et

**Başarılar!** 🎊
