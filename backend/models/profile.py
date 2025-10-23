from pydantic import BaseModel, Field
from typing import Dict, Optional


class Profile(BaseModel):
    """Profil veri modeli"""
    
    code: str = Field(..., description="Profil kodu (örn: AP0002)")
    category: str = Field(..., description="Profil kategorisi (STANDART BORU, KUTU, vb.)")
    dimensions: Dict[str, float] = Field(..., description="Ölçüler (Ø, A, B, K)")
    text_representation: str = Field(..., description="Text formatında profil bilgisi")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "AP0002",
                "category": "STANDART BORU",
                "dimensions": {"Ø": 28.0, "K": 1.0},
                "text_representation": "Profil Kodu: AP0002\nKategori: STANDART BORU\nÖlçüler: Ø=28.0mm, K=1.0mm"
            }
        }
    
    def to_embedding_text(self) -> str:
        """Embedding için text formatına dönüştür"""
        dims = ", ".join([f"{k}={v}mm" for k, v in self.dimensions.items()])
        return (
            f"Profil Kodu: {self.code}\n"
            f"Kategori: {self.category}\n"
            f"Ölçüler: {dims}\n"
            f"Açıklama: Bu profil {self.category} kategorisinde, {dims} ölçülerinde bir alüminyum profildir."
        )
    
    def to_dict(self) -> dict:
        """Dictionary formatına dönüştür"""
        return {
            "code": self.code,
            "category": self.category,
            "dimensions": self.dimensions,
            "text": self.text_representation
        }
