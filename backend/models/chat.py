from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class ChatMessage(BaseModel):
    """Chat mesajı"""
    role: str = Field(..., description="Mesaj rolü: 'user' veya 'assistant'")
    content: str = Field(..., description="Mesaj içeriği")


class ChatRequest(BaseModel):
    """Chat isteği"""
    message: str = Field(..., description="Kullanıcı mesajı")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=[],
        description="Konuşma geçmişi (opsiyonel)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "çap 28 profil nedir?",
                "conversation_history": []
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
    context: List[ProfileContext] = Field(..., description="Kullanılan profiller")
    processing_time: float = Field(..., description="İşlem süresi (saniye)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "AP0002 profilini buldum...",
                "context": [
                    {
                        "code": "AP0002",
                        "category": "STANDART BORU",
                        "dimensions": {"Ø": 28.0, "K": 1.0},
                        "match_reason": "Çap: 28.0mm"
                    }
                ],
                "processing_time": 0.123
            }
        }
