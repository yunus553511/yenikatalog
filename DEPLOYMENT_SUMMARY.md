# 🚀 Render Deployment - Hızlı Özet

## 📦 Yapı
```
3 Ayrı Render Service:
├── 1. Ana Backend (beymetal-backend)
│   └── Port 8004, Chat, Catalog, RAG
├── 2. Benzerlik API (beymetal-similarity)  
│   └── Port 8003, AI Similarity Search
└── 3. Frontend (beymetal-frontend)
    └── Static Site, HTML/CSS/JS
```

## 🎯 Deployment Sırası

### 1️⃣ Benzerlik API'yi İlk Deploy Et
```
Name: beymetal-similarity
Root Directory: YENİ BENZERLİK
Build: pip install -r requirements.txt
Start: python main.py
Env: PORT=8003
```
**URL:** `https://beymetal-similarity.onrender.com`

### 2️⃣ Ana Backend'i Deploy Et
```
Name: beymetal-backend
Root Directory: backend
Build: pip install -r requirements.txt
Start: uvicorn main:app --host 0.0.0.0 --port $PORT
Env:
  PORT=8004
  SIMILARITY_API_URL=https://beymetal-similarity.onrender.com
  SUPABASE_URL=https://your-project.supabase.co
  CORS_ORIGINS=*
```
**URL:** `https://beymetal-backend.onrender.com`

### 3️⃣ Frontend'i Deploy Et
```
Name: beymetal-frontend
Publish Directory: prototype
Build: (boş)
```

### 4️⃣ script.js'i Güncelle
```javascript
const API_BASE_URL = 'https://beymetal-backend.onrender.com';
```

Git push → Otomatik deploy!

## ✅ Test

### Benzerlik API:
```bash
curl https://beymetal-similarity.onrender.com/health
# → {"status":"healthy","indexed_profiles":3607}
```

### Ana Backend:
```bash
curl https://beymetal-backend.onrender.com/api/health
# → {"status":"healthy","profiles_count":3497}
```

### Benzerlik Endpoint:
```bash
curl https://beymetal-backend.onrender.com/api/similarity/LR3104?top_k=10
# → {"query_profile":"LR3104","results":[...]}
```

## 💰 Maliyet

**Free Tier:**
- Benzerlik API: $0/ay (ama yavaş olabilir)
- Ana Backend: $0/ay
- Frontend: $0/ay
**Toplam: $0/ay**

**Önerilen (Hızlı):**
- Benzerlik API: $7/ay (Starter - AI model hızlı çalışır)
- Ana Backend: $0/ay (Free yeterli)
- Frontend: $0/ay
**Toplam: $7/ay**

## ⚠️ Önemli Notlar

1. **Benzerlik API'yi önce deploy et** → URL'i al → Ana backend'e ekle
2. **PNG görseller** Supabase'de olmalı (Render'da dosya depolanamaz)
3. **Free tier** 15 dakika sonra uyur (ilk istek yavaş)
4. **CORS** production'da düzelt: `CORS_ORIGINS=https://your-frontend-url.onrender.com`

## 🐛 Sorun Giderme

**Benzerlik API bulunamıyor:**
```bash
# Backend logs'a bak
# SIMILARITY_API_URL doğru mu kontrol et
```

**Görseller yüklenmiyor:**
```bash
# Supabase URL'ini kontrol et
# Bucket public mi?
```

**Cold start çok yavaş:**
```bash
# Benzerlik API'yi Starter plan'a yükselt ($7/ay)
# Veya keep-alive ping ekle
```

## 📝 Tam Detaylar
Detaylı deployment adımları için: `RENDER_DEPLOYMENT.md`
