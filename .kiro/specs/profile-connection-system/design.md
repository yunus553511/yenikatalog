# Design Document - Profile Connection System

## Overview

Profil birleşim sistemi, alüminyum profillerin hangi fitillerle birleştiğini gösteren bir özellik sağlar. Sistem, Google Sheets'ten veri çeker, backend'de işler, REST API ile sunar ve frontend'de sidebar + chat bot entegrasyonu ile kullanıcıya sunar.

## Architecture

### High-Level Architecture

```
Google Sheets (Veri Kaynağı)
        ↓
Connection Service (Backend)
        ↓
    Cache Layer
        ↓
    REST API
        ↓
Frontend (Sidebar + Chat Bot)
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Layer                        │
│  ┌──────────────┐              ┌──────────────────────┐ │
│  │   Sidebar    │              │     Chat Widget      │ │
│  │  Component   │              │   (RAG Enhanced)     │ │
│  └──────────────┘              └──────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                        ↓ HTTP/REST
┌─────────────────────────────────────────────────────────┐
│                    Backend Layer                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │         FastAPI Application (main.py)            │   │
│  └──────────────────────────────────────────────────┘   │
│                        ↓                                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │      Connection Service (connection_service.py)  │   │
│  │  - Load from Google Sheets                       │   │
│  │  - Parse Excel data                              │   │
│  │  - Cache management                              │   │
│  │  - Search & filter                               │   │
│  └──────────────────────────────────────────────────┘   │
│                        ↓                                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │      RAG Service Enhancement                     │   │
│  │  - Detect connection queries                     │   │
│  │  - Add connection context to LLM                 │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                    Data Layer                            │
│  ┌──────────────┐              ┌──────────────────────┐ │
│  │ Google       │              │  Local Cache         │ │
│  │ Sheets API   │              │  (connections.xlsx)  │ │
│  └──────────────┘              └──────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Connection Service (Backend)

**File:** `backend/services/connection_service.py`

**Responsibilities:**
- Google Sheets'ten Excel dosyasını indirme
- Excel verilerini parse etme ve yapılandırma
- In-memory cache yönetimi
- Arama ve filtreleme işlemleri

**Key Methods:**

```python
class ConnectionService:
    def __init__(self):
        self.cache_file = "data/cache/connections.xlsx"
        self.sheet_url = "https://docs.google.com/spreadsheets/d/1yeyLrNq6RqenoI-ZYK_wiij6jhHmDrBYil1zn8_AAKg/export?format=xlsx"
        self._data = None  # In-memory cache
        self._last_update = None
    
    async def initialize(self) -> None:
        """Servisi başlat ve verileri yükle"""
        
    async def load_data(self) -> None:
        """Google Sheets'ten veri yükle"""
        
    def parse_excel(self, file_path: str) -> Dict:
        """Excel dosyasını parse et"""
        
    def get_all_systems(self) -> List[Dict]:
        """Tüm sistemleri getir"""
        
    def get_system_by_name(self, system_name: str) -> Dict:
        """Belirli bir sistemi getir"""
        
    def get_profile_connections(self, profile_code: str) -> Dict:
        """Belirli bir profilin birleşim bilgilerini getir"""
        
    def search_connections(self, query: str) -> List[Dict]:
        """Birleşim verilerinde arama yap"""
```

**Data Structure:**

```python
{
    "systems": [
        {
            "name": "LR-3100 SİSTEM",
            "profiles": [
                {
                    "name": "Çift Ray Sürme Kasa Profili",
                    "name_eng": "Sliding Frame Profile",
                    "connection_code": "LR-3101",
                    "inner_profile": "LR-3101-1",
                    "middle_profile": None,
                    "outer_profile": "LR-3102-1",
                    "gaskets": {
                        "barrier_ab_bottom": "P200000",
                        "barrier_ab_top": "P200000",
                        "barrier_bc_bottom": None,
                        "barrier_bc_top": None,
                        "barrier_ac_bottom": None,
                        "barrier_ac_top": None
                    },
                    "weights": {
                        "inner_profile": 0.751,
                        "middle_profile": None,
                        "outer_profile": 0.618,
                        "gasket": 0.141,
                        "total_profile": 1.51,
                        "total_logical": 1.51
                    },
                    "mechanical": {
                        "jx": 33.59,
                        "jy": 9.73,
                        "wx": None,
                        "wy": None
                    },
                    "notes": None
                }
            ]
        }
    ]
}
```

### 2. REST API Endpoints (Backend)

**File:** `backend/main.py` (yeni route'lar eklenecek)

**Endpoints:**

```python
@app.get("/api/connections/systems")
async def get_systems():
    """Tüm sistemleri listele"""
    
@app.get("/api/connections/system/{system_name}")
async def get_system(system_name: str):
    """Belirli bir sistemin detaylarını getir"""
    
@app.get("/api/connections/profile/{profile_code}")
async def get_profile_connections(profile_code: str):
    """Belirli bir profilin birleşim bilgilerini getir"""
    
@app.get("/api/connections/search")
async def search_connections(query: str):
    """Birleşim verilerinde arama yap"""
```

### 3. RAG Service Enhancement (Backend)

**File:** `backend/services/rag_service.py` (mevcut dosyaya eklemeler)

**New Methods:**

```python
def _is_connection_query(self, query: str) -> bool:
    """Sorgunun birleşim ile ilgili olup olmadığını kontrol et"""
    connection_keywords = [
        'fitil', 'birleşim', 'birlesim', 'bağlan', 'baglan',
        'hangi profil', 'hangi fitil', 'birleşim kodu', 
        'birlesim kodu', 'bariyer', 'conta'
    ]
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in connection_keywords)

def _get_connection_context(self, query: str) -> str:
    """Birleşim bilgilerini context olarak hazırla"""
    from services.connection_service import connection_service
    
    # Profil kodunu extract et
    profile_code = self._extract_profile_code(query)
    
    if profile_code:
        connections = connection_service.get_profile_connections(profile_code)
        return self._format_connection_context(connections)
    
    # Genel arama yap
    results = connection_service.search_connections(query)
    return self._format_search_results(results)
```

### 4. Sidebar Component (Frontend)

**File:** `prototype/components/sidebar.js` (yeni dosya)

**Structure:**

```javascript
class ConnectionSidebar {
    constructor() {
        this.isOpen = true;
        this.systems = [];
        this.searchQuery = '';
    }
    
    async init() {
        await this.loadSystems();
        this.render();
        this.attachEventListeners();
    }
    
    async loadSystems() {
        const response = await fetch('/api/connections/systems');
        this.systems = await response.json();
    }
    
    render() {
        // Sidebar HTML'ini oluştur
    }
    
    toggleSidebar() {
        this.isOpen = !this.isOpen;
        // Animasyon ve state yönetimi
    }
    
    filterSystems(query) {
        // Sistemleri filtrele
    }
}
```

**UI Design:**

```
┌─────────────────────────────────────┐
│  🔍 Birleşim Sistemleri Ara...      │
├─────────────────────────────────────┤
│  ▼ LR-3100 SİSTEM                   │
│    ├─ LR-3101 - Çift Ray Sürme     │
│    │   Fitil: P200000               │
│    │   Ağırlık: 1.51 kg/m           │
│    ├─ LR-3102 - Çift Ray İzli      │
│    │   Fitil: P200000               │
│    │   Ağırlık: 1.505 kg/m          │
│  ▼ LR-3200 SİSTEM                   │
│    ├─ ...                            │
├─────────────────────────────────────┤
│  [◀] Gizle                          │
└─────────────────────────────────────┘
```

### 5. Frontend Layout Update

**File:** `prototype/index.html` ve `prototype/style.css`

**Layout Structure:**

```html
<body>
    <!-- Sidebar (Sol) -->
    <aside id="connectionSidebar" class="connection-sidebar">
        <!-- Sidebar içeriği -->
    </aside>
    
    <!-- Main Content (Orta) -->
    <main class="main-content">
        <!-- Mevcut kategori içeriği -->
    </main>
    
    <!-- Chat Widget (Sağ Alt) -->
    <div class="chat-widget">
        <!-- Mevcut chat widget -->
    </div>
</body>
```

**CSS Grid Layout:**

```css
body {
    display: grid;
    grid-template-columns: 300px 1fr;
    grid-template-areas: 
        "sidebar main"
        "sidebar main";
}

.connection-sidebar {
    grid-area: sidebar;
    position: sticky;
    top: 0;
    height: 100vh;
    overflow-y: auto;
}

.main-content {
    grid-area: main;
}

/* Responsive */
@media (max-width: 768px) {
    body {
        grid-template-columns: 1fr;
    }
    
    .connection-sidebar {
        position: fixed;
        transform: translateX(-100%);
        transition: transform 0.3s;
    }
    
    .connection-sidebar.open {
        transform: translateX(0);
    }
}
```

## Data Models

### Connection Data Model

```python
from pydantic import BaseModel
from typing import Optional, List, Dict

class GasketInfo(BaseModel):
    barrier_ab_bottom: Optional[str] = None
    barrier_ab_top: Optional[str] = None
    barrier_bc_bottom: Optional[str] = None
    barrier_bc_top: Optional[str] = None
    barrier_ac_bottom: Optional[str] = None
    barrier_ac_top: Optional[str] = None

class WeightInfo(BaseModel):
    inner_profile: Optional[float] = None
    middle_profile: Optional[float] = None
    outer_profile: Optional[float] = None
    gasket: Optional[float] = None
    total_profile: Optional[float] = None
    total_logical: Optional[float] = None

class MechanicalInfo(BaseModel):
    jx: Optional[float] = None
    jy: Optional[float] = None
    wx: Optional[float] = None
    wy: Optional[float] = None

class ProfileConnection(BaseModel):
    name: str
    name_eng: Optional[str] = None
    connection_code: str
    inner_profile: Optional[str] = None
    middle_profile: Optional[str] = None
    outer_profile: Optional[str] = None
    gaskets: GasketInfo
    weights: WeightInfo
    mechanical: MechanicalInfo
    notes: Optional[str] = None

class ConnectionSystem(BaseModel):
    name: str
    profiles: List[ProfileConnection]
```

## Error Handling

### Backend Error Handling

```python
class ConnectionServiceError(Exception):
    """Base exception for connection service"""
    pass

class DataLoadError(ConnectionServiceError):
    """Excel yükleme hatası"""
    pass

class ParseError(ConnectionServiceError):
    """Excel parse hatası"""
    pass

# Error handling in endpoints
@app.get("/api/connections/systems")
async def get_systems():
    try:
        systems = connection_service.get_all_systems()
        return {"success": True, "data": systems}
    except ConnectionServiceError as e:
        logger.error(f"Connection service error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"success": False, "error": "Internal server error"}
```

### Frontend Error Handling

```javascript
async function loadSystems() {
    try {
        const response = await fetch('/api/connections/systems');
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error);
        }
        
        return data.data;
    } catch (error) {
        console.error('Failed to load systems:', error);
        showErrorMessage('Birleşim sistemleri yüklenemedi. Lütfen daha sonra tekrar deneyin.');
        return [];
    }
}
```

## Testing Strategy

### Unit Tests

1. **Connection Service Tests**
   - Excel parse işlemi
   - Cache yönetimi
   - Arama ve filtreleme
   - Hata senaryoları

2. **RAG Service Tests**
   - Birleşim sorgusu tespiti
   - Context oluşturma
   - Profil kodu extraction

### Integration Tests

1. **API Endpoint Tests**
   - Tüm endpoint'lerin doğru çalışması
   - Error handling
   - Response formatları

2. **Frontend-Backend Integration**
   - Sidebar veri yükleme
   - Chat bot birleşim sorguları
   - Arama fonksiyonalitesi

### Manual Testing Scenarios

1. Sidebar'ı aç/kapa
2. Sistemler arasında arama yap
3. Bir profile tıkla ve detayları gör
4. Chat bot'a "LR-3101 hangi fitil ile birleşir?" sor
5. Mobil responsive testi
6. Cache'in çalıştığını doğrula (network offline)

## Performance Considerations

1. **In-Memory Caching**: Tüm birleşim verileri memory'de tutulacak (hızlı erişim)
2. **Lazy Loading**: Sidebar'da sadece görünen sistemler render edilecek
3. **Debounced Search**: Arama inputu 300ms debounce ile optimize edilecek
4. **Virtual Scrolling**: Çok fazla sistem varsa virtual scrolling kullanılacak
5. **API Response Caching**: Frontend'de API response'ları 5 dakika cache'lenecek

## Security Considerations

1. **API Rate Limiting**: Endpoint'lere rate limit uygulanacak
2. **Input Validation**: Tüm user input'ları validate edilecek
3. **CORS**: Sadece izin verilen origin'lerden erişim
4. **Error Messages**: Hassas bilgi içermeyen generic error mesajları

## Deployment Notes

1. Google Sheets URL'i environment variable olarak saklanacak
2. Cache klasörü deployment'ta oluşturulacak
3. İlk deployment'ta veriler manuel olarak yüklenecek
4. Health check endpoint'i eklenecek (`/api/health`)
