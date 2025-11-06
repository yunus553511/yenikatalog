"""
Katalog servisi - Tüm profil kataloğunu yönetir
"""
import gdown
import os
from pathlib import Path
from typing import List, Dict, Optional
import logging

from utils.catalog_parser import parse_catalog_excel, group_by_categories, CatalogProfile

logger = logging.getLogger(__name__)


class CatalogService:
    """Katalog yönetim servisi"""
    
    def __init__(self):
        self.profiles: List[CatalogProfile] = []
        self.grouped_profiles: Dict = {}
        self.cache_dir = Path("data/cache")
        self.catalog_file = self.cache_dir / "catalog.xlsx"
        self.is_ready = False
    
    async def initialize(self, file_id: str = "1FFFwzkP26v9ooQI3w49wBD1SmJpAvCixUmC3tuI-m1o"):
        """
        Katalog servisini başlat
        
        Args:
            file_id: Google Drive dosya ID
        """
        logger.info("Katalog servisi başlatılıyor...")
        
        try:
            # Cache klasörünü oluştur
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Google Drive'dan indir
            success = await self._download_from_drive(file_id)
            if not success:
                logger.error("Katalog indirilemedi!")
                return False
            
            # Parse et
            self.profiles = parse_catalog_excel(str(self.catalog_file))
            
            # Kategorilere göre grupla
            self.grouped_profiles = group_by_categories(self.profiles)
            
            self.is_ready = True
            logger.info(f"Katalog servisi hazır: {len(self.profiles)} profil")
            return True
            
        except Exception as e:
            logger.error(f"Katalog servisi başlatma hatası: {e}")
            return False
    
    async def _download_from_drive(self, file_id: str) -> bool:
        """Google Drive'dan katalog indir"""
        try:
            logger.info(f"Google Drive'dan indiriliyor: {file_id}")
            
            url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
            
            gdown.download(url, str(self.catalog_file), quiet=False, fuzzy=True)
            
            if self.catalog_file.exists():
                logger.info(f"Dosya başarıyla indirildi: {self.catalog_file}")
                return True
            else:
                logger.error("Dosya indirilemedi!")
                return False
                
        except Exception as e:
            logger.error(f"Google Drive indirme hatası: {e}")
            return False
    
    def get_all_profiles(self) -> List[Dict]:
        """Tüm profilleri getir"""
        return [p.to_dict() for p in self.profiles]
    
    def get_profile_by_no(self, profile_no: str) -> Optional[Dict]:
        """Profil numarasına göre profil getir"""
        for profile in self.profiles:
            if profile.profile_no == profile_no:
                return profile.to_dict()
        return None
    
    def search_profiles(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Profil ara
        
        Args:
            query: Arama sorgusu
            limit: Maksimum sonuç sayısı
        """
        query_lower = query.lower()
        results = []
        
        for profile in self.profiles:
            # Profil no, müşteri, açıklama veya kategorilerde ara
            if (query_lower in profile.profile_no.lower() or
                query_lower in profile.customer.lower() or
                query_lower in profile.description.lower() or
                any(query_lower in cat.lower() for cat in profile.categories)):
                
                results.append(profile.to_dict())
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_categories(self, companies: List[str] = None) -> Dict:
        """
        Tüm kategorileri getir (şirket filtrelemeli)
        
        Args:
            companies: Filtrelenecek şirketler listesi ['linearossa', 'beymetal', 'alfore']
                      None ise tüm profiller
        
        Returns:
            {
                'standard': ['STANDART BORU', 'STANDART KUTU', ...],
                'shape': ['T', 'U', 'L', ...],
                'sector': ['Pencere', 'Kapı', ...]
            }
        """
        if companies:
            # Şirket filtrelemeli kategoriler
            filtered_grouped = self._filter_by_companies(companies)
            return {
                'standard': list(filtered_grouped.get('standard', {}).keys()),
                'shape': list(filtered_grouped.get('shape', {}).keys()),
                'sector': list(filtered_grouped.get('sector', {}).keys())
            }
        
        return {
            'standard': list(self.grouped_profiles.get('standard', {}).keys()),
            'shape': list(self.grouped_profiles.get('shape', {}).keys()),
            'sector': list(self.grouped_profiles.get('sector', {}).keys())
        }
    
    def _filter_by_companies(self, companies: List[str]) -> Dict:
        """Profilleri şirketlere göre filtrele ve grupla"""
        filtered_grouped = {
            'standard': {},
            'shape': {},
            'sector': {}
        }
        
        # Filtrelenmiş profilleri al
        filtered_profiles = [p for p in self.profiles if p.company in companies]
        
        # Kategorilere göre grupla
        for profile in filtered_profiles:
            for category in profile.categories:
                cat_type = profile.get_category_type(category)
                
                if category not in filtered_grouped[cat_type]:
                    filtered_grouped[cat_type][category] = []
                
                filtered_grouped[cat_type][category].append(profile)
        
        return filtered_grouped
    
    def get_profiles_by_category(self, category: str, companies: List[str] = None) -> List[Dict]:
        """
        Kategoriye göre profilleri getir (şirket filtrelemeli)
        
        Args:
            category: Kategori adı
            companies: Filtrelenecek şirketler listesi
        """
        # Hangi tipte olduğunu bul
        for cat_type in ['standard', 'shape', 'sector']:
            if category in self.grouped_profiles.get(cat_type, {}):
                profiles = self.grouped_profiles[cat_type][category]
                
                # Şirket filtresi uygula
                if companies:
                    profiles = [p for p in profiles if p.company in companies]
                
                return [p.to_dict() for p in profiles]
        
        return []
    
    def get_stats(self) -> Dict:
        """İstatistikleri getir"""
        standard_count = sum(1 for p in self.profiles if p.is_standard)
        mold_count = sum(1 for p in self.profiles if p.has_mold)
        
        return {
            'total_profiles': len(self.profiles),
            'standard_profiles': standard_count,
            'custom_profiles': len(self.profiles) - standard_count,
            'profiles_with_mold': mold_count,
            'categories': self.get_categories(),
            'is_ready': self.is_ready
        }


# Global instance
catalog_service = CatalogService()
