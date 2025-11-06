import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import requests
from pathlib import Path

logger = logging.getLogger(__name__)


class ConnectionServiceError(Exception):
    """Base exception for connection service"""
    pass


class DataLoadError(ConnectionServiceError):
    """Excel yükleme hatası"""
    pass


class ParseError(ConnectionServiceError):
    """Excel parse hatası"""
    pass


class ConnectionService:
    """Profil birleşim sistemlerini yöneten servis"""
    
    def __init__(self):
        # Google Sheets URL (environment variable'dan veya default)
        self.sheet_url = os.getenv(
            'CONNECTION_SHEET_URL',
            'https://docs.google.com/spreadsheets/d/1yeyLrNq6RqenoI-ZYK_wiij6jhHmDrBYil1zn8_AAKg/export?format=xlsx'
        )
        
        # Cache dosya yolu
        self.cache_dir = Path("data/cache")
        self.cache_file = self.cache_dir / "connections.xlsx"
        
        # In-memory cache
        self._data: Optional[Dict] = None
        self._last_update: Optional[datetime] = None
        
        # Cache expiration (24 saat)
        self.cache_expiration = timedelta(hours=24)
        
        logger.info("ConnectionService initialized")
    
    async def initialize(self) -> None:
        """
        Servisi başlat ve verileri yükle
        
        Raises:
            DataLoadError: Veri yükleme başarısız olursa
        """
        logger.info("Initializing ConnectionService...")
        
        # Cache klasörünü oluştur
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Cache directory: {self.cache_dir}")
        
        try:
            # Verileri yükle
            await self.load_data()
            logger.info("ConnectionService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ConnectionService: {e}")
            raise DataLoadError(f"Initialization failed: {e}")
    
    async def load_data(self, force_refresh: bool = False) -> None:
        """
        Google Sheets'ten veri yükle
        
        Args:
            force_refresh: True ise cache'i yoksay ve yeniden yükle
            
        Raises:
            DataLoadError: Veri yükleme başarısız olursa
        """
        # Cache kontrolü
        if not force_refresh and self._is_cache_valid():
            logger.info("Using cached data (still valid)")
            return
        
        logger.info("Loading data from Google Sheets...")
        
        try:
            # Google Sheets'ten indir
            response = requests.get(self.sheet_url, timeout=30)
            response.raise_for_status()
            
            # Dosyayı kaydet
            with open(self.cache_file, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded Excel file to {self.cache_file}")
            
            # Parse et
            self._data = self.parse_excel(str(self.cache_file))
            self._last_update = datetime.now()
            
            logger.info(f"Data loaded successfully. Systems: {len(self._data.get('systems', []))}")
            
        except requests.RequestException as e:
            logger.error(f"Failed to download from Google Sheets: {e}")
            
            # Fallback: Cache'lenmiş dosyayı kullan
            if self.cache_file.exists():
                logger.warning("Using cached file as fallback")
                try:
                    self._data = self.parse_excel(str(self.cache_file))
                    self._last_update = datetime.now()
                    logger.info("Loaded data from cached file")
                except Exception as parse_error:
                    logger.error(f"Failed to parse cached file: {parse_error}")
                    raise DataLoadError(f"Failed to load data: {e}")
            else:
                raise DataLoadError(f"No cached data available and download failed: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error while loading data: {e}")
            raise DataLoadError(f"Failed to load data: {e}")
    
    def _is_cache_valid(self) -> bool:
        """
        Cache'in hala geçerli olup olmadığını kontrol et
        
        Returns:
            True ise cache geçerli
        """
        if self._data is None or self._last_update is None:
            return False
        
        age = datetime.now() - self._last_update
        is_valid = age < self.cache_expiration
        
        if not is_valid:
            logger.info(f"Cache expired (age: {age})")
        
        return is_valid
    
    def parse_excel(self, file_path: str) -> Dict:
        """
        Excel dosyasını parse et
        
        Args:
            file_path: Excel dosya yolu
            
        Returns:
            Yapılandırılmış veri dictionary'si
            
        Raises:
            ParseError: Parse işlemi başarısız olursa
        """
        logger.info(f"Parsing Excel file: {file_path}")
        
        try:
            # Excel'i oku (header yok, tüm veriyi al)
            df = pd.read_excel(file_path, header=None)
            
            logger.info(f"Excel loaded. Shape: {df.shape}")
            
            # Satır 1 header (index 1)
            headers = df.iloc[1].tolist()
            
            # Satır 2'den itibaren veri (index 2+)
            data_df = df.iloc[2:].copy()
            data_df.columns = headers
            
            # Sistemleri parse et
            systems = []
            current_system = None
            
            for idx, row in data_df.iterrows():
                system_name = row.get('SİSTEMLER')
                
                # Yeni sistem başlıyor mu?
                if pd.notna(system_name) and system_name.strip():
                    # Önceki sistemi kaydet
                    if current_system and current_system.get('profiles'):
                        systems.append(current_system)
                    
                    # Yeni sistem oluştur (newline karakterlerini temizle)
                    clean_name = str(system_name).strip().replace('\n', ' ').replace('  ', ' ')
                    current_system = {
                        'name': clean_name,
                        'profiles': []
                    }
                    logger.debug(f"New system: {current_system['name']}")
                
                # Profil bilgisi var mı?
                profile_name = row.get('PROFİL ADI')
                connection_code = row.get('PROFİL BİRLEŞİM\n KODU')
                
                if pd.notna(profile_name) and pd.notna(connection_code):
                    if current_system is None:
                        logger.warning(f"Profile without system at row {idx}")
                        continue
                    
                    # Profil oluştur
                    profile = self._parse_profile_row(row)
                    current_system['profiles'].append(profile)
                    logger.debug(f"  Profile: {profile['connection_code']}")
            
            # Son sistemi ekle
            if current_system and current_system.get('profiles'):
                systems.append(current_system)
            
            data = {
                "systems": systems,
                "total_systems": len(systems),
                "total_profiles": sum(len(s['profiles']) for s in systems)
            }
            
            logger.info(f"Excel parsed successfully. Systems: {data['total_systems']}, Profiles: {data['total_profiles']}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to parse Excel: {e}", exc_info=True)
            raise ParseError(f"Excel parse failed: {e}")
    
    def _parse_profile_row(self, row: pd.Series) -> Dict:
        """
        Tek bir profil satırını parse et
        
        Args:
            row: Pandas Series (Excel satırı)
            
        Returns:
            Profil dictionary'si
        """
        def safe_get(key, default=None):
            """Güvenli değer alma (NaN kontrolü)"""
            val = row.get(key)
            if pd.isna(val):
                return default
            return val
        
        def safe_float(key, default=None):
            """Güvenli float dönüşümü"""
            val = safe_get(key)
            if val is None:
                return default
            try:
                return float(val)
            except (ValueError, TypeError):
                return default
        
        profile = {
            'name': str(safe_get('PROFİL ADI', '')).strip(),
            'name_eng': str(safe_get('PROFİL ADI (İNG.)', '')).strip() or None,
            'connection_code': str(safe_get('PROFİL BİRLEŞİM\n KODU', '')).strip(),
            'inner_profile': str(safe_get('İÇ\n PROFİL A', '')).strip() or None,
            'middle_profile': str(safe_get('ORTA\n PROFİL B', '')).strip() or None,
            'outer_profile': str(safe_get('DIŞ\n PROFİL C', '')).strip() or None,
            'gaskets': {
                'barrier_ab_bottom': str(safe_get('BARİYER A-B ALT', '')).strip() or None,
                'barrier_ab_top': str(safe_get('BARİYER A-B ÜST', '')).strip() or None,
                'barrier_bc_bottom': str(safe_get('BARİYER B-C ALT', '')).strip() or None,
                'barrier_bc_top': str(safe_get('BARİYER B-C ÜST', '')).strip() or None,
                'barrier_ac_bottom': str(safe_get('BARİYER A-C ALT', '')).strip() or None,
                'barrier_ac_top': str(safe_get('BARİYER A-C ÜST', '')).strip() or None,
            },
            'weights': {
                'inner_profile': safe_float('İÇ PROFİL\n AĞIRLIK kg/m'),
                'middle_profile': safe_float('ORTA PROFİL\n AĞIRLIK kg/m'),
                'outer_profile': safe_float('DIŞ PROFİL\n AĞIRLIK kg/m'),
                'gasket': safe_float('BARİYER AĞIRLIK kg/m'),
                'total_profile': safe_float('PROFİL\n AĞIRLIK kg/m'),
                'total_logical': safe_float('LOGIKAL\n AĞIRLIK kg/m'),
            },
            'mechanical': {
                'jx': safe_float('Jx.\n Cm4'),
                'jy': safe_float('Jy.\n Cm4'),
                'wx': safe_float('Wx\n cm3'),
                'wy': safe_float('Wy\n cm3'),
            },
            'notes': str(safe_get('NOTLAR', '')).strip() or None
        }
        
        return profile
    
    def get_all_systems(self) -> List[Dict]:
        """
        Tüm sistemleri getir
        
        Returns:
            Sistem listesi
        """
        if self._data is None:
            logger.warning("No data loaded")
            return []
        
        return self._data.get('systems', [])
    
    def get_system_by_name(self, system_name: str) -> Optional[Dict]:
        """
        Belirli bir sistemi getir
        
        Args:
            system_name: Sistem adı
            
        Returns:
            Sistem dictionary'si veya None
        """
        systems = self.get_all_systems()
        
        for system in systems:
            if system.get('name', '').lower() == system_name.lower():
                return system
        
        logger.warning(f"System not found: {system_name}")
        return None
    
    def get_profile_connections(self, profile_code: str) -> Optional[Dict]:
        """
        Belirli bir profilin birleşim bilgilerini getir
        
        Args:
            profile_code: Profil kodu (örn: LR-3101)
            
        Returns:
            Profil birleşim bilgileri veya None
        """
        systems = self.get_all_systems()
        
        profile_code_upper = profile_code.upper()
        
        for system in systems:
            for profile in system.get('profiles', []):
                if profile.get('connection_code', '').upper() == profile_code_upper:
                    return {
                        'system': system.get('name'),
                        'profile': profile
                    }
        
        logger.warning(f"Profile not found: {profile_code}")
        return None
    
    def _normalize_turkish(self, text: str) -> str:
        """
        Türkçe karakterleri normalize et (arama için)
        
        Args:
            text: Normalize edilecek metin
            
        Returns:
            Normalize edilmiş metin
        """
        if not text:
            return ""
        
        # Önce büyük harfleri değiştir
        text = text.replace('İ', 'i')
        text = text.replace('I', 'ı')
        
        # Lowercase yap
        text = text.lower()
        
        # Türkçe karakterleri normalize et
        replacements = {
            'ı': 'i',
            'ş': 's',
            'ğ': 'g',
            'ü': 'u',
            'ö': 'o',
            'ç': 'c'
        }
        
        for tr_char, en_char in replacements.items():
            text = text.replace(tr_char, en_char)
        
        return text
    
    def search_connections(self, query: str) -> List[Dict]:
        """
        Birleşim verilerinde arama yap
        
        Args:
            query: Arama sorgusu
            
        Returns:
            Eşleşen profil listesi
        """
        if not query:
            return []
        
        query_lower = query.lower()
        query_normalized = self._normalize_turkish(query)
        results = []
        systems = self.get_all_systems()
        
        for system in systems:
            system_name = system.get('name', '')
            system_name_lower = system_name.lower()
            system_name_normalized = self._normalize_turkish(system_name)
            
            # Sistem adında ara (hem normal hem normalized)
            if query_lower in system_name_lower or query_normalized in system_name_normalized:
                results.append({
                    'type': 'system',
                    'system': system_name,
                    'match': 'system_name'
                })
            
            # Profillerde ara
            for profile in system.get('profiles', []):
                profile_name = profile.get('name', '')
                profile_name_lower = profile_name.lower()
                profile_name_normalized = self._normalize_turkish(profile_name)
                
                connection_code = profile.get('connection_code', '')
                connection_code_lower = connection_code.lower()
                connection_code_normalized = self._normalize_turkish(connection_code)
                
                # Profil adında veya birleşim kodunda ara
                match_in_name = query_lower in profile_name_lower or query_normalized in profile_name_normalized
                match_in_code = query_lower in connection_code_lower or query_normalized in connection_code_normalized
                
                # Fitil kodlarında ara
                match_in_gasket = False
                gaskets = profile.get('gaskets', {})
                for gasket_key, gasket_value in gaskets.items():
                    if gasket_value and query_lower in str(gasket_value).lower():
                        match_in_gasket = True
                        break
                
                if match_in_name or match_in_code or match_in_gasket:
                    match_type = 'profile_name' if match_in_name else ('connection_code' if match_in_code else 'gasket')
                    
                    results.append({
                        'type': 'profile',
                        'system': system_name,
                        'profile': profile,
                        'match': match_type
                    })
        
        logger.info(f"Search '{query}' found {len(results)} results")
        return results


# Global instance
connection_service = ConnectionService()
