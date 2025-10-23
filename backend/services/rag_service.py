from typing import List, Tuple
import logging

from models.profile import Profile
from services.search_service import search_service
from utils.text_formatter import (
    format_profiles_for_context,
    create_system_prompt,
    create_user_prompt
)

logger = logging.getLogger(__name__)


class RAGService:
    """RAG (Retrieval-Augmented Generation) servisi"""
    
    def prepare_context(self, query: str, top_k: int = 5) -> Tuple[List[Profile], str]:
        """
        Sorgu için context hazırla
        
        Args:
            query: Kullanıcı sorusu
            top_k: Maksimum profil sayısı
            
        Returns:
            (profiles, context_text) tuple
        """
        logger.info(f"RAG context hazırlanıyor: '{query}'")
        
        # Akıllı arama ile profilleri bul
        results = search_service.search(query, top_k=top_k)
        
        if not results:
            logger.warning("Hiç profil bulunamadı")
            return [], "İlgili profil bulunamadı."
        
        # Profilleri ve sebepleri ayır
        profiles = [p for p, _, _ in results]
        
        # Context oluştur (sebepleri de ekle)
        context_parts = ["İlgili Profiller:\n"]
        
        for i, (profile, score, reason) in enumerate(results, 1):
            dims = ", ".join([f"{k}={v}mm" for k, v in profile.dimensions.items()])
            context_parts.append(
                f"{i}. {profile.code} ({profile.category})\n"
                f"   Ölçüler: {dims}\n"
                f"   Eşleşme: {reason}"
            )
        
        context_text = "\n".join(context_parts)
        
        logger.info(f"{len(profiles)} profil context'e eklendi")
        return profiles, context_text
    
    def create_prompt_for_llm(self, query: str, top_k: int = 5) -> Tuple[str, str, List[Profile]]:
        """
        LLM için prompt oluştur
        
        Args:
            query: Kullanıcı sorusu
            top_k: Maksimum profil sayısı
            
        Returns:
            (system_prompt, user_prompt, profiles) tuple
        """
        # Context hazırla
        profiles, context = self.prepare_context(query, top_k)
        
        # System prompt
        system_prompt = create_system_prompt()
        
        # User prompt
        user_prompt = create_user_prompt(query, context)
        
        return system_prompt, user_prompt, profiles
    
    def format_direct_answer(self, query: str, top_k: int = 5) -> str:
        """
        LLM olmadan direkt cevap oluştur (fallback)
        
        Args:
            query: Kullanıcı sorusu
            top_k: Maksimum profil sayısı
            
        Returns:
            Formatlanmış cevap
        """
        results = search_service.search(query, top_k=top_k)
        
        if not results:
            return "Üzgünüm, aramanıza uygun profil bulamadım. Lütfen farklı ölçüler veya kategori deneyin."
        
        # Cevap oluştur
        answer_parts = []
        
        if len(results) == 1:
            profile, score, reason = results[0]
            dims = ", ".join([f"{k}={v}mm" for k, v in profile.dimensions.items()])
            answer_parts.append(
                f"**{profile.code}** profilini buldum:\n\n"
                f"• Kategori: {profile.category}\n"
                f"• Ölçüler: {dims}\n"
                f"• Eşleşme: {reason}"
            )
        else:
            # Kategorileri kontrol et
            categories = set(p.category for p, _, _ in results)
            
            if len(categories) == 1:
                # Tek kategoriden sonuçlar
                category = list(categories)[0]
                answer_parts.append(f"**{category}** kategorisinden **{len(results)} profil** buldum:\n")
            else:
                # Birden fazla kategoriden
                answer_parts.append(f"Aramanıza uygun **{len(results)} profil** buldum:\n")
            
            for i, (profile, score, reason) in enumerate(results, 1):
                dims = ", ".join([f"{k}={v}mm" for k, v in profile.dimensions.items()])
                answer_parts.append(
                    f"\n**{i}. {profile.code}** - {profile.category}\n"
                    f"   Ölçüler: {dims}\n"
                    f"   Eşleşme: {reason}"
                )
        
        return "\n".join(answer_parts)


# Global instance
rag_service = RAGService()
