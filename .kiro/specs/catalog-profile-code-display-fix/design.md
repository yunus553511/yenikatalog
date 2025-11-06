# Design Document

## Overview

Bu tasarım, katalog profillerinin chat yanıtlarında profil kodlarının görünmeme sorununu çözer. Sorun, `CatalogProfile` sınıfının `profile_no` alanını kullanırken, `Profile` sınıfının `code` alanını kullanmasından kaynaklanmaktadır. `text_formatter.py` modülü sadece `Profile` nesnelerini desteklemekte ve `profile.code` alanına erişmeye çalışmaktadır.

## Root Cause Analysis

1. **CatalogProfile.to_dict()** metodu `profile_no` anahtarı döndürür
2. **Profile** sınıfı `code` alanı kullanır
3. **text_formatter.py** fonksiyonları sadece `Profile` nesnelerini kabul eder
4. **RAGService._format_catalog_answer()** fonksiyonu profil kodunu gösterir ancak standart profil aramaları için kullanılan **format_profile_for_display()** fonksiyonu kullanılmaz

## Architecture

### Current Flow (Broken)
```
User Query → RAGService → search_service.search() → Profile objects → text_formatter → Display ✓
User Query → RAGService → catalog_service.search_profiles() → Dict objects → Custom formatting → Display ✓
```

Sorun: İki farklı formatlama yolu var ve tutarsızlık yaratıyor.

### Proposed Solution

**Option 1: Normalize at Data Layer (Recommended)**
- `CatalogProfile.to_dict()` metodunu güncelle
- `profile_no` yerine `code` anahtarı kullan
- Geriye dönük uyumluluk için her ikisini de döndür

**Option 2: Adapter Pattern**
- Text formatter'da tip kontrolü yap
- Hem `Profile` hem `Dict` tiplerini destekle
- Alan adı farklılıklarını handle et

**Seçilen Çözüm: Option 1** - Veri katmanında normalizasyon daha temiz ve sürdürülebilir.

## Components and Interfaces

### 1. CatalogProfile Model Update

**File:** `backend/utils/catalog_parser.py`

**Changes:**
```python
def to_dict(self) -> Dict:
    """Dict'e çevir - Profile ile uyumlu format"""
    return {
        'code': self.profile_no,  # Normalize edilmiş alan
        'profile_no': self.profile_no,  # Geriye dönük uyumluluk
        'customer': self.customer,
        'description': self.description,
        'is_standard': self.is_standard,
        'categories': self.categories,
        'mold_status': 'Kalıp Mevcut' if self.has_mold else 'Kalıp Yok',
        'has_mold': self.has_mold,
        'explanation': self.explanation,
        'category_types': {
            cat: self.get_category_type(cat) 
            for cat in self.categories
        }
    }
```

### 2. Text Formatter Enhancement

**File:** `backend/utils/text_formatter.py`

**Changes:**
- `format_profile_for_display()` fonksiyonunu güncelle
- Hem `Profile` nesnelerini hem de `Dict` tiplerini destekle
- `code` alanına güvenli erişim sağla

```python
def format_profile_for_display(profile) -> str:
    """
    Profili kullanıcıya gösterilmek üzere formatlar
    Hem Profile nesnelerini hem de dict'leri destekler
    """
    # Profile nesnesi mi dict mi?
    if hasattr(profile, 'code'):
        code = profile.code
        category = profile.category
        dimensions = profile.dimensions
    else:
        # Dict formatı
        code = profile.get('code', profile.get('profile_no', 'N/A'))
        category = profile.get('category', ', '.join(profile.get('categories', [])))
        dimensions = profile.get('dimensions', {})
    
    if dimensions:
        dims = "\n".join([f"  • {k}: {v} mm" for k, v in dimensions.items()])
        return f"**{code}** - {category}\nÖlçüler:\n{dims}"
    else:
        # Katalog profili - ölçü yok
        return f"**{code}** - {category}"
```

### 3. RAG Service Consistency

**File:** `backend/services/rag_service.py`

**Changes:**
- `_format_catalog_answer()` metodunu güncelle
- `profile.get('code')` kullan (artık normalize edilmiş)
- Tutarlı formatlama sağla

## Data Models

### Before (Inconsistent)
```python
# Profile
{
    "code": "AP0002",
    "category": "STANDART BORU",
    "dimensions": {"Ø": 28.0}
}

# CatalogProfile
{
    "profile_no": "BM-RAY-001",  # ❌ Farklı alan adı
    "categories": ["Ray"],
    "customer": "Müşteri A"
}
```

### After (Consistent)
```python
# Profile
{
    "code": "AP0002",
    "category": "STANDART BORU",
    "dimensions": {"Ø": 28.0}
}

# CatalogProfile
{
    "code": "BM-RAY-001",  # ✓ Normalize edilmiş
    "profile_no": "BM-RAY-001",  # Geriye dönük uyumluluk
    "categories": ["Ray"],
    "customer": "Müşteri A"
}
```

## Error Handling

1. **Missing Code Field**: Eğer ne `code` ne de `profile_no` varsa, `'N/A'` göster
2. **Type Safety**: `hasattr()` ve `isinstance()` kontrolü ile tip güvenliği sağla
3. **Graceful Degradation**: Ölçü bilgisi yoksa sadece kod ve kategori göster

## Testing Strategy

### Unit Tests
1. `CatalogProfile.to_dict()` metodunun hem `code` hem `profile_no` döndürdüğünü test et
2. `format_profile_for_display()` fonksiyonunun hem `Profile` hem `Dict` tiplerini desteklediğini test et
3. Eksik alan durumlarında graceful degradation'ı test et

### Integration Tests
1. Katalog profili araması yap ve profil kodunun görüntülendiğini doğrula
2. Standart profil araması yap ve profil kodunun hala görüntülendiğini doğrula
3. Karışık arama (hem standart hem katalog) yap ve tutarlı formatlama olduğunu doğrula

### Manual Testing
1. Frontend'de kategori butonuna tıkla
2. Chat yanıtında profil kodlarının göründüğünü doğrula
3. Standart profil ara ve kodların hala göründüğünü doğrula

## Migration Notes

- **Geriye Dönük Uyumluluk**: `profile_no` alanı korunuyor, mevcut kod kırılmayacak
- **API Değişikliği**: Yok - sadece internal data model güncellemesi
- **Database Migration**: Gerekli değil - runtime transformation
