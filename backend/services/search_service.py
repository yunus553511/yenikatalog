import re
from typing import List, Tuple, Optional
import logging

from models.profile import Profile
from services.excel_service import excel_service
from services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


def get_category_filter(query_lower: str) -> Optional[str]:
    """
    Sorgudan kategori filtresini çıkar
    Öncelik sırasına dikkat! (uzun kelimeler önce)
    """
    if 'köşebent' in query_lower or 'kosebent' in query_lower:
        return 'KÖŞEBENT'
    elif 't profil' in query_lower or 't tipi' in query_lower:
        return 'T'
    elif 'u profil' in query_lower or 'u tipi' in query_lower:
        return 'U'
    elif 'kutu' in query_lower:
        return 'KUTU'
    elif 'lama' in query_lower:
        return 'LAMA'
    return None


class SearchService:
    """Akıllı profil arama servisi - ölçü bazlı ve text bazlı arama"""
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[Profile, float, str]]:
        """
        Akıllı arama: Önce ölçü bazlı, sonra embedding bazlı
        
        Args:
            query: Kullanıcı sorgusu
            top_k: Maksimum sonuç sayısı
            
        Returns:
            (Profile, score, match_reason) tuple listesi
        """
        logger.info(f"Arama: '{query}'")
        
        # 1. Ölçü bazlı arama dene
        dimension_results = self._search_by_dimensions(query)
        if dimension_results:
            logger.info(f"Ölçü bazlı arama: {len(dimension_results)} sonuç")
            return dimension_results[:top_k]
        
        # 2. Profil kodu araması dene
        code_results = self._search_by_code(query)
        if code_results:
            logger.info(f"Kod bazlı arama: {len(code_results)} sonuç")
            return code_results[:top_k]
        
        # 3. Kategori araması dene (sadece ölçü belirtilmemişse)
        has_dimension = bool(re.search(r'\d+', query))
        if not has_dimension:
            category_results = self._search_by_category(query)
            if category_results:
                logger.info(f"Kategori bazlı arama: {len(category_results)} sonuç")
                return category_results[:top_k]
        
        # 4. Embedding bazlı arama (fallback)
        # Ama kategori belirtilmişse embedding kullanma
        query_lower = query.lower()
        has_category = any(cat in query_lower for cat in ['kutu', 'lama', 'köşebent', 'kosebent', 't profil', 'u profil'])
        
        if has_category:
            logger.info("Kategori belirtilmiş ama uygun profil bulunamadı")
            return []
        
        logger.info("Embedding bazlı arama kullanılıyor")
        emb_results = embedding_service.search(query, top_k=top_k)
        return [(p, score, "Benzerlik araması") for p, score in emb_results]
    
    def _search_by_dimensions(self, query: str) -> List[Tuple[Profile, float, str]]:
        """Ölçü bazlı arama"""
        query_lower = query.lower()
        results = []
        
        # Çap araması (boru profilleri için)
        cap_match = re.search(r'(?:çap|cap|ø)\s*(\d+(?:\.\d+)?)', query_lower)
        if cap_match:
            cap_value = float(cap_match.group(1))
            logger.info(f"Çap araması: Ø={cap_value}")
            
            for profile in excel_service.get_profiles():
                if 'Ø' in profile.dimensions:
                    if abs(profile.dimensions['Ø'] - cap_value) < 0.1:
                        reason = f"Çap: {profile.dimensions['Ø']}mm"
                        results.append((profile, 1.0, reason))
        
        # AxB formatı (30x30, 40x50 gibi)
        axb_match = re.search(r'(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)', query_lower)
        if axb_match:
            a_value = float(axb_match.group(1))
            b_value = float(axb_match.group(2))
            logger.info(f"AxB araması: A={a_value}, B={b_value}")
            
            category_filter = get_category_filter(query_lower)
            logger.info(f"Kategori filtresi: {category_filter}")
            
            for profile in excel_service.get_profiles():
                if category_filter and category_filter not in profile.category:
                    continue
                
                if 'A' in profile.dimensions and 'B' in profile.dimensions:
                    a_diff = abs(profile.dimensions['A'] - a_value)
                    b_diff = abs(profile.dimensions['B'] - b_value)
                    
                    if a_diff < 0.1 and b_diff < 0.1:
                        reason = f"Ölçü: {profile.dimensions['A']}x{profile.dimensions['B']}mm"
                        if 'K' in profile.dimensions:
                            reason += f", Kalınlık: {profile.dimensions['K']}mm"
                        results.append((profile, 1.0, reason))
        
        # "A a B" formatı (30 a 30, 40 a 50 gibi)
        aab_match = re.search(r'(\d+(?:\.\d+)?)\s*[aA]\s*(\d+(?:\.\d+)?)', query_lower)
        if aab_match and not axb_match:
            a_value = float(aab_match.group(1))
            b_value = float(aab_match.group(2))
            logger.info(f"A a B araması: A={a_value}, B={b_value}")
            
            category_filter = get_category_filter(query_lower)
            logger.info(f"Kategori filtresi: {category_filter}")
            
            for profile in excel_service.get_profiles():
                if category_filter and category_filter not in profile.category:
                    continue
                
                if 'A' in profile.dimensions and 'B' in profile.dimensions:
                    a_diff = abs(profile.dimensions['A'] - a_value)
                    b_diff = abs(profile.dimensions['B'] - b_value)
                    
                    if a_diff < 0.1 and b_diff < 0.1:
                        reason = f"Ölçü: {profile.dimensions['A']}x{profile.dimensions['B']}mm"
                        if 'K' in profile.dimensions:
                            reason += f", Kalınlık: {profile.dimensions['K']}mm"
                        results.append((profile, 1.0, reason))
        
        # Kalınlık araması (kategori ile birlikte veya tek başına)
        # Desteklenen formatlar:
        # - "3 mm kalınlık", "kalınlık 3", "et kalınlığı 3 mm"
        # - "kalınlığı 2 milimetre olan", "kalınlığı 2mm olan"
        # - "2 milimetre kalınlıkta", "2mm kalınlık"
        
        # Format 1: "kalınlığı X milimetre/mm olan"
        kalinlik_match = re.search(r'(?:kalınlığı|kalinligi)\s*(\d+(?:\.\d+)?)\s*(?:mm|milimetre|milim)?\s*(?:olan)?', query_lower)
        
        # Format 2: "X mm/milimetre kalınlık/kalınlıkta"
        if not kalinlik_match:
            kalinlik_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:mm|milimetre|milim)?\s*(?:kalınlık|kalinlik|kalınlıkta|kalinlikta)', query_lower)
        
        # Format 3: "kalınlık X" veya "et kalınlığı X"
        if not kalinlik_match:
            kalinlik_match = re.search(r'(?:kalınlık|kalinlik|et kalınlığı|et kalinligi)\s*(\d+(?:\.\d+)?)', query_lower)
        if kalinlik_match and not results:
            k_value = float(kalinlik_match.group(1))
            
            # Kategori filtresi var mı kontrol et
            category_filter = get_category_filter(query_lower)
            
            if category_filter:
                logger.info(f"Kalınlık + Kategori araması: K={k_value}, Kategori={category_filter}")
            else:
                logger.info(f"Kalınlık araması: K={k_value}")
            
            for profile in excel_service.get_profiles():
                # Kategori filtresi varsa kontrol et
                if category_filter and category_filter not in profile.category:
                    continue
                
                if 'K' in profile.dimensions:
                    if abs(profile.dimensions['K'] - k_value) < 0.1:
                        dims_str = ", ".join([f"{k}={v}mm" for k, v in profile.dimensions.items()])
                        if category_filter:
                            reason = f"Kalınlık: {profile.dimensions['K']}mm ({dims_str})"
                        else:
                            reason = f"Kalınlık: {profile.dimensions['K']}mm ({dims_str})"
                        results.append((profile, 1.0, reason))
        
        # Tek sayı (örn: "30 profil", "40 kutu")
        single_num_match = re.search(r'\b(\d+(?:\.\d+)?)\b', query_lower)
        if single_num_match and not results:
            value = float(single_num_match.group(1))
            category_filter = get_category_filter(query_lower)
            
            if category_filter:
                logger.info(f"{category_filter} profil araması: A veya B = {value}")
                
                for profile in excel_service.get_profiles():
                    if category_filter not in profile.category:
                        continue
                    
                    if 'A' in profile.dimensions and 'B' in profile.dimensions:
                        # A veya B değerlerinden herhangi birinde eşleşme varsa
                        a_match = abs(profile.dimensions['A'] - value) < 0.1
                        b_match = abs(profile.dimensions['B'] - value) < 0.1
                        
                        if a_match or b_match:
                            reason = f"Ölçü: {profile.dimensions['A']}x{profile.dimensions['B']}mm"
                            if 'K' in profile.dimensions:
                                reason += f", Kalınlık: {profile.dimensions['K']}mm"
                            results.append((profile, 1.0, reason))
        
        return results
    
    def _search_by_code(self, query: str) -> List[Tuple[Profile, float, str]]:
        """Profil kodu ile arama"""
        code_matches = re.findall(r'\b(AP\d+)\b', query.upper())
        
        if not code_matches:
            return []
        
        results = []
        for code in code_matches:
            profile = excel_service.get_profile_by_code(code)
            if profile:
                dims_str = ", ".join([f"{k}={v}mm" for k, v in profile.dimensions.items()])
                reason = f"Profil kodu eşleşmesi ({dims_str})"
                results.append((profile, 1.0, reason))
        
        return results
    
    def _search_by_category(self, query: str) -> List[Tuple[Profile, float, str]]:
        """Kategori ile arama"""
        query_lower = query.lower()
        
        category_map = {
            'boru': 'STANDART BORU',
            'kutu': 'STANDART KUTU',
            't profil': 'STANDART T',
            'u profil': 'STANDART U',
            'lama': 'STANDART LAMA',
            'köşebent': 'STANDART KÖŞEBENT',
            'kosebent': 'STANDART KÖŞEBENT'
        }
        
        for keyword, category in category_map.items():
            if keyword in query_lower:
                profiles = excel_service.get_profiles_by_category(category)
                if profiles:
                    results = []
                    for profile in profiles[:10]:
                        dims_str = ", ".join([f"{k}={v}mm" for k, v in profile.dimensions.items()])
                        reason = f"{category} ({dims_str})"
                        results.append((profile, 0.9, reason))
                    return results
        
        return []


# Global instance
search_service = SearchService()
