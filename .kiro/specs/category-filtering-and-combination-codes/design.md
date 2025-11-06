# Design Document: Category Filtering and Combination Codes

## Overview

Bu tasarım üç kritik sorunu çözmektedir:

1. **Birleşim Kodu Açıklaması**: LR-3101 gibi birleşim kodları sorgulandığında, hangi profillerin (LR-3101-1, LR-3101-2) birleşiminden oluştuğunu açıkça belirtmemesi
2. **Kategori Filtresi Hatası**: "kutu" sorgulandığında "Dairesel Kutu", "Köşebent" gibi yanlış kategorilerden sonuç göstermesi
3. **Yakın Değer Araması Eksikliği**: Standart kategorilerde (Köşebent, Lama vs.) yakın değer aramasının çalışmaması

### Root Causes

**Sorun 1 - Birleşim Kodu Açıklaması:**
- `_search_by_connection_code()` metodu birleşim kodunu bulduğunda, sadece inner/middle/outer profilleri gösteriyor
- Eğer bu alanlar boşsa, profil varyantlarını (LR-3101-1, LR-3101-2) arıyor ama açıklama eksik
- Kullanıcı "LR-3101, LR-3101-1 ve LR-3101-2'nin birleşimidir" gibi açık bir cevap görmüyor

**Sorun 2 - Kategori Filtresi:**
- `_extract_all_categories()` metodu "kutu" kelimesini gördüğünde tüm "kutu" içeren kategorileri eşleştiriyor
- "Standart Kutu", "Dairesel Kutu", "Köşebent" (açıklamasında "kutu" geçiyor) hepsi eşleşiyor
- Akıllı kategori eşleştirmesi yok - tam eşleşme veya kısmi eşleşme önceliği yok

**Sorun 3 - Yakın Değer Araması:**
- `_extract_dimension_value()` ve `_search_nearby_dimensions()` metodları var
- Ama sadece "Standart Kutu" kategorisinde çalışıyor
- Köşebent, Lama gibi diğer standart kategorilerde çalışmıyor
- Kategori tespiti basit keyword matching ile yapılıyor ("kutu", "lama" kelimeleri)

## Architecture

### Current Flow (Broken)

```
Sorgu: "kutu"
    ↓
_extract_all_categories()
    ↓
Tüm "kutu" içeren kategorileri bul
    ↓
["Standart Kutu", "Dairesel Kutu", "Köşebent"] (YANLIŞ!)
    ↓
Kombinasyon araması (2+ kategori)
    ↓
Yanlış sonuçlar
```

```
Sorgu: "30 köşebent"
    ↓
is_catalog_query() → False (ölçü var)
    ↓
Standart profil araması
    ↓
Yakın değer önerisi YOK (sadece "kutu" için var)
```

```
Sorgu: "LR3101 nedir"
    ↓
_search_by_connection_code()
    ↓
Birleşim kodu bulundu
    ↓
Profil varyantları bulundu (LR-3101-1, LR-3101-2)
    ↓
"LR-3101 bir birleşim kodudur" (hangi profillerin birleşimi açıklanmıyor)
```

### New Flow (Fixed)

```
Sorgu: "kutu"
    ↓
_extract_all_categories() (IMPROVED)
    ↓
Akıllı kategori eşleştirmesi:
  1. Tam eşleşme: "Standart Kutu" ✓
  2. Kısmi eşleşme: "Dairesel Kutu" (atla - "kutu" tek başına)
  3. Öncelik: En spesifik kategori
    ↓
["Standart Kutu"] (DOĞRU!)
    ↓
Tek kategori araması
    ↓
Doğru sonuçlar
```

```
Sorgu: "30 köşebent"
    ↓
_extract_dimension_and_category() (NEW)
    ↓
Ölçü: 30, Kategori: "Köşebent"
    ↓
_search_by_dimension_in_category() (NEW)
    ↓
30x30, 30x20, 30x40 köşebentler
    ↓
Yakın değer önerisi (±3, ±5 gibi)
```

```
Sorgu: "LR3101 nedir"
    ↓
_search_by_connection_code() (IMPROVED)
    ↓
Birleşim kodu bulundu
    ↓
Profil varyantları bulundu (LR-3101-1, LR-3101-2)
    ↓
"LR-3101, LR-3101-1 ve LR-3101-2 profillerinin birleşimidir" (AÇIK!)
```

## Components and Interfaces

### 1. Improved Category Extraction

**Method:** `_extract_all_categories(query: str) -> List[str]`

**Changes:**
- Akıllı kategori eşleştirmesi ekle
- Öncelik sırası: Tam eşleşme > Kısmi eşleşme > Genel
- Tek kelime sorguları için özel mantık ("kutu" → sadece "Standart Kutu")

**Logic:**
```python
def _extract_all_categories(self, query: str) -> List[str]:
    # ... mevcut kod ...
    
    # YENİ: Akıllı kategori eşleştirmesi
    # 1. Tam eşleşme öncelikli
    # 2. Tek kelime sorguları için özel mantık
    # 3. En spesifik kategoriyi seç
    
    # Örnek: "kutu" → sadece "Standart Kutu"
    # Örnek: "dairesel kutu" → "Dairesel Kutu"
    # Örnek: "köşebent" → "Köşebent"
```

### 2. New Dimension and Category Extraction

**Method:** `_extract_dimension_and_category(query: str) -> Tuple[Optional[int], Optional[str]]`

**Purpose:** Sorgudan hem ölçü hem kategori bilgisini extract et

**Logic:**
```python
def _extract_dimension_and_category(self, query: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Sorgudan ölçü ve kategori bilgisini extract et
    
    Args:
        query: "30 köşebent", "6 lama", "100x100 kutu"
        
    Returns:
        (dimension, category) tuple
        Örn: (30, "Köşebent"), (6, "Lama"), (100, "Standart Kutu")
    """
    import re
    
    # Pattern 1: "30 köşebent", "6 lama"
    match = re.match(r'^(\d+)\s+(\w+)', query.lower())
    if match:
        dimension = int(match.group(1))
        category_keyword = match.group(2)
        category = self._map_keyword_to_category(category_keyword)
        return dimension, category
    
    # Pattern 2: "30x30 kutu", "100 a 100 lama"
    match = re.search(r'(\d+)\s*[axye]\s*\d+\s+(\w+)', query.lower())
    if match:
        dimension = int(match.group(1))
        category_keyword = match.group(2)
        category = self._map_keyword_to_category(category_keyword)
        return dimension, category
    
    return None, None
```

### 3. New Keyword to Category Mapping

**Method:** `_map_keyword_to_category(keyword: str) -> Optional[str]`

**Purpose:** Kullanıcı kelimelerini (kutu, lama, köşebent) tam kategori adlarına dönüştür

**Mapping:**
```python
CATEGORY_MAPPING = {
    'kutu': 'Standart Kutu',
    'lama': 'Lama',
    'köşebent': 'Köşebent',
    'kosebent': 'Köşebent',
    'boru': 'Standart Boru',
    'u': 'U',
    't': 'T',
    'l': 'L',
    'c': 'C',
    # ... diğer kategoriler
}
```

### 4. New Dimension Search in Category

**Method:** `_search_by_dimension_in_category(dimension: int, category: str, top_k: int = 20) -> str`

**Purpose:** Belirli bir kategoride ölçü araması yap

**Logic:**
```python
def _search_by_dimension_in_category(self, dimension: int, category: str, top_k: int = 20) -> str:
    """
    Belirli bir kategoride ölçü araması yap
    
    Args:
        dimension: Ölçü değeri (örn: 30)
        category: Kategori adı (örn: "Köşebent")
        top_k: Maksimum sonuç sayısı
        
    Returns:
        Formatlanmış cevap
    """
    from services.catalog_service import catalog_service
    
    # 1. Kategorideki tüm profilleri al
    profiles = catalog_service.get_profiles_by_category(category)
    
    # 2. Ölçü filtresi uygula (dimension değerini içeren profiller)
    matching_profiles = []
    for profile in profiles:
        # Profil açıklamasında veya kodunda dimension değeri var mı?
        # Örn: "30x30", "30x20", "30 mm"
        if self._profile_contains_dimension(profile, dimension):
            matching_profiles.append(profile)
    
    # 3. Sonuçları formatla
    if not matching_profiles:
        return self._suggest_nearby_search(dimension, category)
    
    return self._format_dimension_search_results(matching_profiles, dimension, category)
```

### 5. Improved Connection Code Search

**Method:** `_search_by_connection_code(query: str) -> Optional[str]`

**Changes:**
- Profil varyantları bulunduğunda açık açıklama ekle
- "LR-3101, LR-3101-1 ve LR-3101-2 profillerinin birleşimidir" formatı

**Logic:**
```python
def _search_by_connection_code(self, query: str) -> Optional[str]:
    # ... mevcut kod ...
    
    # Profil varyantları bulundu
    if profile_variants:
        variant_codes = [p.get('code') for p in profile_variants]
        
        # YENİ: Açık açıklama
        answer_parts = [
            f"**{connection_code}** bir birleşim kodudur.\n",
            f"**{connection_code}**, {' ve '.join(variant_codes)} profillerinin birleşimidir.\n",
            f"**Sistem:** {system['name']}\n",
            f"**Birleşen Profiller:** {len(profile_variants)} profil\n"
        ]
        
        # ... profil detayları ...
```

### 6. Profile Dimension Check

**Method:** `_profile_contains_dimension(profile: Dict, dimension: int) -> bool`

**Purpose:** Profilin belirli bir ölçüyü içerip içermediğini kontrol et

**Logic:**
```python
def _profile_contains_dimension(self, profile: Dict, dimension: int) -> bool:
    """
    Profilin belirli bir ölçüyü içerip içermediğini kontrol et
    
    Args:
        profile: Profil dictionary'si
        dimension: Ölçü değeri (örn: 30)
        
    Returns:
        True ise profil bu ölçüyü içeriyor
    """
    import re
    
    # Profil kodu ve açıklamasında ara
    code = profile.get('code', '')
    description = profile.get('description', '')
    
    # Pattern 1: "30x30", "30x20", "30 x 40"
    pattern1 = rf'\b{dimension}\s*[xX]\s*\d+'
    
    # Pattern 2: "30 mm", "30mm"
    pattern2 = rf'\b{dimension}\s*mm'
    
    # Pattern 3: Sadece sayı (30)
    pattern3 = rf'\b{dimension}\b'
    
    text = f"{code} {description}"
    
    if re.search(pattern1, text) or re.search(pattern2, text) or re.search(pattern3, text):
        return True
    
    return False
```

## Data Models

### Category Mapping
```python
CATEGORY_MAPPING = {
    # Standart kategoriler
    'kutu': 'Standart Kutu',
    'lama': 'Lama',
    'köşebent': 'Köşebent',
    'kosebent': 'Köşebent',
    'boru': 'Standart Boru',
    
    # Şekilsel kategoriler
    'u': 'U',
    't': 'T',
    'l': 'L',
    'c': 'C',
    'h': 'H',
    'v': 'V',
    's': 'S',
    'f': 'F',
    'd': 'D',
    'm': 'M',
    'k': 'K',
    'r': 'R',
    
    # Özel kategoriler
    'daire': 'DAİRE',
    'dairesel': 'DAİRE',
    'küpeşte': 'KÜPEŞTE',
    'kupeşte': 'KÜPEŞTE',
}
```

### Dimension Search Result
```python
{
    "dimension": 30,
    "category": "Köşebent",
    "profiles": [
        {
            "code": "AP0001",
            "description": "30x30 Köşebent",
            "categories": ["Köşebent"],
            "customer": "Beymetal"
        },
        # ... diğer profiller
    ],
    "nearby_suggestion": {
        "min": 27,
        "max": 33,
        "message": "±3 aralığında aramak ister misiniz?"
    }
}
```

## Error Handling

### No Profiles Found in Category
- **Scenario:** Kategoride belirtilen ölçüde profil yok
- **Handling:** Yakın değer araması öner
- **Message:** "30 köşebent bulunamadı. ±3 aralığında aramak ister misiniz?"

### Invalid Category Keyword
- **Scenario:** Kullanıcı bilinmeyen kategori kelimesi kullanıyor
- **Handling:** Genel arama yap
- **Message:** "Kategori bulunamadı, genel arama yapılıyor..."

### Multiple Category Matches
- **Scenario:** "kutu" kelimesi birden fazla kategoriyle eşleşiyor
- **Handling:** En spesifik kategoriyi seç (öncelik sırası)
- **Priority:** Tam eşleşme > Standart kategori > Diğer

### Connection Code Without Variants
- **Scenario:** Birleşim kodu bulundu ama profil varyantları yok
- **Handling:** Mevcut inner/middle/outer profilleri göster
- **Message:** "LR-3101 bir birleşim kodudur. Sistem: LR-3100 SİSTEMİ"

## Testing Strategy

### Unit Tests

**Test 1: Category Extraction - Single Word**
- Input: "kutu"
- Expected: ["Standart Kutu"]
- Not: ["Dairesel Kutu", "Köşebent"]

**Test 2: Category Extraction - Multi Word**
- Input: "dairesel kutu"
- Expected: ["Dairesel Kutu"]

**Test 3: Dimension and Category Extraction**
- Input: "30 köşebent"
- Expected: (30, "Köşebent")

**Test 4: Dimension Search in Category**
- Input: dimension=30, category="Köşebent"
- Expected: Profiller (30x30, 30x20, 30x40 köşebentler)

**Test 5: Connection Code Explanation**
- Input: "LR3101 nedir"
- Expected: "LR-3101, LR-3101-1 ve LR-3101-2 profillerinin birleşimidir"

**Test 6: Keyword to Category Mapping**
- Input: "lama"
- Expected: "Lama"
- Input: "köşebent"
- Expected: "Köşebent"

### Integration Tests

**Test 1: Full Query - Dimension in Category**
- Query: "30 köşebent"
- Expected: 30x30, 30x20 köşebentler gösterilmeli
- Verify: Sadece Köşebent kategorisinden sonuçlar

**Test 2: Full Query - Category Only**
- Query: "kutu"
- Expected: Sadece "Standart Kutu" kategorisinden sonuçlar
- Verify: "Dairesel Kutu" veya "Köşebent" yok

**Test 3: Full Query - Connection Code**
- Query: "LR3101 nedir"
- Expected: Birleşim açıklaması + profil varyantları
- Verify: "LR-3101-1 ve LR-3101-2'nin birleşimi" metni var

**Test 4: Nearby Search Suggestion**
- Query: "99 köşebent" (bulunamaz)
- Expected: Yakın değer önerisi
- Verify: "±3 aralığında aramak ister misiniz?" metni var

### Manual Testing Scenarios

1. "kutu" → Sadece Standart Kutu kategorisi
2. "30 köşebent" → 30x30, 30x20 köşebentler
3. "6 lama" → 6mm lamalar
4. "LR3101 nedir" → "LR-3101, LR-3101-1 ve LR-3101-2'nin birleşimidir"
5. "100 kutu" → 100x100, 100x50 kutular + yakın değer önerisi

## Implementation Notes

### Priority Order for Category Matching

1. **Exact Match (Tam Eşleşme)**: "Standart Kutu" = "Standart Kutu"
2. **Keyword Match (Kelime Eşleşmesi)**: "kutu" → CATEGORY_MAPPING["kutu"] = "Standart Kutu"
3. **Partial Match (Kısmi Eşleşme)**: "dairesel" → "Dairesel Kutu"
4. **Fallback (Genel Arama)**: Kategori bulunamazsa genel arama

### Dimension Search Logic

1. Kategorideki tüm profilleri al
2. Profil kodu/açıklamasında dimension değerini ara
3. Regex pattern matching kullan (30x30, 30mm, 30 gibi)
4. Sonuçları formatla
5. Bulunamazsa yakın değer öner

### Connection Code Explanation Format

```
**LR-3101** bir birleşim kodudur.
**LR-3101**, LR-3101-1 ve LR-3101-2 profillerinin birleşimidir.

**Sistem:** LR-3100 SİSTEMİ

**Birleşen Profiller:** 2 profil

**1. LR-3101-1**
![LR-3101-1](http://localhost:8001/api/profile-image/LR-3101-1)
Kategoriler: Çift Ray Sürme Kasa Profili

**2. LR-3101-2**
![LR-3101-2](http://localhost:8001/api/profile-image/LR-3101-2)
Kategoriler: Çift Ray Sürme Kasa Profili
```

### Backward Compatibility

- Mevcut kategori aramaları çalışmaya devam edecek
- Mevcut ölçü aramaları etkilenmeyecek
- Sadece iyileştirmeler eklenecek
- API değişikliği yok
