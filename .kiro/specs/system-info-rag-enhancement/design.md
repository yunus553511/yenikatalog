# Design Document - System Info RAG Enhancement

## Overview

Bu özellik, RAG servisinin profil kodlarını sorgularken hangi sistemde (örn: LR 3100 SİSTEMİ) olduğunu da bilmesini ve kullanıcıya sunmasını sağlar. Mevcut Connection Service ile entegre çalışarak profil-sistem eşleşmelerini otomatik olarak bulur ve chatbot cevaplarına ekler.

## Architecture

### High-Level Flow

```
Kullanıcı Sorusu
      ↓
RAG Service (format_direct_answer)
      ↓
Profil Kodu Tespit Et
      ↓
Connection Service'ten Sistem Bilgisi Al
      ↓
Profil Veritabanından Diğer Bilgileri Al
      ↓
Birleştirilmiş Cevap Oluştur
      ↓
Kullanıcıya Göster
```

### Component Interaction

```
┌─────────────────────────────────────────────────┐
│           RAG Service                           │
│  ┌───────────────────────────────────────────┐  │
│  │  format_direct_answer()                   │  │
│  │    ↓                                      │  │
│  │  _get_system_info_for_profile()          │  │
│  │    ↓                                      │  │
│  │  _enrich_profile_with_system()           │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│        Connection Service                       │
│  - get_profile_connections(profile_code)        │
│  - search_connections(query)                    │
│  - In-memory cache                              │
└─────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. RAG Service Enhancement

**File:** `backend/services/rag_service.py`

**New Methods:**

```python
def _get_system_info_for_profile(self, profile_code: str) -> Optional[str]:
    """
    Profil kodu için sistem bilgisini al
    
    Args:
        profile_code: Profil kodu (örn: LR3101-1, AP0001)
        
    Returns:
        Sistem adı veya None
        
    Logic:
        1. Profil kodunu normalize et (LR3101-1 → LR-3101)
        2. Connection service'ten profil birleşim bilgisini al
        3. Sistem adını döndür
    """
    pass

def _normalize_profile_code(self, code: str) -> str:
    """
    Profil kodunu normalize et (farklı yazım şekillerini standartlaştır)
    
    Args:
        code: Profil kodu (LR3101-1, LR-3101-1, LR 3101-1)
        
    Returns:
        Normalize edilmiş kod (LR-3101)
        
    Examples:
        LR3101-1 → LR-3101
        LR-3101-1 → LR-3101
        AP0001 → AP-0001 (eğer gerekirse)
    """
    pass

def _enrich_profile_with_system(self, profile: Profile, profile_code: str) -> Dict:
    """
    Profil bilgisine sistem bilgisini ekle
    
    Args:
        profile: Profile objesi
        profile_code: Profil kodu
        
    Returns:
        Zenginleştirilmiş profil dictionary'si
        {
            'code': 'LR3101-1',
            'category': 'KASA',
            'customer': 'ALFORE',
            'mold_status': 'Kalıp Mevcut',
            'system': 'LR 3100 SİSTEMİ',  # YENİ
            'dimensions': {...}
        }
    """
    pass
```

**Modified Methods:**

```python
def format_direct_answer(self, query: str, top_k: int = 5) -> str:
    """
    LLM olmadan direkt cevap oluştur
    
    DEĞIŞIKLIK:
    - Profil bilgilerine sistem bilgisini ekle
    - Sistem bilgisini cevabın üst kısmında göster
    """
    # Mevcut kod...
    
    # Profil bulunduysa sistem bilgisini ekle
    if results:
        for profile, score, reason in results:
            # Sistem bilgisini al
            system_info = self._get_system_info_for_profile(profile.code)
            
            # Cevaba ekle
            if system_info:
                answer_parts.append(f"• Sistem: {system_info}")
```

### 2. Connection Service Integration

**File:** `backend/services/connection_service.py`

**Mevcut Metodlar (Kullanılacak):**

```python
def get_profile_connections(self, profile_code: str) -> Optional[Dict]:
    """
    Belirli bir profilin birleşim bilgilerini getir
    
    Returns:
        {
            'system': 'LR 3100 SİSTEMİ',
            'profile': {...}
        }
    """
    pass

def search_connections(self, query: str) -> List[Dict]:
    """
    Birleşim verilerinde arama yap
    
    Returns:
        [
            {
                'type': 'profile',
                'system': 'LR 3100 SİSTEMİ',
                'profile': {...}
            }
        ]
    """
    pass
```

**Yeni Metod (Opsiyonel - Performans için):**

```python
def get_system_for_profile_code(self, profile_code: str) -> Optional[str]:
    """
    Sadece sistem adını döndür (hafif versiyon)
    
    Args:
        profile_code: Profil kodu
        
    Returns:
        Sistem adı veya None
        
    Note:
        get_profile_connections() yerine kullanılabilir
        Daha hızlı çünkü sadece sistem adını döndürür
    """
    pass
```

## Data Flow

### Senaryo 1: Tek Profil Sorgusu

```
Kullanıcı: "LR3101-1 nedir?"
    ↓
RAG Service: format_direct_answer()
    ↓
Search Service: search("LR3101-1") → [Profile(code="LR3101-1", category="KASA", ...)]
    ↓
RAG Service: _get_system_info_for_profile("LR3101-1")
    ↓
Connection Service: get_profile_connections("LR-3101")
    ↓
Return: {'system': 'LR 3100 SİSTEMİ', 'profile': {...}}
    ↓
RAG Service: Cevap oluştur
    ↓
Chatbot: 
    "**LR3101-1** profilini buldum:
    
    • Sistem: LR 3100 SİSTEMİ
    • Kategori: KASA
    • Müşteri: ALFORE
    • Kalıp: Kalıp Mevcut
    • Ölçüler: ..."
```

### Senaryo 2: Sistem Bazlı Arama

```
Kullanıcı: "LR 3100 sistemindeki profiller nelerdir?"
    ↓
RAG Service: _is_connection_query() → True
    ↓
RAG Service: _get_connection_context()
    ↓
Connection Service: search_connections("LR 3100")
    ↓
Return: [
    {'type': 'system', 'system': 'LR 3100 SİSTEMİ'},
    {'type': 'profile', 'system': 'LR 3100 SİSTEMİ', 'profile': {...}},
    ...
]
    ↓
RAG Service: _format_system_profiles()
    ↓
Chatbot:
    "**LR 3100 SİSTEMİ** Profilleri
    
    Bu sistemde **15 profil** bulunmaktadır:
    
    1. LR-3101 - Çift Ray Sürme Kasa Profili
       Fitiller: P200000
       Ağırlık: 1.51 kg/m
    ..."
```

### Senaryo 3: Birden Fazla Profil Sonucu

```
Kullanıcı: "KASA kategorisindeki profiller"
    ↓
Search Service: search("KASA") → [Profile1, Profile2, Profile3, ...]
    ↓
RAG Service: Her profil için sistem bilgisini al
    ↓
Chatbot:
    "**KASA** kategorisinden **10 profil** buldum:
    
    1. **LR3101-1** - KASA
       Sistem: LR 3100 SİSTEMİ
       Müşteri: ALFORE
       ...
    
    2. **LR3201-1** - KASA
       Sistem: LR 3200 SİSTEMİ
       Müşteri: BEYMETAL
       ..."
```

## Error Handling

### 1. Sistem Bilgisi Bulunamadı

```python
system_info = self._get_system_info_for_profile(profile.code)

if system_info:
    answer_parts.append(f"• Sistem: {system_info}")
else:
    # Sistem bilgisi yoksa sadece logla, cevabı göstermeye devam et
    logger.warning(f"System info not found for profile: {profile.code}")
    # Diğer bilgileri göster (kategori, müşteri, kalıp)
```

### 2. Connection Service Erişilemez

```python
try:
    system_info = self._get_system_info_for_profile(profile.code)
except Exception as e:
    logger.error(f"Failed to get system info: {e}")
    system_info = None
    # Devam et, sadece sistem bilgisi olmadan göster
```

### 3. Profil Kodu Normalize Edilemedi

```python
def _normalize_profile_code(self, code: str) -> str:
    try:
        # Normalizasyon logic
        return normalized_code
    except Exception as e:
        logger.warning(f"Failed to normalize profile code '{code}': {e}")
        return code  # Orijinal kodu döndür
```

## Performance Considerations

### 1. In-Memory Cache Kullanımı

Connection Service zaten in-memory cache kullanıyor:
- Tüm sistem ve profil verileri memory'de
- Hızlı erişim (< 1ms)
- 24 saatte bir otomatik yenileme

### 2. Lazy Loading

Sistem bilgisi sadece gerektiğinde alınır:
- Profil bulunduysa → sistem bilgisi al
- Profil bulunamadıysa → sistem bilgisi alma

### 3. Batch Processing (Gelecek İyileştirme)

Birden fazla profil için sistem bilgisi alınırken:
```python
# Şu anki yaklaşım (her profil için ayrı çağrı)
for profile in profiles:
    system_info = self._get_system_info_for_profile(profile.code)

# Gelecek iyileştirme (tek çağrı)
system_infos = self._get_system_info_for_profiles([p.code for p in profiles])
```

## Testing Strategy

### Unit Tests

**Test File:** `backend/tests/test_rag_system_info.py`

```python
def test_get_system_info_for_profile():
    """LR profili için sistem bilgisi alınmalı"""
    rag = RAGService()
    system = rag._get_system_info_for_profile("LR3101-1")
    assert system == "LR 3100 SİSTEMİ"

def test_normalize_profile_code():
    """Profil kodu normalize edilmeli"""
    rag = RAGService()
    assert rag._normalize_profile_code("LR3101-1") == "LR-3101"
    assert rag._normalize_profile_code("LR-3101-1") == "LR-3101"
    assert rag._normalize_profile_code("LR 3101-1") == "LR-3101"

def test_system_info_not_found():
    """Sistem bilgisi bulunamazsa None dönmeli"""
    rag = RAGService()
    system = rag._get_system_info_for_profile("INVALID_CODE")
    assert system is None

def test_enrich_profile_with_system():
    """Profil bilgisine sistem eklenebilmeli"""
    rag = RAGService()
    profile = Profile(code="LR3101-1", category="KASA", ...)
    enriched = rag._enrich_profile_with_system(profile, "LR3101-1")
    assert enriched['system'] == "LR 3100 SİSTEMİ"
```

### Integration Tests

```python
def test_format_direct_answer_with_system():
    """Cevap sistem bilgisini içermeli"""
    rag = RAGService()
    answer = rag.format_direct_answer("LR3101-1 nedir?")
    assert "LR 3100 SİSTEMİ" in answer
    assert "KASA" in answer

def test_multiple_profiles_with_systems():
    """Birden fazla profil için sistem bilgileri gösterilmeli"""
    rag = RAGService()
    answer = rag.format_direct_answer("KASA kategorisi")
    # Her profil için sistem bilgisi olmalı
    assert "Sistem:" in answer
```

### Manual Testing Scenarios

1. **Tek profil sorgusu**
   - Input: "LR3101-1 nedir?"
   - Expected: Sistem bilgisi gösterilmeli

2. **Sistem bazlı arama**
   - Input: "LR 3100 sistemindeki profiller nelerdir?"
   - Expected: Sistemdeki tüm profiller listelenmeli

3. **Kategori araması**
   - Input: "KASA kategorisindeki profiller"
   - Expected: Her profil için sistem bilgisi gösterilmeli

4. **Sistem bilgisi olmayan profil**
   - Input: "AP0001 nedir?" (eğer connection service'te yoksa)
   - Expected: Diğer bilgiler gösterilmeli, hata olmamalı

## Implementation Notes

### Profil Kodu Normalizasyonu

LR profilleri için farklı yazım şekilleri:
- `LR3101-1` → `LR-3101` (birleşim kodu)
- `LR-3101-1` → `LR-3101`
- `LR 3101-1` → `LR-3101`

Logic:
```python
def _normalize_profile_code(self, code: str) -> str:
    # LR/GL profilleri için
    if code.startswith(('LR', 'GL', 'lr', 'gl')):
        # LR3101-1 → LR-3101
        # LR-3101-1 → LR-3101
        import re
        match = re.match(r'([A-Z]{2})-?(\d{4})', code, re.IGNORECASE)
        if match:
            prefix = match.group(1).upper()
            number = match.group(2)
            return f"{prefix}-{number}"
    
    return code.upper()
```

### Sistem Adı Formatı

Connection Service'ten gelen format:
- `LR 3100 SİSTEMİ`
- `LR 3200 SİSTEMİ`
- `GL 3100 SİSTEMİ`

Bu format aynen kullanılacak (değişiklik yok).

## Future Enhancements

### 1. Sistem Görseli

Sistem bilgisi ile birlikte sistem görseli de gösterilebilir:
```markdown
• Sistem: LR 3100 SİSTEMİ
  ![LR 3100 System](http://localhost:8001/api/system-image/LR-3100)
```

### 2. Sistem Özellikleri

Sistem hakkında ek bilgiler:
```markdown
• Sistem: LR 3100 SİSTEMİ
  - Tip: Çift Ray Sürme Sistemi
  - Profil Sayısı: 15
  - Toplam Ağırlık: 22.5 kg/m
```

### 3. İlgili Sistemler

Benzer sistemleri öner:
```markdown
• Sistem: LR 3100 SİSTEMİ

İlgili Sistemler:
- LR 3200 SİSTEMİ (Üç Ray Sürme)
- GL 3100 SİSTEMİ (Giyotin Sistemi)
```

## Deployment Checklist

- [ ] RAG Service'e yeni metodlar ekle
- [ ] format_direct_answer() metodunu güncelle
- [ ] Unit testleri yaz ve çalıştır
- [ ] Integration testleri yaz ve çalıştır
- [ ] Manuel test senaryolarını çalıştır
- [ ] Logging ekle (debug, info, warning)
- [ ] Error handling ekle
- [ ] Performance testleri yap
- [ ] Documentation güncelle
- [ ] Code review
- [ ] Production'a deploy
