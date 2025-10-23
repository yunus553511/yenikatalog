import gdown
import os
from pathlib import Path
from typing import List, Optional
import logging
from datetime import datetime

from config import settings
from models.profile import Profile
from utils.excel_parser import parse_excel_file, validate_profiles

logger = logging.getLogger(__name__)


class ExcelService:
    """Google Drive'dan Excel indirme ve yönetme servisi"""
    
    def __init__(self):
        self.file_id = settings.google_drive_file_id
        self.cache_path = Path(settings.excel_cache_path)
        self.profiles: List[Profile] = []
        self.last_update: Optional[datetime] = None
        
        # Cache klasörünü oluştur
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self) -> bool:
        """
        Servisi başlat: Excel'i indir ve parse et
        
        Returns:
            Başarılı ise True
        """
        logger.info("Excel servisi başlatılıyor...")
        
        try:
            # Excel'i indir veya cache'den yükle
            excel_path = await self.download_or_use_cache()
            
            if not excel_path:
                logger.error("Excel dosyası bulunamadı")
                return False
            
            # Parse et
            await self.load_profiles(excel_path)
            
            logger.info(f"Excel servisi başarıyla başlatıldı: {len(self.profiles)} profil")
            return True
            
        except Exception as e:
            logger.error(f"Excel servisi başlatma hatası: {e}")
            return False
    
    async def download_or_use_cache(self) -> Optional[Path]:
        """
        Google Drive'dan indir, hata olursa cache kullan
        
        Returns:
            Excel dosyasının yolu
        """
        try:
            # Google Drive'dan indir
            logger.info(f"Google Drive'dan indiriliyor: {self.file_id}")
            success = await self.download_from_drive()
            
            if success:
                logger.info("Google Drive'dan başarıyla indirildi")
                return self.cache_path
            else:
                logger.warning("Google Drive indirme başarısız, cache kullanılıyor")
                return self._use_cached_file()
                
        except Exception as e:
            logger.error(f"İndirme hatası: {e}, cache kullanılıyor")
            return self._use_cached_file()
    
    async def download_from_drive(self) -> bool:
        """
        Google Drive'dan dosyayı indir
        
        Returns:
            Başarılı ise True
        """
        try:
            # Google Drive URL oluştur
            url = f"https://docs.google.com/spreadsheets/d/{self.file_id}/export?format=xlsx"
            
            # İndir
            output = str(self.cache_path)
            gdown.download(url, output, quiet=False, fuzzy=True)
            
            # Dosyanın var olduğunu kontrol et
            if self.cache_path.exists() and self.cache_path.stat().st_size > 0:
                logger.info(f"Dosya başarıyla indirildi: {output}")
                return True
            else:
                logger.error("İndirilen dosya boş veya bulunamadı")
                return False
                
        except Exception as e:
            logger.error(f"Google Drive indirme hatası: {e}")
            return False
    
    def _use_cached_file(self) -> Optional[Path]:
        """
        Cache'deki dosyayı kullan
        
        Returns:
            Cache dosyasının yolu veya None
        """
        if self.cache_path.exists():
            logger.info(f"Cache dosyası kullanılıyor: {self.cache_path}")
            return self.cache_path
        else:
            logger.error("Cache dosyası bulunamadı")
            return None
    
    async def load_profiles(self, excel_path: Path) -> None:
        """
        Excel dosyasını parse et ve profilleri yükle
        
        Args:
            excel_path: Excel dosyasının yolu
        """
        logger.info(f"Profiller yükleniyor: {excel_path}")
        
        try:
            # Parse et
            profiles = parse_excel_file(str(excel_path))
            
            # Validate et
            self.profiles = validate_profiles(profiles)
            
            # Güncelleme zamanını kaydet
            self.last_update = datetime.now()
            
            logger.info(f"{len(self.profiles)} profil başarıyla yüklendi")
            
        except Exception as e:
            logger.error(f"Profil yükleme hatası: {e}")
            raise
    
    async def refresh_data(self) -> bool:
        """
        Verileri yeniden indir ve yükle
        
        Returns:
            Başarılı ise True
        """
        logger.info("Veriler yenileniyor...")
        
        try:
            # Yeni dosyayı indir
            success = await self.download_from_drive()
            
            if success:
                # Profilleri yeniden yükle
                await self.load_profiles(self.cache_path)
                logger.info("Veriler başarıyla yenilendi")
                return True
            else:
                logger.error("Veri yenileme başarısız")
                return False
                
        except Exception as e:
            logger.error(f"Veri yenileme hatası: {e}")
            return False
    
    def get_profiles(self) -> List[Profile]:
        """
        Tüm profilleri döner
        
        Returns:
            Profile listesi
        """
        return self.profiles
    
    def get_profile_by_code(self, code: str) -> Optional[Profile]:
        """
        Profil koduna göre profil döner
        
        Args:
            code: Profil kodu
            
        Returns:
            Profile veya None
        """
        code_upper = code.upper().strip()
        
        for profile in self.profiles:
            if profile.code.upper() == code_upper:
                return profile
        
        return None
    
    def get_profiles_by_category(self, category: str) -> List[Profile]:
        """
        Kategoriye göre profilleri döner
        
        Args:
            category: Kategori adı
            
        Returns:
            Profile listesi
        """
        return [p for p in self.profiles if category.upper() in p.category.upper()]
    
    def get_stats(self) -> dict:
        """
        İstatistikleri döner
        
        Returns:
            İstatistik dictionary
        """
        categories = {}
        for profile in self.profiles:
            categories[profile.category] = categories.get(profile.category, 0) + 1
        
        return {
            "total_profiles": len(self.profiles),
            "categories": categories,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "cache_file": str(self.cache_path),
            "cache_exists": self.cache_path.exists()
        }


# Global instance
excel_service = ExcelService()
