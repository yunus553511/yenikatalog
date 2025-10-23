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

### 4. Environment Variables Ayarla

`.env.example` dosyasını `.env` olarak kopyalayın ve gerekli değerleri düzenleyin:

```bash
copy .env.example .env
```

## Çalıştırma

```bash
python main.py
```

API şu adreste çalışacak: `http://localhost:8001`

## API Endpoints

- `GET /` - Root endpoint
- `GET /api/health` - Health check
- `POST /api/chat` - Chat endpoint (yakında)
- `POST /api/refresh-data` - Refresh Excel data (yakında)

## Geliştirme

Auto-reload ile çalıştırmak için:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```
