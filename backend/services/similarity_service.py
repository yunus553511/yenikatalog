"""Similarity Service - Benzerlik API ile entegrasyon"""
import logging
import aiohttp
from typing import List, Dict, Optional, Any
import re

logger = logging.getLogger(__name__)


class SimilarityService:
    """Benzerlik API'si ile iletişimi yöneten servis"""
    
    def __init__(self, api_url: str = None):
        # Config'den al veya default kullan
        if api_url is None:
            from config import settings
            api_url = settings.similarity_api_url
        self.api_url = api_url
        self.session = None
        self.available = False
    
    async def initialize(self):
        """Servisi başlat ve API durumunu kontrol et"""
        try:
            self.session = aiohttp.ClientSession()
            
            # Health check
            async with self.session.get(f"{self.api_url}/health", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    self.available = data.get("status") == "healthy"
                    if self.available:
                        logger.info(f"✅ Similarity API bağlantısı kuruldu: {data.get('indexed_profiles')} profil indexlenmiş")
                    else:
                        logger.warning("⚠️ Similarity API sağlıksız durumda")
                else:
                    self.available = False
                    logger.warning(f"⚠️ Similarity API health check başarısız: {response.status}")
                    
        except Exception as e:
            self.available = False
            logger.warning(f"⚠️ Similarity API'ye bağlanılamadı: {e}")
    
    async def close(self):
        """Servisi kapat"""
        if self.session:
            await self.session.close()
    
    async def find_similar_profiles(self, profile_code: str, top_k: int = 30) -> Optional[Dict]:
        """Benzer profilleri bul
        
        Args:
            profile_code: Profil kodu (örn: "LR3104", "A 3703")
            top_k: Döndürülecek benzer profil sayısı
            
        Returns:
            Benzer profiller listesi veya None
        """
        if not self.available:
            return None
        
        try:
            # Profil kodunu normalize et (LR-3104 -> LR3104 gibi)
            normalized_code = self._normalize_profile_code(profile_code)
            
            async with self.session.get(
                f"{self.api_url}/api/similar/{normalized_code}",
                params={"top_k": top_k},
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ {profile_code} için {data['count']} benzer profil bulundu")
                    return data
                elif response.status == 404:
                    logger.warning(f"❌ Profil bulunamadı: {profile_code}")
                    return {"error": f"{profile_code} kodlu profil bulunamadı"}
                else:
                    logger.error(f"❌ Similarity API hatası: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Benzerlik arama hatası: {e}")
            return None
    
    def _normalize_profile_code(self, code: str) -> str:
        """Profil kodunu normalize et
        
        LR-3104 -> LR3104
        LR 3104 -> LR3104
        lr3104 -> LR3104
        A 3703 -> A 3703 (boşluklu olanları koru)
        """
        # Küçük harfleri büyük harfe çevir
        code = code.upper().strip()
        
        # LR- veya GL- ile başlıyorsa tireyi kaldır
        if code.startswith(('LR-', 'GL-')):
            code = code[:2] + code[3:]
        
        # LR veya GL ile başlıyorsa ve boşluk varsa kaldır
        if code.startswith(('LR ', 'GL ')):
            code = code[:2] + code[3:]
        
        return code
    
    def parse_similarity_request(self, message: str, conversation_history: list = None) -> Optional[Dict]:
        """Kullanıcı mesajından benzerlik isteğini parse et
        
        Args:
            message: Kullanıcı mesajı
            conversation_history: Önceki mesajlar (profil kodu almak için)
        
        Returns:
            {
                "type": "similarity",
                "profile_code": "LR3104",
                "count": 30
            }
            veya None
        """
        message_lower = message.lower()
        
        # Benzerlik ile ilgili anahtar kelimeler
        similarity_keywords = ['benzer', 'benzeri', 'benzerleri', 'benzeyen', 'gibi', 'similar', 'like', 'benzer profil']
        
        # Mesajda benzerlik anahtar kelimesi var mı?
        if not any(keyword in message_lower for keyword in similarity_keywords):
            return None
        
        # Profil kodunu bul
        # Paternler: LR3104, LR-3104, GL3100, A 3703, AP0001 vb.
        patterns = [
            r'(LR[\s-]?\d{4}(?:-\d+)?)',  # LR3104, LR-3104, LR 3104-1
            r'(GL[\s-]?\d{4}(?:-\d+)?)',  # GL3100, GL-3100
            r'(A\s+\d{4})',                # A 3703
            r'(AP\d{4})',                  # AP0001
            r'([A-Z]{2,}\d{4})',           # Genel: BEYMETAL3104 gibi
            r'([A-Z]+[\s-]?\d{3,4}(?:-\d+)?)'  # Genel pattern
        ]
        
        profile_code = None
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                profile_code = match.group(1)
                break
        
        # Mesajda profil kodu bulunamadıysa, conversation history'den bul
        if not profile_code and conversation_history:
            # Son birkaç mesajı kontrol et (user ve assistant)
            for msg in reversed(conversation_history[-10:]):  # Son 10 mesaj
                content = msg.get('content', '')
                for pattern in patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        profile_code = match.group(1)
                        logger.info(f"Profil kodu conversation history'den bulundu: {profile_code}")
                        break
                if profile_code:
                    break
        
        if not profile_code:
            logger.warning(f"Benzerlik isteği algılandı ama profil kodu bulunamadı: {message}")
            return None
        
        # Sayı bul (kaç tane benzer gösterilecek)
        count = 30  # Varsayılan
        number_match = re.search(r'\b(\d+)\s*(?:tane|adet|benzer|benzeri)?\b', message_lower)
        if number_match:
            count = min(int(number_match.group(1)), 100)  # Max 100 ile sınırla
        
        return {
            "type": "similarity",
            "profile_code": profile_code,
            "count": count
        }
    
    def format_similarity_response(self, data: Dict) -> str:
        """Benzerlik sonuçlarını formatla"""
        if "error" in data:
            return data["error"]
        
        if not data.get("results"):
            return f"{data['query_profile']} için benzer profil bulunamadı."
        
        # Sonuçları grupla (yüksek, orta, düşük benzerlik)
        high_similarity = []
        medium_similarity = []
        low_similarity = []
        
        for result in data["results"]:
            score = result["similarity_score"]
            if score >= 0.8:
                high_similarity.append(result)
            elif score >= 0.6:
                medium_similarity.append(result)
            else:
                low_similarity.append(result)
        
        # Response oluştur
        response = f"🔍 **{data['query_profile']}** için {data['count']} benzer profil bulundu:\n\n"
        
        if high_similarity:
            response += "**🟢 Çok Benzer Profiller:**\n"
            for item in high_similarity[:10]:  # İlk 10 tanesi
                response += f"• {item['profile_code']} (Benzerlik: %{int(item['similarity_score']*100)})\n"
            response += "\n"
        
        if medium_similarity:
            response += "**🟡 Orta Benzerlik:**\n"
            for item in medium_similarity[:10]:
                response += f"• {item['profile_code']} (Benzerlik: %{int(item['similarity_score']*100)})\n"
            response += "\n"
        
        if low_similarity:
            response += "**🔴 Düşük Benzerlik:**\n"
            for item in low_similarity[:10]:
                response += f"• {item['profile_code']} (Benzerlik: %{int(item['similarity_score']*100)})\n"
        
        response += f"\n⚡ İşlem süresi: {data.get('processing_time_ms', 0):.2f}ms"
        
        return response


# Global instance
similarity_service = SimilarityService()
