"""
Beymetal Katalog Excel Parser
Tüm profil kataloğunu parse eder
"""
import openpyxl
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CatalogProfile:
    """Katalog profil modeli"""
    
    def __init__(self, row_data: Dict):
        self.profile_no = row_data.get('A', '').strip()
        self.customer = row_data.get('B', '').strip()
        self.description = row_data.get('C', '').strip()
        self.is_standard = row_data.get('D', '').strip().upper() == 'STANDART'
        # E sütunu bilgi amaçlı, kullanmıyoruz
        self.mold_tonnage = row_data.get('F', '').strip()
        self.mold_status = row_data.get('G', '').strip()
        self.category_1 = row_data.get('H', '').strip()
        self.category_2 = row_data.get('I', '').strip()
        self.category_3 = row_data.get('J', '').strip()
        self.category_4 = row_data.get('K', '').strip()
        self.category_5 = row_data.get('L', '').strip()
        self.explanation = row_data.get('M', '').strip()
        
        # Kategorileri H-L sütunlarından al (boş olmayanlar)
        self.categories = [
            cat for cat in [
                self.category_1,
                self.category_2,
                self.category_3,
                self.category_4,
                self.category_5
            ] if cat  # Boş olmayanları al
        ]
        
        # Kalıp durumu normalize et
        if self.mold_status:
            self.has_mold = 'mevcut' in self.mold_status.lower() or 'var' in self.mold_status.lower()
        else:
            self.has_mold = False
        
        # Şirket bilgisini belirle
        self.company = self._determine_company()
    
    def _determine_company(self) -> str:
        """
        Profilin hangi şirkete ait olduğunu belirle
        
        Returns:
            'linearossa', 'beymetal', 'alfore' veya 'other'
        """
        # Profil kodu kontrolü (LR veya GLR ile başlayanlar Linearossa)
        if self.profile_no.upper().startswith('LR') or self.profile_no.upper().startswith('GLR'):
            return 'linearossa'
        
        # Müşteri bilgisi kontrolü - TAM EŞLEŞMELİ
        customer_upper = self.customer.upper().strip()
        
        if customer_upper == 'BEYMETAL':
            return 'beymetal'
        elif customer_upper == 'ALFORE':
            return 'alfore'
        
        return 'other'
    
    def get_category_type(self, category: str) -> str:
        """Kategori tipini belirle"""
        if not category:
            return 'other'
        
        category_upper = category.upper()
        
        # Standart profiller
        if category_upper.startswith('STANDART'):
            return 'standard'
        
        # Şekilsel kategoriler - DAİRE ve DAİRESEL şekilsel kategorilerdir
        shape_keywords = ['DAİRE', 'DAIRE', 'DAİRESEL', 'DAIRESEL']
        if any(keyword in category_upper for keyword in shape_keywords):
            return 'shape'
        
        # Kutu kategorisi Sektörel'e taşı
        if 'KUTU' in category_upper:
            return 'sector'
        
        # Sektörel kategoriler (özel isimler)
        sector_keywords = ['RAY', 'CAM TUTUCU', 'PENCERE', 'KAPI', 'CEPHE', 'PERDE', 
                          'SÜRGÜ', 'SÜRME', 'PANEL', 'BÖLME', 'VITRIN']
        if any(keyword in category_upper for keyword in sector_keywords):
            return 'sector'
        
        # Şekilsel kategori (sadece tek harf veya çok kısa harfler)
        if category[0].isalpha() and not category_upper.startswith('STANDART'):
            # İlk kelime sadece harf mi kontrol et
            first_word = category.split()[0] if ' ' in category else category
            # Sadece 1-2 harflik kategoriler şekilsel (T, U, L, C, H, V, S, F, D, M, K, R gibi)
            if first_word.isalpha() and len(first_word) <= 2:
                return 'shape'
        
        # Diğerleri sektörel
        return 'sector'
    
    def to_dict(self) -> Dict:
        """Dict'e çevir - Profile ile uyumlu format"""
        return {
            'code': self.profile_no,  # Normalize edilmiş alan (Profile ile uyumlu)
            'profile_no': self.profile_no,  # Geriye dönük uyumluluk
            'customer': self.customer,
            'description': self.description,
            'is_standard': self.is_standard,
            'categories': self.categories,
            'company': self.company,  # Şirket bilgisi
            'mold_status': 'Kalıp Mevcut' if self.has_mold else 'Kalıp Yok',
            'has_mold': self.has_mold,
            'explanation': self.explanation,
            'category_types': {
                cat: self.get_category_type(cat) 
                for cat in self.categories
            }
        }


def parse_catalog_excel(file_path: str) -> List[CatalogProfile]:
    """
    Katalog Excel dosyasını parse et
    
    Args:
        file_path: Excel dosya yolu
        
    Returns:
        CatalogProfile listesi
    """
    logger.info(f"Katalog Excel parse ediliyor: {file_path}")
    
    try:
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        sheet = workbook.active
        
        profiles = []
        header_row = 1  # İlk satır başlık
        
        for row_idx, row in enumerate(sheet.iter_rows(min_row=header_row + 1), start=header_row + 1):
            # Boş satırları atla
            if not row[0].value:  # A sütunu (Profil No) boşsa
                continue
            
            # Satır verisini dict'e çevir
            row_data = {
                'A': str(row[0].value) if row[0].value else '',
                'B': str(row[1].value) if row[1].value else '',
                'C': str(row[2].value) if row[2].value else '',
                'D': str(row[3].value) if row[3].value else '',
                'E': str(row[4].value) if row[4].value else '',
                'F': str(row[5].value) if row[5].value else '',
                'G': str(row[6].value) if row[6].value else '',
                'H': str(row[7].value) if row[7].value else '',
                'I': str(row[8].value) if row[8].value else '',
                'J': str(row[9].value) if row[9].value else '',
                'K': str(row[10].value) if row[10].value else '',
                'L': str(row[11].value) if row[11].value else '',
                'M': str(row[12].value) if row[12].value else '',
            }
            
            try:
                profile = CatalogProfile(row_data)
                profiles.append(profile)
            except Exception as e:
                logger.warning(f"Satır {row_idx} parse edilemedi: {e}")
                continue
        
        logger.info(f"Toplam {len(profiles)} profil parse edildi")
        return profiles
        
    except Exception as e:
        logger.error(f"Excel parse hatası: {e}")
        raise


def group_by_categories(profiles: List[CatalogProfile]) -> Dict:
    """
    Profilleri kategorilere göre grupla
    
    Returns:
        {
            'standard': {'STANDART BORU': [profiles], ...},
            'shape': {'T': [profiles], ...},
            'sector': {'Pencere': [profiles], ...}
        }
    """
    grouped = {
        'standard': {},
        'shape': {},
        'sector': {}
    }
    
    for profile in profiles:
        for category in profile.categories:
            cat_type = profile.get_category_type(category)
            
            if category not in grouped[cat_type]:
                grouped[cat_type][category] = []
            
            grouped[cat_type][category].append(profile)
    
    return grouped
