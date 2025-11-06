# Beymetal Chat Backend

AI-powered chat assistant backend for Beymetal aluminum profiles.

## Kurulum

### 1. Python Sanal Ortamı Oluştur

```bash
python -m venv venv
```

### 2. Sanal Ortamı Aktifleştir

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Bağımlılıkları Yükle

```bash
pip install -r requirements.txt
```

### 4. Groq API Key Alın

1. https://console.groq.com adresine gidin
2. Ücretsiz hesap oluşturun
3. API key oluşturun
4. API key'i kopyalayın

### 5. Environment Variables Ayarla

`.env.example` dosyasını `.env` olarak kopyalayın ve gerekli değerleri düzenleyin:

```bash
copy .env.example .env
```

**Önemli:** `.env` dosyasına Groq API key'inizi ekleyin:

```bash
GROQ_API_KEY=your_groq_api_key_here
```

## Çalıştırma

```bash
python main.py
```

API şu adreste çalışacak: `http://localhost:8001`

## API Endpoints

- `GET /` - Root endpoint
- `GET /api/health` - Health check (LLM stats dahil)
- `POST /api/chat` - Chat endpoint (Groq LLM ile)
- `POST /api/refresh-data` - Refresh Excel data
- `GET /api/catalog/categories` - Katalog kategorileri
- `GET /api/catalog/profiles` - Tüm profiller
- `GET /api/connections/systems` - Birleşim sistemleri

## LLM Configuration

Groq LLM entegrasyonu için `.env` dosyasında şu ayarları yapabilirsiniz:

```bash
# Groq LLM Configuration
GROQ_API_KEY=your_api_key_here          # Groq API key (zorunlu)
GROQ_MODEL=llama-3.3-70b-versatile      # Model adı
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_TIMEOUT=10                          # Timeout (saniye)
GROQ_TEMPERATURE=0.7                     # Sampling temperature (0-2)
GROQ_MAX_TOKENS=1000                     # Maksimum token sayısı
LLM_ENABLED=true                         # LLM'i aktif/pasif yap
```

### Desteklenen Modeller

- `llama-3.3-70b-versatile` (Önerilen) - En güçlü, Türkçe desteği mükemmel
- `llama-3.1-8b-instant` - Daha hızlı, daha hafif
- `mixtral-8x7b-32768` - Uzun context desteği

### LLM'i Devre Dışı Bırakma

LLM'i devre dışı bırakmak için `.env` dosyasında:

```bash
LLM_ENABLED=false
```

Bu durumda sistem otomatik olarak fallback moduna geçer ve mevcut direkt cevap formatını kullanır.

## Geliştirme

Auto-reload ile çalıştırmak için:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```
