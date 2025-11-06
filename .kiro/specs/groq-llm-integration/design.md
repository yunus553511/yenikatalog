# Design Document

## Overview

Bu tasarım, Groq LLM'i konuşma yöneticisi olarak kullanır. LLM tüm konuşma geçmişini hatırlar ve gerektiğinde profil aramak için backend API'sini bir araç (tool/function) olarak çağırır.

**Temel Prensipler:**
- LLM konuşma akışını ve context'i yönetir
- Backend API sadece profil arama aracı olarak kullanılır
- LLM, kullanıcı ihtiyacına göre API'yi çağırıp çağırmamaya karar verir
- Conversation history frontend'de veya LLM tarafında tutulur, backend stateless kalır
- Groq'un function calling özelliği kullanılır
- Fallback mekanizması ile sistem her zaman çalışır

## Architecture

### High-Level Flow (YENİ MİMARİ - AI-Driven)

```
User Query + Conversation History
    ↓
Chat Endpoint (/api/chat)
    ↓
LLM Service (Groq API) ← Conversation Manager
    ├── Analyze user query
    ├── Check conversation history
    ├── Decide: Need to search profiles?
    │
    ├─YES─▶ Call "search_profiles" tool
    │         ↓
    │    Tool Call to Backend
    │         ↓
    │    RAG Service (Mevcut)
    │    ├── Connection Query? → Connection Service
    │    ├── Catalog Query? → Catalog Service
    │    └── Standard Query? → Search Service
    │         ↓
    │    Profiles Found (5-15 profil)
    │         ↓
    │    Return to LLM as tool result
    │         ↓
    │    LLM formulates final answer
    │
    └─NO──▶ Answer from conversation context
              (e.g., "Evet, bu profil uygun")
    ↓
Formatted Response + Updated Conversation
    ↓
User (Frontend updates conversation history)
```

**Önemli Fark:**
- Eski: Backend profilleri bulur → LLM formatlar
- Yeni: LLM karar verir → Gerekirse backend'i çağırır → LLM cevaplar

### Component Diagram (YENİ MİMARİ)

```
┌──────────────────────────────────────────────────────────────┐
│                      Frontend (Browser)                       │
├──────────────────────────────────────────────────────────────┤
│  • Manages conversation history (messages array)             │
│  • Sends full history with each request                      │
│  • Displays AI responses and tool calls                      │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Stateless)                │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────┐                                             │
│  │ Chat         │──────────────────┐                          │
│  │ Endpoint     │                  │                          │
│  └──────────────┘                  │                          │
│         │                           ▼                          │
│         │                  ┌─────────────────┐                │
│         │                  │  LLM Service    │                │
│         │                  │  (YENİ)         │                │
│         │                  │                 │                │
│         │                  │ • Conversation  │                │
│         │                  │   Manager       │                │
│         │                  │ • Tool Caller   │                │
│         │                  └────────┬────────┘                │
│         │                           │                          │
│         │                           ▼                          │
│         │                  ┌─────────────────┐                │
│         │                  │ Groq API Client │                │
│         │                  │ (Function Call) │                │
│         │                  └────────┬────────┘                │
│         │                           │                          │
│         │    ┌──────────────────────┘                          │
│         │    │ Tool Call: search_profiles                      │
│         │    │                                                 │
│         ▼    ▼                                                 │
│  ┌──────────────────┐                                          │
│  │  RAG Service     │                                          │
│  │  (Tool Handler)  │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐                                          │
│  │ Search Services  │                                          │
│  │ (Mevcut)         │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐                                          │
│  │ Profiles Found   │                                          │
│  │ (Tool Result)    │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│           └──────────▶ Return to LLM                           │
│                                                                 │
└──────────────────────────────────────────────────────────────┘
                         │
                         ▼
                ┌─────────────────┐
                │   Groq Cloud    │
                │ (Llama 3.1 70B) │
                │ + Function Call │
                └─────────────────┘
```

## Components and Interfaces

### 1. LLM Service (YENİ - AI-Driven Architecture)

**Dosya:** `backend/services/llm_service.py`

**Sorumluluklar:**
- Groq API ile iletişim (function calling ile)
- Conversation history yönetimi (pass-through)
- Tool definitions (search_profiles)
- Tool call execution
- Rate limit ve hata yönetimi
- Fallback mekanizması

**Interface:**

```python
class LLMService:
    """Groq LLM servisi - Conversation Manager"""
    
    def __init__(self, rag_service):
        self.api_key: str
        self.model: str
        self.base_url: str
        self.timeout: int
        self.is_enabled: bool
        self.rag_service = rag_service  # Tool handler
        
    async def chat(
        self,
        messages: List[Dict],  # Full conversation history
        tools: List[Dict] = None  # Tool definitions
    ) -> LLMResponse:
        """
        LLM ile konuşma (function calling ile)
        
        Args:
            messages: OpenAI format conversation history
                [
                    {"role": "system", "content": "..."},
                    {"role": "user", "content": "..."},
                    {"role": "assistant", "content": "..."},
                    {"role": "tool", "content": "...", "tool_call_id": "..."}
                ]
            tools: Tool definitions (search_profiles)
            
        Returns:
            LLMResponse with message or tool_calls
        """
        pass
    
    async def handle_tool_calls(
        self,
        tool_calls: List[Dict]
    ) -> List[Dict]:
        """
        Tool call'ları execute et
        
        Args:
            tool_calls: LLM'den gelen tool call istekleri
            
        Returns:
            Tool results (LLM'e geri gönderilecek)
        """
        pass
    
    def _get_tool_definitions(self) -> List[Dict]:
        """
        Groq function calling format tool definitions
        
        Returns:
            [
                {
                    "type": "function",
                    "function": {
                        "name": "search_profiles",
                        "description": "...",
                        "parameters": {...}
                    }
                }
            ]
        """
        pass
    
    async def _execute_search_profiles(
        self,
        query: str,
        top_k: int = 15
    ) -> Dict:
        """search_profiles tool'unu execute et"""
        pass
    
    def get_stats(self) -> Dict:
        """Kullanım istatistikleri"""
        pass
```

### 2. Groq API Client (YENİ - Function Calling Support)

**Dosya:** `backend/clients/groq_client.py`

**Sorumluluklar:**
- HTTP istekleri (function calling ile)
- Authentication
- Response parsing (tool_calls dahil)
- Error handling

**Interface:**

```python
class GroqClient:
    """Groq API HTTP client with function calling"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.session: aiohttp.ClientSession
        
    async def chat_completion(
        self,
        messages: List[Dict],
        model: str,
        tools: List[Dict] = None,  # YENİ: Tool definitions
        tool_choice: str = "auto",  # YENİ: "auto", "none", or specific tool
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict:
        """
        Chat completion API çağrısı (function calling ile)
        
        Args:
            messages: Conversation history
            model: Model name
            tools: Tool definitions (Groq format)
            tool_choice: Tool selection strategy
            
        Returns:
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "..." OR None,
                            "tool_calls": [  # If LLM wants to call tools
                                {
                                    "id": "call_xxx",
                                    "type": "function",
                                    "function": {
                                        "name": "search_profiles",
                                        "arguments": "{\"query\": \"...\"}"
                                    }
                                }
                            ]
                        }
                    }
                ],
                "usage": {
                    "total_tokens": 234
                }
            }
        """
        pass
    
    async def close(self):
        """Session'ı kapat"""
        pass
```

### 3. RAG Service Güncellemesi (GÜNCELLEME)

**Dosya:** `backend/services/rag_service.py`

**Değişiklikler:**
- `format_direct_answer()` metoduna LLM entegrasyonu ekle
- Fallback mekanizması koru
- Mevcut mantık değişmeyecek

**Yeni Metod:**

```python
async def format_answer_with_llm(
    self,
    query: str,
    top_k: int = 5,
    conversation_history: List[ChatMessage] = None
) -> Tuple[str, Dict]:
    """
    LLM ile cevap oluştur (fallback ile)
    
    Args:
        query: Kullanıcı sorusu
        top_k: Maksimum profil sayısı
        conversation_history: Konuşma geçmişi
        
    Returns:
        (answer, metadata) tuple
        metadata: {
            "llm_used": bool,
            "tokens_used": int,
            "model": str,
            "profiles_count": int
        }
    """
    # 1. Profilleri bul (mevcut mantık)
    # 2. LLM'e gönder
    # 3. Hata durumunda fallback
    pass
```

### 4. Chat Endpoint Güncellemesi (GÜNCELLEME - AI-Driven)

**Dosya:** `backend/main.py`

**Değişiklikler:**
- Conversation history'yi direkt LLM'e gönder
- LLM tool call yapabilir (multi-turn)
- Backend stateless kalır

**Güncellenmiş Endpoint:**

```python
@app.post("/api/chat")
async def chat(request: dict):
    """Chat endpoint - AI-Driven with Function Calling"""
    chat_request = ChatRequest(**request)
    
    start_time = time.time()
    
    try:
        # Conversation history'yi hazırla
        messages = []
        
        # System prompt ekle (sadece ilk mesajsa)
        if not chat_request.conversation_history:
            messages.append({
                "role": "system",
                "content": SYSTEM_PROMPT
            })
        else:
            # Mevcut history'yi kullan
            messages = chat_request.conversation_history
        
        # Yeni kullanıcı mesajını ekle
        messages.append({
            "role": "user",
            "content": chat_request.message
        })
        
        # LLM'e gönder (tool definitions ile)
        llm_response = await llm_service.chat(
            messages=messages,
            tools=llm_service._get_tool_definitions()
        )
        
        # LLM tool call yaptı mı?
        if llm_response.tool_calls:
            # Tool'ları execute et
            tool_results = await llm_service.handle_tool_calls(
                llm_response.tool_calls
            )
            
            # Tool call mesajını history'ye ekle
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": llm_response.tool_calls
            })
            
            # Tool results'ları ekle
            for tool_result in tool_results:
                messages.append({
                    "role": "tool",
                    "content": tool_result["content"],
                    "tool_call_id": tool_result["tool_call_id"]
                })
            
            # LLM'e tekrar gönder (final answer için)
            llm_response = await llm_service.chat(
                messages=messages,
                tools=llm_service._get_tool_definitions()
            )
        
        processing_time = time.time() - start_time
        
        # Response döndür
        return ChatResponse(
            message=llm_response.message,
            conversation_history=messages + [{
                "role": "assistant",
                "content": llm_response.message
            }],  # Updated history
            processing_time=processing_time,
            metadata={
                "llm_used": True,
                "tokens_used": llm_response.tokens_used,
                "model": llm_response.model_used,
                "tool_calls_made": len(llm_response.tool_calls) if llm_response.tool_calls else 0
            }
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

## Data Models

### LLMResponse (YENİ)

**Dosya:** `backend/models/llm.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class LLMResponse(BaseModel):
    """LLM cevap modeli (function calling ile)"""
    
    message: Optional[str] = Field(None, description="LLM'den gelen cevap (tool call yoksa)")
    tool_calls: Optional[List[Dict]] = Field(None, description="LLM'in yapmak istediği tool calls")
    tokens_used: int = Field(0, description="Kullanılan token sayısı")
    model_used: str = Field(..., description="Kullanılan model adı")
    fallback_used: bool = Field(False, description="Fallback kullanıldı mı?")
    error: Optional[str] = Field(None, description="Hata mesajı (varsa)")
```

### ChatRequest Güncellemesi (GÜNCELLEME)

**Dosya:** `backend/models/chat.py`

```python
class ChatRequest(BaseModel):
    """Chat isteği"""
    message: str = Field(..., description="Kullanıcı mesajı")
    conversation_history: Optional[List[Dict]] = Field(  # YENİ
        default=None,
        description="Önceki konuşma geçmişi (OpenAI format)"
    )
    # Örnek:
    # [
    #     {"role": "system", "content": "..."},
    #     {"role": "user", "content": "30x30 kutu profil"},
    #     {"role": "assistant", "content": "...", "tool_calls": [...]},
    #     {"role": "tool", "content": "...", "tool_call_id": "..."},
    #     {"role": "assistant", "content": "AP0123 buldum..."}
    # ]
```

### ChatResponse Güncellemesi (GÜNCELLEME)

**Dosya:** `backend/models/chat.py`

```python
class ChatResponse(BaseModel):
    """Chat cevabı"""
    message: str = Field(..., description="AI'ın cevabı")
    conversation_history: List[Dict] = Field(  # YENİ
        ...,
        description="Güncellenmiş conversation history (frontend'e geri gönderilir)"
    )
    processing_time: float
    metadata: Optional[Dict] = Field(
        default=None,
        description="LLM kullanım metadata'sı"
    )
```

## Configuration

### Environment Variables (YENİ)

**Dosya:** `.env`

```bash
# Groq API Configuration
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.1-70b-versatile
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_TIMEOUT=10
GROQ_TEMPERATURE=0.7
GROQ_MAX_TOKENS=1000

# LLM Feature Flag
LLM_ENABLED=true
```

### Settings Güncellemesi (GÜNCELLEME)

**Dosya:** `backend/config.py`

```python
class Settings(BaseSettings):
    # ... mevcut ayarlar ...
    
    # Groq LLM Configuration (YENİ)
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_timeout: int = 10
    groq_temperature: float = 0.7
    groq_max_tokens: int = 1000
    llm_enabled: bool = True
    
    @property
    def is_llm_available(self) -> bool:
        """LLM kullanılabilir mi?"""
        return self.llm_enabled and bool(self.groq_api_key)
```

## Error Handling

### Error Scenarios

1. **API Key Missing**
   - Durum: `GROQ_API_KEY` tanımlı değil
   - Aksiyon: LLM devre dışı, fallback kullan
   - Log: Warning level

2. **Rate Limit (429)**
   - Durum: Dakikada 30 istek aşıldı
   - Aksiyon: Fallback kullan
   - Log: Warning level
   - Retry: Yok (direkt fallback)

3. **Timeout**
   - Durum: 10 saniye içinde cevap gelmedi
   - Aksiyon: Fallback kullan
   - Log: Warning level

4. **API Error (4xx, 5xx)**
   - Durum: Groq API hatası
   - Aksiyon: Fallback kullan
   - Log: Error level

5. **Network Error**
   - Durum: İnternet bağlantısı yok
   - Aksiyon: Fallback kullan
   - Log: Error level

### Fallback Strategy

```python
async def generate_response_with_fallback(
    query: str,
    context: str,
    history: List[ChatMessage] = None
) -> LLMResponse:
    """LLM ile cevap üret, hata durumunda fallback"""
    
    try:
        # LLM'i dene
        if llm_service.is_enabled:
            response = await llm_service.generate_response(
                query, context, history
            )
            return response
    except RateLimitError:
        logger.warning("Rate limit reached, using fallback")
    except TimeoutError:
        logger.warning("LLM timeout, using fallback")
    except Exception as e:
        logger.error(f"LLM error: {e}, using fallback")
    
    # Fallback: Mevcut format_direct_answer kullan
    fallback_answer = rag_service.format_direct_answer(query)
    
    return LLMResponse(
        message=fallback_answer,
        tokens_used=0,
        model_used="fallback",
        fallback_used=True
    )
```

## Prompt Engineering

### System Prompt (Tool-Aware)

```python
SYSTEM_PROMPT = """Sen ALUNA, Beymetal'in alüminyum profil asistanısın.

Görevin:
- Kullanıcılara profil kodları, ölçüleri ve kategorileri hakkında bilgi vermek
- Gerektiğinde profil aramak için 'search_profiles' aracını kullanmak
- Konuşma geçmişini hatırlayarak doğal sohbet etmek
- Net, kısa ve profesyonel Türkçe cevaplar vermek

Araçların:
- search_profiles: Kullanıcının ihtiyacına göre profil aramak için kullan

Ne Zaman Araç Kullanmalısın:
1. Kullanıcı yeni bir profil sorusu sorduğunda (örn: "30x30 kutu profil")
2. Kullanıcı farklı bir profil istediğinde (örn: "daha kalın olanı var mı?")
3. Kullanıcı spesifik özellikler sorduğunda (örn: "2mm kalınlıkta")

Ne Zaman Araç Kullanmamalısın:
1. Kullanıcı genel soru sorduğunda (örn: "Merhaba", "Teşekkürler")
2. Daha önce bulduğun profiller hakkında soru sorduğunda (örn: "Bu profil uygun mu?")
3. Konuşma geçmişinde zaten cevap varsa

Kurallar:
1. SADECE search_profiles'dan gelen profil bilgilerini kullan
2. Profil kodu, ölçü veya özellik uydurmak YASAK
3. Bilmediğin bir şey sorulursa "Bu konuda bilgi bulamadım" de
4. Ölçüleri mm (milimetre) cinsinden belirt
5. Profil kodlarını büyük harfle yaz (örn: AP0123)
6. Markdown formatı kullan (bold, liste, vb.)
7. Konuşma geçmişini hatırla ve doğal cevaplar ver

Örnek Cevap Formatı:
**AP0123** profilini buldum:

• Kategori: STANDART KUTU
• Ölçüler: 30x30mm
• Kalınlık: 2mm
• Sistem: LR 3100 SİSTEMİ

Bu profil pencere ve kapı sistemlerinde yaygın olarak kullanılır.
"""
```

### Tool Definition (Groq Function Calling Format)

```python
def get_tool_definitions() -> List[Dict]:
    """Groq function calling format tool definitions"""
    
    return [
        {
            "type": "function",
            "function": {
                "name": "search_profiles",
                "description": "Kullanıcının ihtiyacına göre alüminyum profil ara. Profil kodu, ölçü, kategori veya özellik bazlı arama yapar.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Arama sorgusu. Kullanıcının tam isteğini içermeli (örn: '30x30mm kutu profil 2mm kalınlık')"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Maksimum kaç profil döndürülsün (varsayılan: 15)",
                            "default": 15
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]
```

### Tool Result Format

```python
def format_tool_result(profiles: List[Profile]) -> str:
    """Tool result'ı LLM'e geri gönderilecek formatta hazırla"""
    
    if not profiles:
        return "Aramanıza uygun profil bulunamadı."
    
    result_parts = [f"Toplam {len(profiles)} profil bulundu:\n"]
    
    for i, profile in enumerate(profiles, 1):
        result_parts.append(f"\n{i}. **{profile.code}**")
        result_parts.append(f"   - Kategori: {profile.category}")
        result_parts.append(f"   - Ölçüler: {profile.dimensions}")
        if profile.thickness:
            result_parts.append(f"   - Kalınlık: {profile.thickness}mm")
        if profile.system:
            result_parts.append(f"   - Sistem: {profile.system}")
        if profile.image_url:
            result_parts.append(f"   - Görsel: {profile.image_url}")
    
    return "\n".join(result_parts)
```

## Conversation Flow Examples

### Example 1: Simple Query with Tool Call

**User:** "30x30 kutu profil arıyorum"

**Flow:**
```
1. Frontend → Backend:
   POST /api/chat
   {
     "message": "30x30 kutu profil arıyorum",
     "conversation_history": null
   }

2. Backend → Groq LLM:
   messages: [
     {"role": "system", "content": SYSTEM_PROMPT},
     {"role": "user", "content": "30x30 kutu profil arıyorum"}
   ]
   tools: [search_profiles definition]

3. Groq LLM → Backend:
   {
     "tool_calls": [{
       "id": "call_abc123",
       "function": {
         "name": "search_profiles",
         "arguments": "{\"query\": \"30x30 kutu profil\"}"
       }
     }]
   }

4. Backend executes tool:
   results = rag_service.search("30x30 kutu profil")
   tool_result = format_tool_result(results)

5. Backend → Groq LLM (2nd call):
   messages: [
     {"role": "system", "content": SYSTEM_PROMPT},
     {"role": "user", "content": "30x30 kutu profil arıyorum"},
     {"role": "assistant", "tool_calls": [...]},
     {"role": "tool", "content": tool_result, "tool_call_id": "call_abc123"}
   ]

6. Groq LLM → Backend:
   {
     "message": "**AP0123** profilini buldum:\n• Ölçüler: 30x30mm\n..."
   }

7. Backend → Frontend:
   {
     "message": "**AP0123** profilini buldum...",
     "conversation_history": [all messages including tool calls],
     "metadata": {"llm_used": true, "tool_calls_made": 1}
   }
```

### Example 2: Follow-up Question (No Tool Call)

**User:** "Bu profil uygun mu?"

**Flow:**
```
1. Frontend → Backend:
   POST /api/chat
   {
     "message": "Bu profil uygun mu?",
     "conversation_history": [
       {"role": "system", "content": "..."},
       {"role": "user", "content": "30x30 kutu profil arıyorum"},
       {"role": "assistant", "content": "**AP0123** profilini buldum..."}
     ]
   }

2. Backend → Groq LLM:
   messages: [conversation_history + new user message]
   tools: [search_profiles definition]

3. Groq LLM → Backend:
   {
     "message": "Evet, AP0123 profili ihtiyacınıza uygun. 30x30mm ölçülerinde..."
   }
   (NO tool call - LLM answered from context)

4. Backend → Frontend:
   {
     "message": "Evet, AP0123 profili...",
     "conversation_history": [updated with new messages],
     "metadata": {"llm_used": true, "tool_calls_made": 0}
   }
```

### Example 3: Multi-turn Conversation

**Turn 1:**
User: "Merhaba"
AI: "Merhaba! Ben ALUNA, alüminyum profil asistanınızım. Size nasıl yardımcı olabilirim?"
(No tool call)

**Turn 2:**
User: "30x30 kutu profil lazım"
AI: [Calls search_profiles] → "**AP0123** buldum..."

**Turn 3:**
User: "Daha kalın olanı var mı?"
AI: [Calls search_profiles with "30x30 kutu profil kalın"] → "**AP0124** 3mm kalınlıkta..."

**Turn 4:**
User: "Teşekkürler"
AI: "Rica ederim! Başka bir şey için yardıma ihtiyacınız olursa buradayım."
(No tool call)

## Testing Strategy

### Unit Tests

1. **LLM Service Tests**
   - API key validation
   - Prompt generation
   - Error handling
   - Fallback mechanism

2. **Groq Client Tests**
   - HTTP request formatting
   - Response parsing
   - Timeout handling
   - Rate limit detection

3. **RAG Service Tests**
   - LLM integration
   - Fallback behavior
   - Context formatting

### Integration Tests

1. **End-to-End Chat Flow**
   - User query → LLM response
   - Conversation history handling
   - Profile context accuracy

2. **Error Scenarios**
   - Invalid API key
   - Rate limit simulation
   - Network timeout
   - API error responses

### Manual Testing

1. **Türkçe Dil Testi**
   - Türkçe karakterler
   - Doğal dil soruları
   - Konuşma akışı

2. **Performance Testing**
   - Response time (<2 saniye)
   - Token usage tracking
   - Rate limit behavior

## Monitoring and Logging

### Metrics to Track

```python
# LLM Usage Metrics
- Total requests
- Successful LLM calls
- Fallback usage count
- Average tokens per request
- Average response time
- Rate limit hits
- Error count by type

# Example Log Format
logger.info(
    "LLM request completed",
    extra={
        "query": query[:50],
        "tokens_used": 234,
        "model": "llama-3.1-70b-versatile",
        "response_time": 1.23,
        "fallback_used": False
    }
)
```

### Health Check Update

```python
@app.get("/api/health")
async def health_check():
    """Health check with LLM status"""
    
    llm_stats = llm_service.get_stats()
    
    return {
        "status": "healthy",
        "llm_enabled": settings.is_llm_available,
        "llm_stats": llm_stats,
        # ... mevcut health check bilgileri ...
    }
```

## Dependencies

### New Python Packages

```txt
# requirements.txt'e eklenecek
aiohttp==3.9.1          # Async HTTP client
groq==0.4.1             # Groq Python SDK (opsiyonel)
```

**Not:** Groq SDK kullanmak yerine direkt `aiohttp` ile API çağrısı yapabiliriz (daha hafif).

## Security Considerations

1. **API Key Protection**
   - Environment variable'da sakla
   - Loglarda gösterme
   - Git'e commit etme (.env.example kullan)

2. **Rate Limiting**
   - Groq'un limitlerine uy (30 req/min)
   - Fallback ile kullanıcı deneyimini koru

3. **Input Validation**
   - Query length limiti (max 500 karakter)
   - Conversation history limiti (max 5 mesaj)

4. **Error Messages**
   - Kullanıcıya teknik detay verme
   - Generic error messages

## Performance Optimization

1. **Caching**
   - Aynı sorular için cache (opsiyonel, gelecek)
   - TTL: 1 saat

2. **Timeout Management**
   - 10 saniye timeout
   - Hızlı fallback

3. **Token Optimization**
   - Context'i minimize et
   - Sadece gerekli profil bilgilerini gönder
   - Max 1000 token output

4. **Async Operations**
   - Non-blocking LLM calls
   - Concurrent request handling

## Migration Plan

1. **Phase 1: Development**
   - LLM service implementation
   - Unit tests
   - Local testing

2. **Phase 2: Staging**
   - Integration tests
   - Performance testing
   - Türkçe dil testi

3. **Phase 3: Production**
   - Feature flag ile deploy (LLM_ENABLED=false)
   - Gradual rollout
   - Monitor metrics
   - Enable LLM (LLM_ENABLED=true)

4. **Rollback Plan**
   - LLM_ENABLED=false ile devre dışı bırak
   - Fallback otomatik devreye girer
   - Zero downtime
