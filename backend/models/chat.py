from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class ChatMessage(BaseModel):
    """Chat mesajı"""
    role: str = Field(..., description="Mesaj rolü: 'user' veya 'assistant'")
    content: str = Field(..., description="Mesaj içeriği")


class ChatRequest(BaseModel):
    """Chat isteği"""
    message: str = Field(..., description="Kullanıcı mesajı")
    conversation_history: Optional[List[Dict]] = Field(
        default=None,
        description="Önceki konuşma geçmişi (OpenAI format)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "çap 28 profil nedir?",
                "conversation_history": [
                    {"role": "system", "content": "Sen ALUNA..."},
                    {"role": "user", "content": "30x30 kutu profil"},
                    {"role": "assistant", "content": "AP0123 buldum..."}
                ]
            }
        }


class ProfileContext(BaseModel):
    """Profil context bilgisi"""
    code: str = Field(..., description="Profil kodu")
    category: str = Field(..., description="Kategori")
    dimensions: Dict[str, float] = Field(..., description="Ölçüler")
    match_reason: Optional[str] = Field(None, description="Eşleşme sebebi")


class ChatResponse(BaseModel):
    """Chat cevabı"""
    message: str = Field(..., description="Asistan cevabı")
    conversation_history: List[Dict] = Field(
        ...,
        description="Güncellenmiş conversation history (frontend'e geri gönderilir)"
    )
    processing_time: float = Field(..., description="İşlem süresi (saniye)")
    metadata: Optional[Dict] = Field(
        default=None,
        description="LLM kullanım metadata'sı"
    )
    profile_data: Optional[List[Dict]] = Field(
        default=None,
        description="Profil verileri (load more için)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "AP0002 profilini buldum...",
                "conversation_history": [
                    {"role": "system", "content": "Sen ALUNA..."},
                    {"role": "user", "content": "çap 28 profil"},
                    {"role": "assistant", "content": "AP0002 profilini buldum..."}
                ],
                "processing_time": 0.123,
                "metadata": {
                    "llm_used": True,
                    "tokens_used": 234,
                    "model": "llama-3.3-70b-versatile",
                    "tool_calls_made": 1
                }
            }
        }
