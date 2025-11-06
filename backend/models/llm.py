"""
LLM Response Models
"""
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
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "AP0123 profilini buldum...",
                "tool_calls": None,
                "tokens_used": 234,
                "model_used": "llama-3.3-70b-versatile",
                "fallback_used": False,
                "error": None
            }
        }
