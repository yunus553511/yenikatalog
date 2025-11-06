"""
Profil görselleri servisi - Google Drive'dan görselleri indirir ve cache'ler
"""
import os
import logging
from pathlib import Path
from typing import Optional
import gdown

logger = logging.getLogger(__name__)


class ImageService:
    """Profil görselleri yönetim servisi"""
    
    def __init__(self):
        self.cache_dir = Path("data/cache/images")
        self.is_ready = False
        # Google Drive folder ID
        self.folder_id = "1t8LYU4yoQe2zHEs4RYBmdxLj5tz4pTsp"
    
    async def initialize(self):
        """
        Image servisini başlat - Google Drive'dan görselleri indir
        """
        logger.info("Image servisi başlatılıyor...")
        
        try:
            # Cache klasörünü oluştur
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Google Drive klasöründen tüm görselleri indir
            success = await self._download_images_from_drive()
            
            if success:
                self.is_ready = True
                image_count = len(list(self.cache_dir.glob("*.png")))
                logger.info(f"Image servisi hazır: {image_count} görsel")
                return True
            else:
                logger.warning("Image servisi başlatılamadı, görseller yüklenemedi")
                return False
                
        except Exception as e:
            logger.error(f"Image servisi başlatma hatası: {e}")
            return False
    
    async def _download_images_from_drive(self) -> bool:
        """
        Google Drive klasöründen görselleri kontrol et ve sync yap
        
        Not: gdown 50+ dosya limitasyonu olduğu için, manuel kopyalanan
        görselleri kullanıyoruz. Bu metod sadece mevcut görselleri kontrol eder.
        """
        try:
            logger.info(f"Mevcut görseller kontrol ediliyor...")
            
            # Cache klasöründeki mevcut görselleri say
            image_files = list(self.cache_dir.glob("*.png"))
            
            if len(image_files) > 0:
                logger.info(f"{len(image_files)} görsel mevcut")
                return True
            else:
                logger.warning("Hiç görsel bulunamadı! Görselleri manuel olarak kopyalayın:")
                logger.warning(f"  Hedef klasör: {self.cache_dir.absolute()}")
                logger.warning(f"  Drive klasör: https://drive.google.com/drive/folders/{self.folder_id}")
                return False
                
        except Exception as e:
            logger.error(f"Görsel kontrol hatası: {e}")
            return False
    
    async def sync_with_drive(self) -> bool:
        """
        Google Drive ile senkronizasyon yap (gelecekte Google Drive API ile)
        
        Şu an için sadece mevcut görselleri kontrol eder.
        İleride Google Drive API entegrasyonu eklenebilir.
        """
        try:
            # Mevcut görselleri kontrol et
            image_files = list(self.cache_dir.glob("*.png"))
            current_count = len(image_files)
            
            logger.info(f"Sync kontrol: {current_count} görsel mevcut")
            
            # TODO: Google Drive API ile yeni/silinen dosyaları kontrol et
            # Bu özellik için Google Drive API credentials gerekli
            
            return True
            
        except Exception as e:
            logger.error(f"Sync hatası: {e}")
            return False
    
    def get_image_path(self, profile_code: str) -> Optional[Path]:
        """
        Profil koduna göre görsel dosya yolunu getir
        
        Args:
            profile_code: Profil kodu (örn: AP0001, LR-3101-1)
            
        Returns:
            Görsel dosya yolu veya None
        """
        if not self.is_ready:
            logger.warning(f"Image service not ready for: {profile_code}")
            return None
        
        # Deneme sırası:
        # 1. Orijinal kod (örn: AP0001.png)
        # 2. İlk tire kaldırılmış (örn: LR-3101-1 -> LR3101-1.png)
        # 3. Küçük harf versiyonları
        
        variants = [
            profile_code,  # Orijinal
        ]
        
        # LR-3101-1 -> LR3101-1 (sadece ilk tire kaldır)
        if profile_code.startswith('LR-') or profile_code.startswith('GL-'):
            without_first_dash = profile_code[:2] + profile_code[3:]
            variants.append(without_first_dash)
        
        # Küçük harf versiyonları
        variants.extend([v.lower() for v in variants])
        
        # Her varyantı dene
        for variant in variants:
            image_file = self.cache_dir / f"{variant}.png"
            logger.debug(f"Trying: {image_file}")
            
            if image_file.exists():
                logger.debug(f"Image found: {image_file}")
                return image_file
        
        logger.warning(f"Image not found for: {profile_code} (tried {len(variants)} variants)")
        return None
    
    def has_image(self, profile_code: str) -> bool:
        """Profil için görsel var mı kontrol et"""
        return self.get_image_path(profile_code) is not None


# Global instance
image_service = ImageService()
