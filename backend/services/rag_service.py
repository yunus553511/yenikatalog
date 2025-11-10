from typing import List, Tuple, Dict, Optional
import logging

from models.profile import Profile
from services.search_service import search_service
from utils.text_formatter import (
    format_profiles_for_context,
    create_system_prompt,
    create_user_prompt
)
from config import settings

logger = logging.getLogger(__name__)


def is_small_talk(query: str) -> bool:
    """
    Sorgunun genel sohbet (small talk) olup olmadığını kontrol et
    
    Args:
        query: Kullanıcı sorusu
        
    Returns:
        True ise genel sohbet
    """
    query_lower = query.lower().strip()
    
    # Selamlaşma ve genel sohbet kelimeleri
    greetings = [
        'merhaba', 'selam', 'günaydın', 'iyi günler', 'hey', 'hi', 'hello',
        'nasılsın', 'nasılsınız', 'naber', 'nasilsin', 'nasilsiniz',
        'hoş geldin', 'hoşgeldin', 'hos geldin', 'hosgeldin'
    ]
    
    farewells = [
        'görüşürüz', 'hoşça kal', 'güle güle', 'bay', 'bye', 'görüşmek üzere',
        'gorusuruz', 'hosca kal', 'gule gule', 'teşekkür', 'tesekkur', 'sağol', 'sagol'
    ]
    
    questions_about_bot = [
        'kimsin', 'kim sin', 'adın ne', 'adin ne', 'ne yaparsın', 'ne yaparsin',
        'nasıl yardım', 'nasil yardim', 'ne işe yarar', 'ne ise yarar',
        'sen kimsin', 'sen ne', 'nedir bu', 'ne bu', 'yardım et', 'yardim et'
    ]
    
    general_chat = [
        'nasıl gidiyor', 'nasil gidiyor', 'ne var ne yok', 'naber',
        'iyi misin', 'iyi misiniz', 'keyifler nasıl', 'keyifler nasil'
    ]
    
    # Tüm small talk kelimelerini birleştir
    all_small_talk = greetings + farewells + questions_about_bot + general_chat
    
    # Sorgu çok kısa ve small talk kelimesi içeriyorsa
    if len(query_lower.split()) <= 5:
        for keyword in all_small_talk:
            if keyword in query_lower:
                logger.info(f"Small talk detected: '{keyword}' in query")
                return True
    
    # Sadece selamlaşma ise (tek kelime veya çok kısa)
    if query_lower in greetings or query_lower in farewells:
        return True
    
    return False


def is_catalog_query(query: str) -> bool:
    """Sorgunun katalog araması olup olmadığını kontrol et"""
    from services.catalog_service import catalog_service
    import re
    
    query_lower = query.lower()
    
    # ÖNCE: Ölçü bilgisi varsa ASLA katalog araması yapma!
    # Örn: "30 a 30 kutu", "100x50 lama", "çap 28", "50 ye 50 köşebent", "6 lama"
    dimension_patterns = [
        r'\d+\s*[axye]\s*\d+',  # 30x30, 30 a 30, 50 ye 50
        r'\d+\s*mm',            # 30mm
        r'çap\s*\d+',           # çap 28
        r'\d+\s*çap',           # 28 çap
        r'kalınlık',            # kalınlık 2mm
        r'et\s*kalınlığı',      # et kalınlığı
        r'\d+\s+\w+\s+\d+',     # 30 a 30, 50 ye 50
        r'^\d+\s+\w+',          # 6 lama, 100 kutu (başta sayı + kelime)
    ]
    for pattern in dimension_patterns:
        if re.search(pattern, query_lower):
            logger.info(f"Dimension pattern found: {pattern} - Using standard profile search")
            return False  # Standart profil araması yap
    
    # 1. Şekilsel kategori kontrolü (L şeklinde, T şeklinde, U şeklinde gibi)
    shape_pattern = r'[ltucfhvsdmkr]\s+(?:şekl|sekl)'
    if re.search(shape_pattern, query_lower):
        return True
    
    # 2. "daire" özel kontrolü
    if 'daire' in query_lower or 'dairesel' in query_lower:
        return True
    
    # 3. "küpeşte" özel kontrolü
    if 'küpeşte' in query_lower or 'kupeşte' in query_lower or 'küpeste' in query_lower or 'kupeste' in query_lower:
        return True
    
    # 4. "kategorisinde/kategorisindeki" gibi açık kategori belirten kelimeler
    if 'kategorisinde' in query_lower or 'kategorisindeki' in query_lower or 'kategoriden' in query_lower:
        return True
    
    # 5. Tüm katalog kategorilerini kontrol et (dinamik)
    # AMA sadece kategori adı varsa, ölçü yoksa
    try:
        all_categories = catalog_service.get_categories()
        all_cats = []
        for cat_type in ['standard', 'shape', 'sector']:
            categories = all_categories.get(cat_type, [])
            all_cats.extend(categories)
        
        # Türkçe karakter normalizasyonu
        def normalize_turkish(text):
            replacements = {
                'ı': 'i', 'İ': 'i', 'I': 'i',
                'ş': 's', 'Ş': 's',
                'ğ': 'g', 'Ğ': 'g',
                'ü': 'u', 'Ü': 'u',
                'ö': 'o', 'Ö': 'o',
                'ç': 'c', 'Ç': 'c'
            }
            for tr_char, en_char in replacements.items():
                text = text.replace(tr_char, en_char)
            return text.lower()
        
        query_normalized = normalize_turkish(query_lower)
        
        # Normalize edilmiş kategori isimleriyle karşılaştır
        for category in all_cats:
            cat_normalized = normalize_turkish(category)
            # Basit substring match
            if cat_normalized in query_normalized or query_normalized in cat_normalized:
                return True
    except:
        # Catalog servisi henüz hazır değilse, eski yöntemi kullan
        pass
    
    return False


class RAGService:
    """RAG (Retrieval-Augmented Generation) servisi"""
    
    def _is_connection_query(self, query: str) -> bool:
        """
        Sorgunun birleşim ile ilgili olup olmadığını kontrol et
        
        Args:
            query: Kullanıcı sorusu
            
        Returns:
            True ise birleşim sorgusu
        """
        import re
        
        connection_keywords = [
            'fitil', 'birleşim', 'birlesim', 'bağlan', 'baglan',
            'hangi profil', 'hangi fitil', 'birleşim kodu', 
            'birlesim kodu', 'bariyer', 'conta', 'birleşir',
            'birlesir', 'bağlanır', 'baglanir', 'hangi sistemde',
            'gasket', 'barrier', 'sisteminde', 'sistemdeki'
        ]
        
        query_lower = query.lower()
        query_normalized = self._normalize_turkish(query)
        
        # LR/GL profil kodu var mı? (birleşim sistemi profili)
        # LR-3101, LR3101-1, LR-3101-1, GL3201 gibi formatlar
        # SADECE profil kodu varsa (LR3101-1 nedir?) NORMAL ARAMA YAP
        # Ama "fitil", "birleşim" gibi kelimeler varsa connection query
        
        # Önce anahtar kelime kontrolü
        has_connection_keyword = False
        for keyword in connection_keywords:
            keyword_normalized = self._normalize_turkish(keyword)
            if keyword in query_lower or keyword_normalized in query_normalized:
                logger.info(f"Connection query detected: keyword '{keyword}' found")
                has_connection_keyword = True
                break
        
        # Eğer connection keyword varsa, connection query
        if has_connection_keyword:
            return True
        
        # Eğer sadece LR/GL kodu varsa, NORMAL ARAMA (embedding'den bulunacak)
        # Connection query DEĞİL
        return False
    
    def _extract_profile_code(self, query: str) -> str:
        """
        Sorgudan profil kodunu extract et
        
        Args:
            query: Kullanıcı sorusu
            
        Returns:
            Profil kodu veya None
        """
        import re
        
        # LR/GL formatları (Linearossa/Giyotin)
        # LR-3101, LR3101-1, LR-3101-1, GL3201 gibi formatlar
        lr_pattern = r'[LG][LR]-?\d{4}(?:-\d)?'
        match = re.search(lr_pattern, query, re.IGNORECASE)
        if match:
            code = match.group(0).upper()
            logger.info(f"Profile code extracted: {code}")
            return code
        
        # AP veya diğer formatlar (APXXXX, AP0001, vb.)
        ap_pattern = r'AP\d{4,5}'
        match = re.search(ap_pattern, query, re.IGNORECASE)
        if match:
            code = match.group(0).upper()
            logger.info(f"Profile code extracted: {code}")
            return code
        
        logger.debug("No profile code found in query")
        return None
    
    def _search_by_connection_code(self, query: str) -> Optional[str]:
        """
        Birleşim koduna göre arama yap (örn: GLR64-05)
        
        Args:
            query: Kullanıcı sorusu
            
        Returns:
            Formatlanmış birleşim bilgisi veya None
        """
        from services.connection_service import connection_service
        from services.catalog_service import catalog_service
        import re
        
        # Birleşim kodu pattern'i: GLR64-05, LR-3101, vb.
        connection_code_pattern = r'\b([A-Z]{2,3}R?-?\d{2,4}(?:-\d{2})?)\b'
        match = re.search(connection_code_pattern, query.upper())
        
        if not match:
            return None
        
        connection_code = match.group(1)
        
        # Normalize et: LR3101 → LR-3101, GLR6405 → GLR64-05
        # Pattern: LR/GLR + sayılar → LR/GLR-sayılar
        if re.match(r'^(LR|GLR)(\d+)$', connection_code):
            # Tire yok, ekle: LR3101 → LR-3101
            prefix = connection_code[:2] if connection_code.startswith('LR') else connection_code[:3]
            numbers = connection_code[len(prefix):]
            connection_code = f"{prefix}-{numbers}"
        elif re.match(r'^(GLR)(\d{2})(\d{2})$', connection_code):
            # GLR6405 → GLR64-05
            connection_code = f"{connection_code[:5]}-{connection_code[5:]}"
        
        logger.info(f"Birleşim kodu aranıyor (normalized): {connection_code}")
        
        # Tüm sistemleri al ve birleşim kodunu ara
        all_systems = connection_service.get_all_systems()
        
        for system in all_systems:
            for profile in system.get('profiles', []):
                if profile.get('connection_code') == connection_code:
                    # Birleşim kodu bulundu!
                    logger.info(f"Birleşim kodu bulundu: {connection_code} in {system['name']}")
                    
                    # Birleşen profilleri topla
                    profiles_info = []
                    profile_codes = []
                    
                    if profile.get('inner_profile'):
                        profile_codes.append(profile['inner_profile'])
                    if profile.get('middle_profile'):
                        profile_codes.append(profile['middle_profile'])
                    if profile.get('outer_profile'):
                        profile_codes.append(profile['outer_profile'])
                    
                    # Her profil için kategori bilgisini al
                    for code in profile_codes:
                        # Profil kodunu normalize et (sadece ilk tire'yi kaldır)
                        # LR-3101-1 → LR3101-1, LR-3102-1 → LR3102-1
                        # Ama LR3101-1 → LR3101-1 (değişmez)
                        import re
                        normalized_code = re.sub(r'^([A-Z]+)-(\d+)', r'\1\2', code)
                        
                        # Önce normalize edilmiş kod ile dene
                        cat_profile = catalog_service.get_profile_by_no(normalized_code)
                        
                        # Bulunamazsa orijinal kod ile dene
                        if not cat_profile:
                            cat_profile = catalog_service.get_profile_by_no(code)
                        
                        if cat_profile:
                            categories = ', '.join(cat_profile.get('categories', []))
                            image_url = f"{settings.backend_url}/api/profile-image/{code}"
                            profiles_info.append({
                                'code': code,
                                'categories': categories,
                                'image_url': image_url
                            })
                    
                    # Cevap oluştur
                    if len(profiles_info) > 0:
                        # Profiller var - açık açıklama ile göster
                        # Açıklama oluştur: "LR-3101, LR-3101-1 ve LR-3101-2 profillerinin birleşimidir"
                        if len(profiles_info) == 1:
                            explanation = f"**{connection_code}**, {profiles_info[0]['code']} profilinden oluşur."
                        elif len(profiles_info) == 2:
                            explanation = f"**{connection_code}**, {profiles_info[0]['code']} ve {profiles_info[1]['code']} profillerinin birleşimidir."
                        else:
                            # 3 veya daha fazla profil
                            codes = [p['code'] for p in profiles_info]
                            last_code = codes[-1]
                            other_codes = ', '.join(codes[:-1])
                            explanation = f"**{connection_code}**, {other_codes} ve {last_code} profillerinin birleşimidir."
                        
                        answer_parts = [
                            f"**{connection_code}** bir birleşim kodudur.\n",
                            f"{explanation}\n",
                            f"**Sistem:** {system['name']}\n",
                            f"**Birleşen Profiller:** {len(profiles_info)} profil\n"
                        ]
                        
                        for i, prof_info in enumerate(profiles_info, 1):
                            answer_parts.append(f"\n**{i}. {prof_info['code']}**")
                            answer_parts.append(f"![{prof_info['code']}]({prof_info['image_url']})")
                            if prof_info['categories']:
                                answer_parts.append(f"Kategoriler: {prof_info['categories']}")
                        
                        return "\n".join(answer_parts)
                    else:
                        # Profil yok - bu birleşim kodunun hangi profil kodlarından oluştuğunu bul
                        logger.info(f"Birleşim kodunda inner/middle/outer profil yok, profil varyantlarını arıyorum")
                        
                        # Tüm profilleri al
                        all_profiles = catalog_service.get_all_profiles()
                        
                        # LR-3101 → LR-3101-1, LR-3101-2 gibi profil kodlarını ara
                        profile_variants = []
                        
                        for prof in all_profiles:
                            prof_code = prof.get('code', '')
                            # LR-3101 ile başlayan ve suffix'i olan profiller
                            if prof_code.startswith(connection_code + '-'):
                                profile_variants.append(prof)
                        
                        # Tire olmadan da dene: LR3101-1, LR3101-2
                        if not profile_variants:
                            connection_code_no_dash = connection_code.replace('-', '')
                            for prof in all_profiles:
                                prof_code = prof.get('code', '')
                                if prof_code.startswith(connection_code_no_dash + '-'):
                                    profile_variants.append(prof)
                        
                        if profile_variants:
                            # Profil kodlarını topla
                            variant_codes = [prof.get('code') for prof in profile_variants]
                            
                            # Açık açıklama oluştur: "LR-3101, LR-3101-1 ve LR-3101-2 profillerinin birleşimidir"
                            if len(variant_codes) == 1:
                                explanation = f"**{connection_code}**, {variant_codes[0]} profilinden oluşur."
                            elif len(variant_codes) == 2:
                                explanation = f"**{connection_code}**, {variant_codes[0]} ve {variant_codes[1]} profillerinin birleşimidir."
                            else:
                                # 3 veya daha fazla profil
                                last_code = variant_codes[-1]
                                other_codes = ', '.join(variant_codes[:-1])
                                explanation = f"**{connection_code}**, {other_codes} ve {last_code} profillerinin birleşimidir."
                            
                            answer_parts = [
                                f"**{connection_code}** bir birleşim kodudur.\n",
                                f"{explanation}\n",
                                f"**Sistem:** {system['name']}\n",
                                f"**Birleşen Profiller:** {len(profile_variants)} profil\n"
                            ]
                            
                            for i, prof in enumerate(profile_variants, 1):
                                code = prof.get('code')
                                categories = ', '.join(prof.get('categories', []))
                                image_url = f"{settings.backend_url}/api/profile-image/{code}"
                                
                                answer_parts.append(f"\n**{i}. {code}**")
                                answer_parts.append(f"![{code}]({image_url})")
                                if categories:
                                    answer_parts.append(f"Kategoriler: {categories}")
                            
                            return "\n".join(answer_parts)
                        else:
                            # Hiçbir profil bulunamadı
                            return f"**{connection_code}** bir birleşim kodudur.\n\n**Sistem:** {system['name']}\n\nBu birleşim kodunda profil bilgisi bulunmuyor."
        
        return None
    
    def _get_connection_context(self, query: str) -> str:
        """
        Birleşim bilgilerini context olarak hazırla
        
        Args:
            query: Kullanıcı sorusu
            
        Returns:
            Formatlanmış birleşim context'i
        """
        from services.connection_service import connection_service
        
        query_lower = query.lower()
        
        # "sisteminde", "sistemdeki" gibi kelimeler varsa sistem araması yap
        if 'sisteminde' in query_lower or 'sistemdeki' in query_lower or 'sistem' in query_lower:
            # Genel arama yap
            results = connection_service.search_connections(query)
            logger.info(f"System search found {len(results)} results")
            
            if results:
                # Sistem sonuçlarını önceliklendir
                system_results = [r for r in results if r['type'] == 'system']
                if system_results:
                    # İlk sistemin tüm profillerini göster
                    system_name = system_results[0]['system']
                    logger.info(f"Returning system profiles for: {system_name}")
                    system = connection_service.get_system_by_name(system_name)
                    if system:
                        return self._format_system_profiles(system)
                    else:
                        logger.warning(f"System not found: {system_name}")
                
                # Profil sonuçları varsa
                profile_results = [r for r in results if r['type'] == 'profile']
                if profile_results:
                    logger.info(f"Returning {len(profile_results)} profile results")
                    return self._format_search_results(profile_results[:10])
        
        # Profil kodunu extract et
        profile_code = self._extract_profile_code(query)
        
        if profile_code:
            # Profil kodunu normalize et (LR3101-1 → LR-3101)
            normalized_code = self._normalize_profile_code(profile_code)
            logger.info(f"Normalized profile code: {profile_code} → {normalized_code}")
            
            # Belirli bir profil için birleşim bilgisi
            connection = connection_service.get_profile_connections(normalized_code)
            if connection:
                return self._format_connection_context(connection)
        
        # Genel arama yap
        results = connection_service.search_connections(query)
        logger.info(f"Connection search found {len(results)} results")
        
        if results:
            # Profil sonuçlarını filtrele
            profile_results = [r for r in results if r['type'] == 'profile']
            if profile_results:
                logger.info(f"Returning {len(profile_results)} profile results")
                return self._format_search_results(profile_results[:10])  # İlk 10 profil
            
            # Sistem sonuçları varsa
            system_results = [r for r in results if r['type'] == 'system']
            if system_results:
                # İlk sistemin tüm profillerini göster
                system_name = system_results[0]['system']
                logger.info(f"Returning system profiles for: {system_name}")
                system = connection_service.get_system_by_name(system_name)
                if system:
                    return self._format_system_profiles(system)
                else:
                    logger.warning(f"System not found: {system_name}")
        
        logger.warning("No connection results found")
        return ""
    
    def _format_connection_context(self, connection: Dict) -> str:
        """
        Tek bir profil birleşim bilgisini formatla
        
        Args:
            connection: Birleşim dictionary'si
            
        Returns:
            Markdown formatında birleşim bilgisi
        """
        profile = connection['profile']
        system = connection['system']
        
        context_parts = [
            f"## Profil Birleşim Bilgisi\n",
            f"**Sistem:** {system}",
            f"**Profil:** {profile['name']}",
            f"**Birleşim Kodu:** {profile['connection_code']}\n"
        ]
        
        # Profil bileşenleri
        if profile.get('inner_profile'):
            inner_code = profile['inner_profile']
            context_parts.append(f"**İç Profil:** {inner_code}")
            context_parts.append(f"![{inner_code}]({settings.backend_url}/api/profile-image/{inner_code})")
        if profile.get('middle_profile'):
            middle_code = profile['middle_profile']
            context_parts.append(f"**Orta Profil:** {middle_code}")
            context_parts.append(f"![{middle_code}]({settings.backend_url}/api/profile-image/{middle_code})")
        if profile.get('outer_profile'):
            outer_code = profile['outer_profile']
            context_parts.append(f"**Dış Profil:** {outer_code}")
            context_parts.append(f"![{outer_code}]({settings.backend_url}/api/profile-image/{outer_code})")
        
        # Fitiller
        gaskets = profile.get('gaskets', {})
        active_gaskets = {k: v for k, v in gaskets.items() if v}
        if active_gaskets:
            context_parts.append("\n**Fitiller:**")
            for gasket_key, gasket_value in active_gaskets.items():
                gasket_name = gasket_key.replace('_', ' ').title()
                context_parts.append(f"  - {gasket_name}: {gasket_value}")
        
        # Ağırlık bilgileri
        weights = profile.get('weights', {})
        if weights.get('total_profile'):
            context_parts.append(f"\n**Toplam Ağırlık:** {weights['total_profile']} kg/m")
        
        return "\n".join(context_parts)
    
    def _format_search_results(self, results: List[Dict]) -> str:
        """
        Arama sonuçlarını formatla
        
        Args:
            results: Arama sonuçları listesi
            
        Returns:
            Markdown formatında sonuçlar
        """
        if not results:
            return ""
        
        context_parts = ["## İlgili Birleşim Profilleri\n"]
        
        for i, result in enumerate(results, 1):
            if result['type'] == 'profile':
                profile = result['profile']
                system = result['system']
                
                context_parts.append(f"**{i}. {profile['connection_code']}** - {profile['name']}")
                context_parts.append(f"   Sistem: {system}")
                
                # Fitiller
                gaskets = profile.get('gaskets', {})
                active_gaskets = [v for v in gaskets.values() if v]
                if active_gaskets:
                    context_parts.append(f"   Fitiller: {', '.join(set(active_gaskets))}")
                
                context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _format_system_profiles(self, system: Dict) -> str:
        """
        Bir sistemdeki tüm profilleri formatla
        
        Args:
            system: Sistem dictionary'si
            
        Returns:
            Markdown formatında sistem profilleri
        """
        context_parts = [
            f"## {system['name']} Profilleri\n",
            f"Bu sistemde **{len(system['profiles'])} profil** bulunmaktadır:\n"
        ]
        
        for i, profile in enumerate(system['profiles'][:15], 1):  # İlk 15 profil
            context_parts.append(f"**{i}. {profile['connection_code']}** - {profile['name']}")
            
            # Fitiller
            gaskets = profile.get('gaskets', {})
            active_gaskets = [v for v in gaskets.values() if v]
            if active_gaskets:
                context_parts.append(f"   Fitiller: {', '.join(set(active_gaskets))}")
            
            # Ağırlık
            weights = profile.get('weights', {})
            if weights.get('total_profile'):
                context_parts.append(f"   Ağırlık: {weights['total_profile']} kg/m")
            
            context_parts.append("")
        
        if len(system['profiles']) > 15:
            context_parts.append(f"... ve {len(system['profiles']) - 15} profil daha.")
        
        return "\n".join(context_parts)
    
    def _normalize_turkish(self, text: str) -> str:
        """Türkçe karakterleri normalize et (encoding sorunları için)"""
        # Önce büyük harfleri değiştir (lower() çağrılmadan önce!)
        text = text.replace('İ', 'i')  # Türkçe büyük İ → küçük i
        text = text.replace('I', 'ı')  # İngilizce büyük I → Türkçe küçük ı
        
        # Şimdi lowercase yap
        text = text.lower()
        
        # Sonra diğer Türkçe karakterleri normalize et
        replacements = {
            'ı': 'i',  # Türkçe ı → i
            'ş': 's', 
            'ğ': 'g',
            'ü': 'u',
            'ö': 'o',
            'ç': 'c'
        }
        for tr_char, en_char in replacements.items():
            text = text.replace(tr_char, en_char)
        
        # Combining characters'ı temizle (İ'nin lower() sonrası bıraktığı dot)
        import unicodedata
        text = unicodedata.normalize('NFKD', text)
        text = ''.join([c for c in text if not unicodedata.combining(c)])
        
        return text
    
    def _normalize_profile_code(self, code: str) -> str:
        """
        Profil kodunu normalize et (farklı yazım şekillerini standartlaştır)
        
        Args:
            code: Profil kodu (LR3101-1, LR-3101-1, LR 3101-1)
            
        Returns:
            Normalize edilmiş kod (LR-3101)
            
        Examples:
            LR3101-1 → LR-3101
            LR-3101-1 → LR-3101
            LR 3101-1 → LR-3101
            GL3201 → GL-3201
        """
        import re
        
        try:
            # Boşlukları temizle
            code = code.strip().replace(' ', '')
            
            # LR/GL profilleri için (birleşim sistemi profilleri)
            if code.upper().startswith(('LR', 'GL')):
                # Pattern: LR3101-1, LR-3101-1, LR3101 gibi formatlar
                # Hedef: LR-3101-1 (tire ekle ama suffix'i koru)
                match = re.match(r'([A-Z]{2})-?(\d{4})(-\d+)?', code, re.IGNORECASE)
                if match:
                    prefix = match.group(1).upper()
                    number = match.group(2)
                    suffix = match.group(3) or ''  # -1, -2 gibi suffix varsa koru
                    normalized = f"{prefix}-{number}{suffix}"
                    logger.debug(f"Normalized profile code: {code} → {normalized}")
                    return normalized
            
            # Diğer profiller için (AP, vb.) - büyük harfe çevir
            return code.upper()
            
        except Exception as e:
            logger.warning(f"Failed to normalize profile code '{code}': {e}")
            return code.upper()  # Hata durumunda orijinal kodu büyük harfle döndür
    
    def _get_system_info_for_profile(self, profile_code: str) -> Optional[str]:
        """
        Profil kodu için sistem bilgisini al
        
        Args:
            profile_code: Profil kodu (örn: LR3101-1, AP0001)
            
        Returns:
            Sistem adı veya None
            
        Examples:
            LR3101-1 → "LR 3100 SİSTEMİ"
            LR-3201 → "LR 3200 SİSTEMİ"
            AP0001 → None (connection service'te yoksa)
        """
        try:
            from services.connection_service import connection_service
            
            # Profil kodunu normalize et
            normalized_code = self._normalize_profile_code(profile_code)
            logger.debug(f"Getting system info for profile: {profile_code} (normalized: {normalized_code})")
            
            # Connection service'ten profil birleşim bilgisini al
            connection = connection_service.get_profile_connections(normalized_code)
            
            if connection and connection.get('system'):
                system_name = connection['system']
                logger.info(f"System found for profile {profile_code}: {system_name}")
                return system_name
            else:
                logger.debug(f"No system info found for profile: {profile_code}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get system info for profile '{profile_code}': {e}")
            return None
    
    def _get_connection_info_for_profile(self, profile_code: str) -> Optional[Dict]:
        """
        Profil kodu için birleşim bilgilerini al (sistem, birleşim kodu, profiller)
        
        Args:
            profile_code: Profil kodu (örn: GLR64-52)
            
        Returns:
            Birleşim bilgileri dict veya None
            {
                'system': 'GLR 64 SİSTEMİ',
                'connection_code': 'GLR64-05',
                'profiles': ['GLR64-52', 'GLR64-53']
            }
        """
        try:
            from services.connection_service import connection_service
            
            # Profil kodunu normalize et
            normalized_code = self._normalize_profile_code(profile_code)
            
            # Connection service'ten profil birleşim bilgisini al
            connection = connection_service.get_profile_connections(normalized_code)
            
            if not connection:
                return None
            
            profile_data = connection.get('profile', {})
            system_name = connection.get('system')
            connection_code = profile_data.get('connection_code')
            
            if not connection_code:
                return None
            
            # Birleşim kodundaki profilleri topla
            profiles = []
            if profile_data.get('inner_profile'):
                profiles.append(profile_data['inner_profile'])
            if profile_data.get('middle_profile'):
                profiles.append(profile_data['middle_profile'])
            if profile_data.get('outer_profile'):
                profiles.append(profile_data['outer_profile'])
            
            return {
                'system': system_name,
                'connection_code': connection_code,
                'profiles': profiles
            }
                
        except Exception as e:
            logger.error(f"Failed to get connection info for profile '{profile_code}': {e}")
            return None
    
    def _extract_all_categories(self, query: str) -> List[str]:
        """
        Sorgudan TÜM kategorileri extract et (kombinasyon ve tekli aramalar için)
        
        Örnek:
            "daire şeklinde küpeşte" → ['DAİRE', 'KÜPEŞTE']
            "L şeklinde kapak" → ['L', 'KAPAK']
            "küpeşte profilleri" → ['KÜPEŞTE']
            "30x30 lama" → []
        
        Returns:
            Kategori listesi (boş liste = kategori yok)
        """
        from services.catalog_service import catalog_service
        import re
        
        query_lower = query.lower()
        found_categories = []
        
        # Sorguyu temizle - gereksiz kelimeleri kaldır
        noise_words = ['sanırım', 'sanirim', 'galiba', 'herhalde', 'belki', 'gibi', 
                       'varmı', 'var mı', 'var mi', 'varmı?', 'var mı?']
        query_cleaned = query_lower
        for noise in noise_words:
            query_cleaned = query_cleaned.replace(noise, ' ')
        query_cleaned = ' '.join(query_cleaned.split())  # Fazla boşlukları temizle
        
        logger.info(f"Temizlenmiş sorgu: '{query_cleaned}'")
        
        # 1. Tek harfli şekilsel kategorileri kontrol et (L, T, U, etc.)
        shape_letters = ['L', 'T', 'U', 'C', 'H', 'V', 'S', 'F', 'D', 'M', 'K', 'R']
        
        for letter in shape_letters:
            # Pattern 1: "X şeklinde", "X şekl"
            pattern1 = rf'(?:^|\s){letter.lower()}\s+(?:şeklinde|şekl(?!li)|sekl(?!li))'
            # Pattern 2: "şekil X", "şekli X"
            pattern2 = rf'(?:şekil|şekli|sekil|sekli)\s+{letter.lower()}'
            # Pattern 3: "X şekilli"
            pattern3 = rf'(?:^|\s)({letter.lower()})\s+(?:şekilli|sekilli)'
            
            if re.search(pattern1, query_cleaned) or re.search(pattern2, query_cleaned) or re.search(pattern3, query_cleaned):
                if letter not in found_categories:
                    found_categories.append(letter)
                    logger.info(f"Şekilsel kategori bulundu (harf): {letter}")
        
        # 2. Özel durum: "daire", "dairesel", "daire şeklinde" → "DAİRE" kategorisi
        if re.search(r'daire(?:sel|\s+(?:şekl|sekl))', query_cleaned) or 'daire' in query_cleaned:
            all_categories = catalog_service.get_categories()
            for cat_type in ['shape', 'sector']:
                for cat in all_categories.get(cat_type, []):
                    cat_normalized = self._normalize_turkish(cat.lower())
                    if 'daire' in cat_normalized or 'dairesel' in cat_normalized:
                        if cat not in found_categories:
                            found_categories.append(cat)
                            logger.info(f"Şekilsel kategori bulundu (daire): {cat}")
        
        # 3. Özel durum: "küpeşte" → "KÜPEŞTE" kategorisi
        if 'küpeşte' in query_cleaned or 'kupeşte' in query_cleaned or 'küpeste' in query_cleaned or 'kupeste' in query_cleaned:
            all_categories = catalog_service.get_categories()
            for cat_type in ['sector', 'shape', 'standard']:
                for cat in all_categories.get(cat_type, []):
                    cat_normalized = self._normalize_turkish(cat.lower())
                    if 'kupeste' in cat_normalized:
                        if cat not in found_categories:
                            found_categories.append(cat)
                            logger.info(f"Ürün kategorisi bulundu (küpeşte): {cat}")
        
        # 4. Tüm katalog kategorilerini kontrol et (genel eşleşme)
        all_categories = catalog_service.get_categories()
        all_cats = []
        for cat_type in ['standard', 'shape', 'sector']:
            categories = all_categories.get(cat_type, [])
            all_cats.extend(categories)
        
        # Uzunluğa göre sırala (uzun olanlar önce - daha spesifik)
        all_cats.sort(key=len, reverse=True)
        
        # Sorgu içinde geçen kategorileri bul (Türkçe karakter normalizasyonu ile)
        query_normalized = self._normalize_turkish(query_cleaned)
        
        for category in all_cats:
            # Tek harfli şekilsel kategorileri atla (zaten yukarıda pattern ile bulduk)
            if len(category) == 1 and category.isalpha():
                continue
            
            # Türkçe karakter normalizasyonu ile karşılaştır
            cat_normalized = self._normalize_turkish(category)
            
            # İki tür eşleşme:
            # 1. TAM KELİME eşleşmesi (öncelikli)
            # 2. KISMI eşleşme (uzun kategori isimleri için, örn: "güneş kırıcı" → "Güneş Kırıcı Menfez")
            
            # Tam kelime eşleşmesi
            pattern_exact = r'\b' + re.escape(cat_normalized) + r'\b'
            if re.search(pattern_exact, query_normalized):
                if category not in found_categories:
                    found_categories.append(category)
                    logger.info(f"Katalog kategorisi bulundu (tam): {category}")
                    continue
            
            # Kısmi eşleşme (kategori 2+ kelimeden oluşuyorsa)
            cat_words = cat_normalized.split()
            if len(cat_words) >= 2:
                # Sorgu kategorinin ilk N kelimesini içeriyorsa eşleş
                # Örn: "güneş kırıcı" sorgusu → "Güneş Kırıcı Menfez" kategorisi
                query_words = query_normalized.split()
                
                # İlk 2 kelimeyi kontrol et
                first_two_words = ' '.join(cat_words[:2])
                if first_two_words in query_normalized:
                    if category not in found_categories:
                        found_categories.append(category)
                        logger.info(f"Katalog kategorisi bulundu (kısmi - ilk 2 kelime): {category}")
                        continue
                
                # Tek kelime ile eşleşme (kategori içindeki herhangi bir kelime)
                # Örn: "menfez" → "Güneş Kırıcı Menfez"
                for cat_word in cat_words:
                    if len(cat_word) >= 4 and cat_word in query_normalized:  # En az 4 harf
                        if category not in found_categories:
                            found_categories.append(category)
                            logger.info(f"Katalog kategorisi bulundu (kısmi - tek kelime): {category}")
                            break
        
        logger.info(f"Toplam {len(found_categories)} kategori bulundu: {found_categories}")
        return found_categories
    
    
    def _extract_companies_from_query(self, query: str) -> list:
        """
        Sorgudan şirket listesini extract et
        Örn: 
        - "LAMA kategorisindeki profilleri göster (alfore, beymetal şirketleri)"
        - "beymetal şirketi"
        - "alfore profilleri"
        """
        import re
        
        query_lower = query.lower()
        companies = []
        
        # Pattern 1: Parantez içindeki şirket isimleri
        match = re.search(r'\((.*?)\s+şirketleri?\)', query_lower)
        if match:
            companies_str = match.group(1)
            # Virgülle ayrılmış şirketleri parse et
            companies = [c.strip() for c in companies_str.split(',')]
            return companies
        
        # Pattern 2: "beymetal şirketi", "alfore şirketi"
        company_names = ['beymetal', 'alfore', 'linearossa']
        for company in company_names:
            if re.search(rf'{company}\s+(?:şirketi|sirketi|firması|firmas)', query_lower):
                companies.append(company)
        
        # Pattern 3: Sadece şirket ismi geçiyorsa (ama kategori değilse)
        if not companies:
            for company in company_names:
                if company in query_lower:
                    companies.append(company)
        
        return companies if companies else None
    
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
    
    def format_direct_answer(self, query: str, top_k: int = 5, previous_query: Optional[str] = None) -> str:
        """
        LLM olmadan direkt cevap oluştur (fallback)
        
        Args:
            query: Kullanıcı sorusu
            top_k: Maksimum profil sayısı
            previous_query: Önceki sorgu (yakın değer araması için)
            
        Returns:
            Formatlanmış cevap
        """
        import re
        
        # Yakın değer araması mı? (10, 10 lama, 3 kutu gibi)
        range_match = re.match(r'^(\d+)(?:\s+\w+)?$', query.strip())
        if range_match and previous_query:
            range_value = int(range_match.group(1))
            logger.info(f"Yakın değer araması: ±{range_value} (önceki sorgu: {previous_query})")
            return self._search_nearby_dimensions(previous_query, range_value, top_k)
        
        # Birleşim sorgusu mu?
        is_conn_query = self._is_connection_query(query)
        logger.info(f"Is connection query: {is_conn_query}")
        
        if is_conn_query:
            logger.info("Getting connection context...")
            connection_context = self._get_connection_context(query)
            logger.info(f"Connection context length: {len(connection_context)}")
            
            if connection_context:
                logger.info("Returning connection context")
                return connection_context
            else:
                logger.warning("Connection context is empty")
                return "Üzgünüm, bu profil veya birleşim hakkında bilgi bulamadım."
        
        # Katalog araması mı yoksa standart profil araması mı?
        if is_catalog_query(query):
            return self._format_catalog_answer(query, top_k)
        
        results = search_service.search(query, top_k=top_k)
        
        if not results:
            # Profil bulunamadı - ama yakın değer önerisi göster (eğer ölçü araması ise)
            import re
            
            # Önce AxB formatını kontrol et (100x200 gibi)
            axb_match = re.search(r'(\d+)\s*[axye]\s*(\d+)', query.lower())
            
            if axb_match:
                # AxB formatı var - ilk ölçüyü kullan
                dimension_value = int(axb_match.group(1))
                category_match = re.search(r'\d+\s*[axye]\s*\d+\s*(\w+)', query.lower())
                category_keyword = category_match.group(1) if category_match else "profil"
            else:
                # Tek ölçü var mı kontrol et
                dimension_value = self._extract_dimension_value(query)
                category_match = re.search(r'\d+\s*(\w+)', query.lower())
                category_keyword = category_match.group(1) if category_match else "profil"
            
            if dimension_value:
                # STANDART kategorisi mi kontrol et (sadece standart kategorilerde yakın değer önerisi)
                # Basit kontrol: "kutu", "lama", "boru", "köşebent" gibi kelimeler STANDART kategorilerde
                standard_keywords = ['kutu', 'lama', 'boru', 'köşebent', 'kosebent', 'u', 't', 'l', 'c']
                is_standard = any(kw in category_keyword.lower() for kw in standard_keywords)
                
                if is_standard:
                    return (
                        f"Üzgünüm, aramanıza uygun profil bulamadım.\n\n"
                        f"💡 **Yakın değerlerde aramak ister misiniz?**\n"
                        f"Sadece değer girin. Örneğin **3** yazarsanız, **{dimension_value-3} ile {dimension_value+3}** arasındaki {category_keyword.upper()} profillerini gösterebilirim."
                    )
            
            return "Üzgünüm, aramanıza uygun profil bulamadım. Lütfen farklı ölçüler veya kategori deneyin."
        
        # Cevap oluştur
        answer_parts = []
        
        if len(results) == 1:
            profile, score, reason = results[0]
            dims = ", ".join([f"{k}={v}mm" for k, v in profile.dimensions.items()])
            
            # Birleşim bilgisini al
            connection_info = self._get_connection_info_for_profile(profile.code)
            system_info = ""
            
            if connection_info:
                system_name = connection_info['system']
                connection_code = connection_info['connection_code']
                profiles = connection_info['profiles']
                
                system_info = f"• Sistem: {system_name}\n"
                system_info += f"• Birleşim Kodu: {connection_code}\n"
                if len(profiles) > 1:
                    system_info += f"• Birleşen Profiller: {', '.join(profiles)}\n"
            
            # Profil görseli ekle
            image_url = f"{settings.backend_url}/api/profile-image/{profile.code}"
            answer_parts.append(
                f"**{profile.code}** profilini buldum:\n\n"
                f"![{profile.code}]({image_url})\n\n"
                f"• Kategori: {profile.category}\n"
                f"{system_info}"
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
                
                # Birleşim bilgisini al
                connection_info = self._get_connection_info_for_profile(profile.code)
                connection_lines = ""
                
                if connection_info:
                    system_name = connection_info['system']
                    connection_code = connection_info['connection_code']
                    profiles = connection_info['profiles']
                    
                    connection_lines = f"   Sistem: {system_name}\n"
                    connection_lines += f"   Birleşim: {connection_code}"
                    if len(profiles) > 1:
                        connection_lines += f" ({', '.join(profiles)})"
                    connection_lines += "\n"
                
                # Profil görseli ekle
                image_url = f"{settings.backend_url}/api/profile-image/{profile.code}"
                answer_parts.append(
                    f"\n**{i}. {profile.code}** - {profile.category}\n"
                    f"![{profile.code}]({image_url})\n"
                    f"{connection_lines}"
                    f"   Ölçüler: {dims}\n"
                    f"   Eşleşme: {reason}"
                )
        
        # Yakın değer arama önerisi ekle (ölçü araması ise VE STANDART kategori ise)
        dimension_value = self._extract_dimension_value(query)
        if dimension_value and len(results) > 0:
            # Kategoriyi al ve STANDART olup olmadığını kontrol et
            category = results[0][0].category if len(results) > 0 else "profil"
            
            # STANDART kategorileri kontrol et (STANDART LAMA, STANDART KUTU, STANDART KÖŞEBENT, vs.)
            is_standard_category = "STANDART" in category.upper()
            
            if is_standard_category:
                answer_parts.append(
                    f"\n\n💡 **Yakın değerlerde aramak ister misiniz?**\n"
                    f"Sadece değer girin. Örneğin **3** yazarsanız, **{dimension_value-3} ile {dimension_value+3}** arasındaki {category} profillerini gösterebilirim."
                )
        
        return "\n".join(answer_parts)
    
    def _extract_dimension_value(self, query: str) -> Optional[int]:
        """
        Sorgudan ölçü değerini extract et
        
        Args:
            query: Kullanıcı sorusu (örn: "6 lama", "30x30 kutu")
            
        Returns:
            Ölçü değeri (int) veya None
        """
        import re
        
        query_lower = query.lower()
        
        # Pattern 1 (ÖNCELİKLİ): AxB formatı (30x30, 30 a 30, 100 e 200) - AxB varsa tek ölçü DEĞİL
        # Bu durumda None döndür (yakın değer araması yapılmasın)
        match = re.search(r'(\d+)\s*[axye]\s*(\d+)', query_lower)
        if match:
            # İki farklı ölçü varsa (100x200 gibi), None döndür
            dim1 = int(match.group(1))
            dim2 = int(match.group(2))
            if dim1 != dim2:
                return None  # Farklı ölçüler, yakın değer araması yapma
            else:
                return dim1  # Aynı ölçüler (30x30), ilk değeri döndür
        
        # Pattern 2: Çap (çap 28, 28 çap)
        match = re.search(r'(?:çap|cap)\s*(\d+)|(\d+)\s*(?:çap|cap)', query_lower)
        if match:
            return int(match.group(1) or match.group(2))
        
        # Pattern 3: Başta sayı (6 lama, 100 kutu)
        match = re.match(r'^(\d+)\s+\w+', query_lower)
        if match:
            return int(match.group(1))
        
        return None
    
    def _search_nearby_dimensions(self, original_query: str, range_value: int, top_k: int = 20) -> str:
        """
        Yakın ölçülerde arama yap
        
        Args:
            original_query: Orijinal sorgu (örn: "6 lama")
            range_value: Aralık değeri (örn: 3 → ±3)
            top_k: Maksimum profil sayısı
            
        Returns:
            Formatlanmış cevap
        """
        # Orijinal ölçü değerini al
        original_value = self._extract_dimension_value(original_query)
        
        if not original_value:
            return "Üzgünüm, orijinal ölçü değerini bulamadım. Lütfen tekrar arama yapın."
        
        # Aralığı hesapla
        min_value = max(1, original_value - range_value)
        max_value = original_value + range_value
        
        logger.info(f"Yakın değer araması: {min_value}-{max_value} (orijinal: {original_value}, aralık: ±{range_value})")
        
        # Kategoriyi extract et (lama, kutu, boru, vb.)
        import re
        # Pattern: "30 a 30 kutu" → "kutu", "6 lama" → "lama"
        category_match = re.search(r'(?:\d+\s*[axye]\s*\d+\s+)?(\w+)', original_query.lower())
        category_keyword = category_match.group(1) if category_match else ""
        logger.info(f"Kategori keyword: {category_keyword}")
        
        # Orijinal kategoriden profilleri al (kategori filtresi)
        original_results = search_service.search(original_query, top_k=1)
        original_category = None
        if original_results:
            original_category = original_results[0][0].category
            logger.info(f"Orijinal kategori: {original_category}")
        
        # Aralıktaki tüm değerler için arama yap
        all_results = []
        seen_codes = set()
        
        for value in range(min_value, max_value + 1):
            # Yeni sorgu oluştur
            new_query = f"{value} {category_keyword}" if category_keyword else str(value)
            
            # Arama yap
            results = search_service.search(new_query, top_k=50)
            
            if results:
                for profile, score, reason in results:
                    # Kategori filtresi: Sadece orijinal kategoriyle eşleşenleri al
                    if original_category and profile.category != original_category:
                        continue
                    
                    if profile.code not in seen_codes:
                        all_results.append((profile, score, reason, value))
                        seen_codes.add(profile.code)
        
        if not all_results:
            return f"Üzgünüm, **{min_value}-{max_value}** aralığında profil bulamadım."
        
        # Sonuçları ölçüye göre grupla
        from collections import defaultdict
        results_by_dimension = defaultdict(list)
        
        for profile, score, reason, value in all_results:
            results_by_dimension[value].append((profile, score, reason))
        
        # Cevap oluştur
        answer_parts = []
        answer_parts.append(
            f"**{min_value}-{max_value}** aralığında **{len(all_results)} profil** buldum:\n"
        )
        
        # Ölçüye göre sıralı göster
        profile_count = 0
        for dimension_value in sorted(results_by_dimension.keys()):
            profiles = results_by_dimension[dimension_value]
            
            for profile, score, reason in profiles[:5]:  # Her ölçüden max 5 profil
                if profile_count >= top_k:
                    break
                
                profile_count += 1
                dims = ", ".join([f"{k}={v}mm" for k, v in profile.dimensions.items()])
                
                # Profil görseli ekle
                image_url = f"{settings.backend_url}/api/profile-image/{profile.code}"
                answer_parts.append(
                    f"\n**{profile_count}. {profile.code}** - {profile.category}\n"
                    f"![{profile.code}]({image_url})\n"
                    f"   Ölçüler: {dims}\n"
                    f"   Eşleşme: {reason}"
                )
            
            if profile_count >= top_k:
                break
        
        if len(all_results) > profile_count:
            answer_parts.append(f"\n... ve {len(all_results) - profile_count} profil daha.")
        
        return "\n".join(answer_parts)
    
    def _format_categories_with_colors(self, categories: List[str]) -> str:
        """
        Kategorileri renkli HTML span'ler ile formatla
        
        Args:
            categories: Kategori listesi
            
        Returns:
            Renkli HTML formatında kategoriler
        """
        from services.catalog_service import catalog_service
        
        # Tüm kategorileri al
        all_categories = catalog_service.get_categories()
        
        colored_cats = []
        for cat in categories:
            cat_upper = cat.upper()
            
            # Hangi tipte olduğunu bul
            if cat in all_categories.get('standard', []):
                # Standart - Mavi
                colored_cats.append(f'<span style="color: #4a90e2; font-weight: 600;">{cat}</span>')
            elif cat in all_categories.get('shape', []):
                # Şekilsel - Turuncu
                colored_cats.append(f'<span style="color: #e2a44a; font-weight: 600;">{cat}</span>')
            elif cat in all_categories.get('sector', []):
                # Sektörel - Yeşil
                colored_cats.append(f'<span style="color: #4ae2a4; font-weight: 600;">{cat}</span>')
            else:
                # Bilinmeyen - Normal
                colored_cats.append(cat)
        
        return ', '.join(colored_cats)
    def _search_profile_by_code(self, query: str) -> Optional[str]:
        """
        Sorgudan profil kodunu extract edip o profili ara
        
        Args:
            query: Kullanıcı sorusu (örn: "LR3101-1 göster", "AP0028 nedir")
            
        Returns:
            Formatlanmış profil bilgisi veya None
        """
        import re
        from services.catalog_service import catalog_service
        
        # Profil kodu pattern'leri
        # LR/GL formatları: LR-3101, LR3101-1, GL3201
        # AP formatları: AP0028, AP278, AP17382
        # Diğer formatlar: BM-RAY-001, vb.
        patterns = [
            r'\b([LG][LR]-?\d{4}(?:-\d)?)\b',  # LR-3101, LR3101-1, GL3201
            r'\b(AP\d{3,5})\b',                 # AP0028, AP278, AP17382
            r'\b([A-Z]{2,}-[A-Z]+-\d+)\b',     # BM-RAY-001
        ]
        
        query_upper = query.upper()
        
        # Özel durum: LR3101, GLR64 gibi kodlar (suffix yok)
        # Önce birleşim kodu mu kontrol et, değilse profil varyantlarını ara
        base_code_pattern = r'\b([LG][LR]R?-?\d{2,4})\b(?!-\d)'  # LR3101, GLR64 (ama LR3101-1 değil)
        base_match = re.search(base_code_pattern, query_upper)
        
        if base_match:
            base_code = base_match.group(1)
            # Tire ekle: LR3101 → LR-3101
            if not '-' in base_code:
                if base_code.startswith('GLR') and len(base_code) == 7:
                    # GLR6405 → GLR64-05
                    base_code = f"{base_code[:5]}-{base_code[5:]}"
                elif base_code.startswith(('LR', 'GL')):
                    # LR3101 → LR-3101
                    prefix = base_code[:2]
                    numbers = base_code[2:]
                    base_code = f"{prefix}-{numbers}"
            
            logger.info(f"Base kod bulundu: {base_code}, önce birleşim kodu mu kontrol ediliyor...")
            
            # ÖNCE birleşim kodu mu kontrol et
            from services.connection_service import connection_service
            all_systems = connection_service.get_all_systems()
            
            for system in all_systems:
                for profile in system.get('profiles', []):
                    if profile.get('connection_code') == base_code:
                        # Bu bir birleşim kodu! Profil araması yapma, None döndür
                        # Böylece birleşim kodu araması çalışacak
                        logger.info(f"{base_code} bir birleşim kodu, profil araması yapılmıyor")
                        return None
            
            logger.info(f"{base_code} birleşim kodu değil, profil varyantları aranıyor...")
            
            # Tüm profilleri al ve bu base code ile başlayanları bul
            all_profiles = catalog_service.get_all_profiles()
            matching_profiles = []
            
            for prof in all_profiles:
                prof_code = prof.get('code', '')
                # LR-3101-1, LR-3101-2 gibi kodları bul
                if prof_code.startswith(base_code):
                    matching_profiles.append(prof)
            
            # Eğer catalog'da bulunamadıysa, tire olmadan da dene
            if not matching_profiles:
                # LR-3101 → LR3101 (tire kaldır)
                base_code_no_dash = base_code.replace('-', '')
                for prof in all_profiles:
                    prof_code = prof.get('code', '')
                    if prof_code.startswith(base_code_no_dash):
                        matching_profiles.append(prof)
            
            if matching_profiles:
                logger.info(f"{len(matching_profiles)} varyant bulundu")
                # Çoklu profil gösterimi
                answer_parts = [f"**{base_code}** için **{len(matching_profiles)} profil** bulundu:\n"]
                
                for i, prof in enumerate(matching_profiles, 1):
                    code = prof.get('code')
                    categories = prof.get('categories', [])
                    customer = prof.get('customer', '')
                    mold_status = prof.get('mold_status', '')
                    
                    image_url = f"{settings.backend_url}/api/profile-image/{code}"
                    answer_parts.append(f"\n**{i}. {code}**")
                    answer_parts.append(f"![{code}]({image_url})")
                    
                    if categories:
                        colored_categories = self._format_categories_with_colors(categories)
                        answer_parts.append(f"Kategoriler: {colored_categories}")
                    
                    if customer:
                        answer_parts.append(f"Müşteri: {customer}")
                    
                    if mold_status:
                        answer_parts.append(f"Kalıp: {mold_status}")
                
                return "\n".join(answer_parts)
        
        # Normal profil kodu araması (LR3101-1, AP0028 gibi)
        for pattern in patterns:
            match = re.search(pattern, query_upper)
            if match:
                profile_code = match.group(1)
                logger.info(f"Profil kodu bulundu: {profile_code}")
                
                # Katalog servisinden profili ara
                profile = catalog_service.get_profile_by_no(profile_code)
                
                if profile:
                    logger.info(f"Profil bulundu: {profile_code}")
                    return self._format_single_profile(profile)
                else:
                    logger.info(f"Profil bulunamadı: {profile_code}")
        
        return None
    
    def _format_single_profile(self, profile: Dict) -> str:
        """
        Tek bir profili detaylı şekilde formatla
        
        Args:
            profile: Profil dictionary'si
            
        Returns:
            Formatlanmış profil bilgisi
        """
        code = profile.get('code', 'N/A')
        customer = profile.get('customer', '')
        description = profile.get('description', '')
        categories = profile.get('categories', [])
        mold_status = profile.get('mold_status', '')
        explanation = profile.get('explanation', '')
        
        # Profil görseli
        image_url = f"{settings.backend_url}/api/profile-image/{code}"
        
        answer_parts = [
            f"**{code}** profili bulundu:\n",
            f"![{code}]({image_url})\n"
        ]
        
        if categories:
            colored_categories = self._format_categories_with_colors(categories)
            answer_parts.append(f"**Kategoriler:** {colored_categories}")
        
        # Sistem bilgisini al
        system_name = self._get_system_info_for_profile(code)
        if system_name:
            answer_parts.append(f"**Sistem:** {system_name}")
        
        # Bu profilin hangi birleşimlerde kullanıldığını bul
        try:
            from services.connection_service import connection_service
            all_systems = connection_service.get_all_systems()
            used_in_connections = []
            
            logger.info(f"Checking {code} in {len(all_systems)} systems")
            
            # Normalize code: LR3101-1 → LR-3101-1
            normalized_code = self._normalize_profile_code(code)
            logger.info(f"Normalized code: {code} → {normalized_code}")
            
            for sys in all_systems:
                for prof in sys.get('profiles', []):
                    if (prof.get('inner_profile') == normalized_code or 
                        prof.get('middle_profile') == normalized_code or 
                        prof.get('outer_profile') == normalized_code):
                        used_in_connections.append({
                            'connection_code': prof.get('connection_code'),
                            'name': prof.get('name')
                        })
            
            logger.info(f"Found {len(used_in_connections)} connections for {code}")
            
            if used_in_connections:
                answer_parts.append(f"\n**Kullanıldığı Birleşimler:** {len(used_in_connections)} birleşim")
                for conn in used_in_connections[:5]:  # İlk 5 birleşim
                    answer_parts.append(f"  • {conn['connection_code']} - {conn['name']}")
                if len(used_in_connections) > 5:
                    answer_parts.append(f"  ... ve {len(used_in_connections) - 5} birleşim daha")
        except Exception as e:
            logger.error(f"Error getting connection info: {e}")
        
        if customer:
            answer_parts.append(f"\n**Müşteri:** {customer}")
        
        if description:
            answer_parts.append(f"**Açıklama:** {description}")
        
        if mold_status:
            answer_parts.append(f"**Kalıp:** {mold_status}")
        
        if explanation:
            answer_parts.append(f"\n**Detay:**\n{explanation}")
        
        return "\n".join(answer_parts)
    
    def _format_catalog_answer(self, query: str, top_k: int = 20) -> str:
        """
        Katalog araması için cevap oluştur
        
        Args:
            query: Kullanıcı sorusu
            top_k: Maksimum profil sayısı
            
        Returns:
            Formatlanmış cevap
        """
        from services.catalog_service import catalog_service
        
        # Tüm kategorileri extract et
        categories = self._extract_all_categories(query)
        logger.info(f"Extracted categories: {categories}")
        
        # Şirket filtresi extract et
        companies = self._extract_companies_from_query(query)
        logger.info(f"Extracted companies: {companies}")
        
        # Karar ağacı: 2+ kategori → kombinasyon, 1 kategori → tekli, 0 → genel
        if len(categories) >= 2:
            # Kategori kombinasyonu araması
            logger.info(f"Kombinasyon araması yapılıyor: {categories}")
            results = self._search_by_category_combination(categories)
            
            if not results:
                # Kombinasyon bulunamadıysa, genel arama yap
                logger.warning(f"Kombinasyon bulunamadı, genel arama yapılıyor")
                results = catalog_service.search_profiles(query, limit=top_k)
                
                if not results:
                    return f"Üzgünüm, **{' + '.join(categories)}** kombinasyonunda profil bulamadım."
            
            # Cevap oluştur
            answer_parts = []
            answer_parts.append(f"**{' + '.join(categories)}** kombinasyonunda **{len(results)} profil** buldum:\n")
            
            # Profilleri listele
            for i, profile in enumerate(results[:15], 1):
                code = profile.get('code', 'N/A')
                customer = profile.get('customer', '')
                description = profile.get('description', '')
                profile_categories = profile.get('categories', [])
                mold_status = profile.get('mold_status', '')
                
                # Profil görseli ekle
                image_url = f"{settings.backend_url}/api/profile-image/{code}"
                answer_parts.append(f"\n**{i}. {code}**")
                answer_parts.append(f"![{code}]({image_url})")
                
                if profile_categories:
                    colored_categories = self._format_categories_with_colors(profile_categories)
                    answer_parts.append(f"   Kategoriler: {colored_categories}")
                
                # Sistem bilgisini al (Connection Service'ten)
                system_name = self._get_system_info_for_profile(code)
                if system_name:
                    answer_parts.append(f"   Sistem: {system_name}")
                
                if customer:
                    answer_parts.append(f"   Müşteri: {customer}")
                
                if description:
                    answer_parts.append(f"   Açıklama: {description}")
                
                if mold_status:
                    answer_parts.append(f"   Kalıp: {mold_status}")
            
            if len(results) > 15:
                answer_parts.append(f"\n... ve {len(results) - 15} profil daha.")
            
            return "\n".join(answer_parts)
        
        elif len(categories) == 1:
            # Tek kategori araması
            category_name = categories[0]
            logger.info(f"Tek kategori araması yapılıyor: '{category_name}' with companies: {companies}")
            results = catalog_service.get_profiles_by_category(category_name, companies=companies)
            
            if not results:
                return f"Üzgünüm, **{category_name}** kategorisinde profil bulamadım."
            
            # Cevap oluştur
            answer_parts = []
            answer_parts.append(f"**{category_name}** kategorisinden **{len(results)} profil** buldum:\n")
            
            # Profilleri listele
            for i, profile in enumerate(results[:15], 1):
                code = profile.get('code', 'N/A')
                customer = profile.get('customer', '')
                description = profile.get('description', '')
                mold_status = profile.get('mold_status', '')
                
                # Profil görseli ekle
                image_url = f"{settings.backend_url}/api/profile-image/{code}"
                answer_parts.append(f"\n**{i}. {code}**")
                answer_parts.append(f"![{code}]({image_url})")
                
                if customer:
                    answer_parts.append(f"   Müşteri: {customer}")
                
                if description:
                    answer_parts.append(f"   Açıklama: {description}")
                
                if mold_status:
                    answer_parts.append(f"   Kalıp: {mold_status}")
            
            if len(results) > 15:
                answer_parts.append(f"\n... ve {len(results) - 15} profil daha.")
            
            return "\n".join(answer_parts)
        
        else:
            # Genel arama (kategori bulunamadı)
            logger.info("Kategori bulunamadı, genel arama yapılıyor")
            results = catalog_service.search_profiles(query, limit=top_k)
            
            if not results:
                return "Üzgünüm, aramanıza uygun profil bulamadım."
            
            # Eğer tek profil bulunduysa, detaylı göster
            if len(results) == 1:
                return self._format_single_profile(results[0])
            
            # Cevap oluştur
            answer_parts = []
            
            # Sonuçlardaki kategorileri topla
            category_names = set()
            for p in results:
                cats = p.get('categories', [])
                if isinstance(cats, list):
                    category_names.update(cats)
            
            if category_names:
                cat_str = ", ".join(list(category_names)[:3])
                answer_parts.append(f"**{cat_str}** kategorisinden **{len(results)} profil** buldum:\n")
            else:
                answer_parts.append(f"Aramanıza uygun **{len(results)} profil** buldum:\n")
            
            # Profilleri listele
            for i, profile in enumerate(results[:15], 1):
                code = profile.get('code', 'N/A')
                customer = profile.get('customer', '')
                description = profile.get('description', '')
                mold_status = profile.get('mold_status', '')
                profile_categories = profile.get('categories', [])
                
                # Profil görseli ekle
                image_url = f"{settings.backend_url}/api/profile-image/{code}"
                answer_parts.append(f"\n**{i}. {code}**")
                answer_parts.append(f"![{code}]({image_url})")
                
                # Kategorileri göster (renkli)
                if profile_categories:
                    colored_categories = self._format_categories_with_colors(profile_categories)
                    answer_parts.append(f"   Kategoriler: {colored_categories}")
                
                # Sistem bilgisini al (Connection Service'ten)
                system_name = self._get_system_info_for_profile(code)
                if system_name:
                    answer_parts.append(f"   Sistem: {system_name}")
                
                if customer:
                    answer_parts.append(f"   Müşteri: {customer}")
                
                if description:
                    answer_parts.append(f"   Açıklama: {description}")
                
                if mold_status:
                    answer_parts.append(f"   Kalıp: {mold_status}")
            
            if len(results) > 15:
                answer_parts.append(f"\n... ve {len(results) - 15} profil daha.")
            
            return "\n".join(answer_parts)
    
    def _search_by_category_combination(self, categories: List[str]) -> List[Dict]:
        """
        Birden fazla kategoride birden bulunan profilleri ara
        
        Args:
            categories: Kategori listesi (örn: ['KAPAK', 'L'])
            
        Returns:
            Her kategoride de bulunan profiller
        """
        from services.catalog_service import catalog_service
        
        # Tüm profilleri al
        all_profiles = catalog_service.get_all_profiles()
        
        # Her kategoride de bulunan profilleri filtrele
        matching_profiles = []
        
        for profile in all_profiles:
            profile_categories = profile.get('categories', [])
            
            # Profil tüm aranan kategorilerde var mı?
            # Büyük/küçük harf duyarsız karşılaştırma
            profile_cats_upper = [c.upper() for c in profile_categories]
            search_cats_upper = [c.upper() for c in categories]
            
            if all(cat in profile_cats_upper for cat in search_cats_upper):
                matching_profiles.append(profile)
        
        logger.info(f"Kategori kombinasyonu sonucu: {len(matching_profiles)} profil")
        return matching_profiles
    
    async def format_answer_with_llm(
        self,
        query: str,
        top_k: int = 5,
        conversation_history: Optional[List] = None,
        previous_query: Optional[str] = None
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
                "profiles_count": int,
                "fallback_used": bool
            }
        """
        from services.llm_service import llm_service
        from models.chat import ChatMessage
        
        logger.info(f"Formatting answer with LLM: query='{query[:50]}...'")
        
        # 0. Yakın değer araması kontrolü (EN ÖNCE!)
        import re
        range_match = re.match(r'^(\d+)(?:\s+\w+)?$', query.strip())
        if range_match and previous_query:
            logger.info(f"Nearby search detected: {query} (previous: {previous_query})")
            # format_direct_answer'ı çağır, o zaten yakın değer aramasını yapacak
            fallback_answer = self.format_direct_answer(query, top_k, previous_query=previous_query)
            metadata = {
                "llm_used": False,
                "tokens_used": 0,
                "model": "nearby_search",
                "profiles_count": 0,
                "fallback_used": False,
                "query_type": "nearby_search"
            }
            return fallback_answer, metadata
        
        # 1. Small talk kontrolü
        if is_small_talk(query):
            logger.info("Small talk detected, using LLM for friendly response")
            
            # Small talk için özel context
            small_talk_context = """
Sen ALUNA, Beymetal'in alüminyum profil asistanısın.

Kullanıcı seninle genel sohbet ediyor (profil aramıyor).
Samimi, dostça ve profesyonel bir şekilde cevap ver.

Kendini tanıt:
- Adın ALUNA
- Beymetal, Linearossa ve Alfore şirketlerinin alüminyum profil asistanısın
- Kullanıcılara profil aramasında yardımcı oluyorsun
- Ölçü, kategori veya sistem bazlı arama yapabiliyorsun

Kısa ve samimi cevaplar ver. Emoji kullanabilirsin ama abartma.
"""
            
            if llm_service.is_enabled:
                try:
                    llm_response = await llm_service.generate_response(
                        query=query,
                        context=small_talk_context,
                        conversation_history=conversation_history
                    )
                    
                    if not llm_response.fallback_used:
                        metadata = {
                            "llm_used": True,
                            "tokens_used": llm_response.tokens_used,
                            "model": llm_response.model_used,
                            "profiles_count": 0,
                            "fallback_used": False,
                            "query_type": "small_talk"
                        }
                        return llm_response.message, metadata
                except Exception as e:
                    logger.error(f"LLM error in small talk: {e}")
            
            # Fallback: Basit cevaplar
            simple_responses = {
                'merhaba': 'Merhaba! Ben ALUNA, Beymetal profil asistanınızım. Size nasıl yardımcı olabilirim? 😊',
                'selam': 'Selam! Alüminyum profil aramanızda size yardımcı olabilirim. Ne arıyorsunuz?',
                'nasılsın': 'İyiyim, teşekkür ederim! 😊 Size profil aramasında nasıl yardımcı olabilirim?',
                'kimsin': 'Ben ALUNA, Beymetal\'in alüminyum profil asistanıyım. Profil aramanızda size yardımcı oluyorum!',
                'teşekkür': 'Rica ederim! Başka bir konuda yardımcı olabilir miyim? 😊',
            }
            
            query_lower = query.lower().strip()
            for keyword, response in simple_responses.items():
                if keyword in query_lower:
                    metadata = {
                        "llm_used": False,
                        "tokens_used": 0,
                        "model": "small_talk_fallback",
                        "profiles_count": 0,
                        "fallback_used": True,
                        "query_type": "small_talk"
                    }
                    return response, metadata
            
            # Genel small talk cevabı
            metadata = {
                "llm_used": False,
                "tokens_used": 0,
                "model": "small_talk_fallback",
                "profiles_count": 0,
                "fallback_used": True,
                "query_type": "small_talk"
            }
            return "Merhaba! Ben ALUNA, size alüminyum profil aramanızda yardımcı olabilirim. Hangi profili arıyorsunuz? 😊", metadata
        
        # 1. Profilleri bul (mevcut mantık - DEĞİŞMEYECEK)
        # Birleşim sorgusu mu?
        is_conn_query = self._is_connection_query(query)
        
        if is_conn_query:
            # Birleşim context'i al
            connection_context = self._get_connection_context(query)
            
            if connection_context:
                # LLM'e gönder
                if llm_service.is_enabled:
                    try:
                        llm_response = await llm_service.generate_response(
                            query=query,
                            context=connection_context,
                            conversation_history=conversation_history
                        )
                        
                        if not llm_response.fallback_used:
                            # LLM başarılı
                            metadata = {
                                "llm_used": True,
                                "tokens_used": llm_response.tokens_used,
                                "model": llm_response.model_used,
                                "profiles_count": 0,
                                "fallback_used": False
                            }
                            return llm_response.message, metadata
                    except Exception as e:
                        logger.error(f"LLM error: {e}")
                
                # Fallback: Direkt connection context döndür
                metadata = {
                    "llm_used": False,
                    "tokens_used": 0,
                    "model": "fallback",
                    "profiles_count": 0,
                    "fallback_used": True
                }
                return connection_context, metadata
            else:
                # Connection bulunamadı
                fallback_answer = "Üzgünüm, bu profil veya birleşim hakkında bilgi bulamadım."
                metadata = {
                    "llm_used": False,
                    "tokens_used": 0,
                    "model": "fallback",
                    "profiles_count": 0,
                    "fallback_used": True
                }
                return fallback_answer, metadata
        
        # Direkt profil kodu araması mı? (örn: "LR3101 nedir", "AP0028 nedir")
        # ÖNCE profil araması yap - kullanıcı profil görmek istiyor
        profile_by_code = self._search_profile_by_code(query)
        if profile_by_code:
            metadata = {
                "llm_used": False,
                "tokens_used": 0,
                "model": "direct_code_search",
                "profiles_count": 1,
                "fallback_used": False
            }
            return profile_by_code, metadata
        
        # Profil bulunamadı, birleşim kodu mu? (örn: "GLR64-05", "LR-3101")
        connection_by_code = self._search_by_connection_code(query)
        if connection_by_code:
            metadata = {
                "llm_used": False,
                "tokens_used": 0,
                "model": "connection_code_search",
                "profiles_count": 0,
                "fallback_used": False
            }
            return connection_by_code, metadata
        
        # Katalog araması mı?
        if is_catalog_query(query):
            catalog_answer = self._format_catalog_answer(query, top_k)
            
            # Katalog cevaplarını LLM'e gönderme (zaten formatlanmış)
            metadata = {
                "llm_used": False,
                "tokens_used": 0,
                "model": "catalog",
                "profiles_count": 0,
                "fallback_used": False
            }
            return catalog_answer, metadata
        
        # Standart profil araması
        results = search_service.search(query, top_k=top_k)
        
        if not results:
            # Profil bulunamadı AMA conversation history varsa, LLM'e sor
            # Belki önceki konuşmadan cevap verebilir
            if conversation_history and len(conversation_history) > 0 and llm_service.is_enabled:
                logger.info("No profiles found, but conversation history exists. Asking LLM...")
                
                try:
                    # Önceki konuşmadan context oluştur
                    history_context = "Yeni profil bulunamadı. Ancak önceki konuşmamızda bahsettiğimiz profiller var. Kullanıcının sorusunu önceki konuşma bağlamında cevapla."
                    
                    llm_response = await llm_service.generate_response(
                        query=query,
                        context=history_context,
                        conversation_history=conversation_history
                    )
                    
                    if not llm_response.fallback_used:
                        metadata = {
                            "llm_used": True,
                            "tokens_used": llm_response.tokens_used,
                            "model": llm_response.model_used,
                            "profiles_count": 0,
                            "fallback_used": False,
                            "query_type": "follow_up"
                        }
                        return llm_response.message, metadata
                except Exception as e:
                    logger.error(f"LLM error on follow-up: {e}")
            
            # Fallback: format_direct_answer çağır (yakın değer önerisi için)
            fallback_answer = self.format_direct_answer(query, top_k, previous_query=previous_query)
            metadata = {
                "llm_used": False,
                "tokens_used": 0,
                "model": "fallback",
                "profiles_count": 0,
                "fallback_used": True
            }
            return fallback_answer, metadata
        
        # 2. Context formatla
        context = self._format_profile_context_for_llm(results)
        
        # 3. LLM'e gönder
        if llm_service.is_enabled:
            try:
                llm_response = await llm_service.generate_response(
                    query=query,
                    context=context,
                    conversation_history=conversation_history
                )
                
                if not llm_response.fallback_used:
                    # LLM başarılı
                    metadata = {
                        "llm_used": True,
                        "tokens_used": llm_response.tokens_used,
                        "model": llm_response.model_used,
                        "profiles_count": len(results),
                        "fallback_used": False
                    }
                    return llm_response.message, metadata
                
            except Exception as e:
                logger.error(f"LLM error: {e}")
        
        # 4. Fallback: Mevcut format_direct_answer kullan
        logger.info("Using fallback: format_direct_answer")
        fallback_answer = self.format_direct_answer(query, top_k, previous_query=previous_query)
        
        metadata = {
            "llm_used": False,
            "tokens_used": 0,
            "model": "fallback",
            "profiles_count": len(results),
            "fallback_used": True
        }
        
        return fallback_answer, metadata
    
    def _format_profile_context_for_llm(self, results: List[Tuple]) -> str:
        """
        Profil sonuçlarını LLM için formatla
        
        Args:
            results: (Profile, score, reason) tuple listesi
            
        Returns:
            Formatlanmış context string
        """
        context_parts = []
        
        for i, (profile, score, reason) in enumerate(results, 1):
            dims = ", ".join([f"{k}={v}mm" for k, v in profile.dimensions.items()])
            
            # Sistem bilgisi varsa ekle
            system_name = self._get_system_info_for_profile(profile.code)
            system_line = f"Sistem: {system_name}\n" if system_name else ""
            
            # Profil görseli URL'i
            image_url = f"{settings.backend_url}/api/profile-image/{profile.code}"
            
            context_parts.append(
                f"{i}. **{profile.code}**\n"
                f"Kategori: {profile.category}\n"
                f"{system_line}"
                f"Ölçüler: {dims}\n"
                f"Eşleşme Sebebi: {reason}\n"
                f"Görsel: {image_url}\n"
            )
        
        return "\n".join(context_parts)


# Global instance
rag_service = RAGService()
