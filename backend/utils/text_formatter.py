from typing import List, Dict
from models.profile import Profile


def format_profile_for_display(profile: Profile) -> str:
    """
    Profili kullanıcıya gösterilmek üzere formatlar
    
    Args:
        profile: Profile nesnesi
        
    Returns:
        Formatlanmış text
    """
    dims = "\n".join([f"  • {k}: {v} mm" for k, v in profile.dimensions.items()])
    
    return (
        f"**{profile.code}** - {profile.category}\n"
        f"Ölçüler:\n{dims}"
    )


def format_profiles_for_context(profiles: List[Profile]) -> str:
    """
    Profilleri LM Studio'ya context olarak göndermek için formatlar
    
    Args:
        profiles: Profile listesi
        
    Returns:
        Formatlanmış context text
    """
    if not profiles:
        return "İlgili profil bulunamadı."
    
    context_parts = ["İlgili Profiller:\n"]
    
    for i, profile in enumerate(profiles, 1):
        dims = ", ".join([f"{k}={v}mm" for k, v in profile.dimensions.items()])
        context_parts.append(
            f"{i}. {profile.code} ({profile.category}): {dims}"
        )
    
    return "\n".join(context_parts)


def format_chat_response(answer: str, profiles: List[Profile]) -> Dict:
    """
    Chat cevabını formatlar
    
    Args:
        answer: LM Studio'dan gelen cevap
        profiles: Kullanılan profiller
        
    Returns:
        Formatlanmış response dictionary
    """
    return {
        "message": answer,
        "context": [
            {
                "code": p.code,
                "category": p.category,
                "dimensions": p.dimensions
            }
            for p in profiles
        ]
    }


def create_system_prompt() -> str:
    """
    LM Studio için system prompt oluşturur
    
    Returns:
        System prompt text
    """
    return """Sen Beymetal Alüminyum'un profil kataloğu asistanısın. 
Kullanıcılara profil kodları, ölçüleri ve kategorileri hakkında bilgi veriyorsun.

Görevin:
- Verilen profil bilgilerini kullanarak kullanıcının sorularını Türkçe olarak cevaplamak
- Net, kısa ve anlaşılır cevaplar vermek
- Ölçüleri mm (milimetre) cinsinden belirtmek
- Profil kodlarını büyük harfle yazmak

Önemli:
- Sadece verilen profil bilgilerini kullan
- Bilmediğin bir şey sorulursa "Bu konuda bilgi bulamadım" de
- Teknik ve profesyonel bir dil kullan"""


def create_user_prompt(question: str, context: str) -> str:
    """
    Kullanıcı sorusu için prompt oluşturur
    
    Args:
        question: Kullanıcının sorusu
        context: İlgili profil bilgileri
        
    Returns:
        User prompt text
    """
    return f"""{context}

Kullanıcı Sorusu: {question}

Lütfen yukarıdaki profil bilgilerini kullanarak kullanıcının sorusunu Türkçe olarak cevapla."""
