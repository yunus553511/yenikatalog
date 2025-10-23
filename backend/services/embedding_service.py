import pickle
from pathlib import Path
from typing import List, Tuple
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import settings
from models.profile import Profile

logger = logging.getLogger(__name__)


class EmbeddingService:
    """TF-IDF tabanlı embedding servisi"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 2),
            min_df=1
        )
        self.profiles: List[Profile] = []
        self.embeddings = None
        self.is_ready = False
        
        # Persist klasörünü oluştur
        self.persist_dir = Path(settings.chroma_persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.vectorizer_path = self.persist_dir / "vectorizer.pkl"
        self.embeddings_path = self.persist_dir / "embeddings.pkl"
    
    async def initialize(self, profiles: List[Profile]) -> bool:
        """
        Embedding servisini başlat
        
        Args:
            profiles: Profile listesi
            
        Returns:
            Başarılı ise True
        """
        logger.info("Embedding servisi başlatılıyor...")
        
        try:
            self.profiles = profiles
            
            # Profilleri text'e çevir
            texts = [p.to_embedding_text() for p in profiles]
            
            # TF-IDF embeddings oluştur
            logger.info(f"{len(texts)} profil için embedding oluşturuluyor...")
            self.embeddings = self.vectorizer.fit_transform(texts)
            
            # Kaydet
            self._save_to_disk()
            
            self.is_ready = True
            logger.info(f"Embedding servisi hazır: {self.embeddings.shape}")
            return True
            
        except Exception as e:
            logger.error(f"Embedding servisi başlatma hatası: {e}")
            return False
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[Profile, float]]:
        """
        Sorguya en benzer profilleri bul
        
        Args:
            query: Arama sorgusu
            top_k: Döndürülecek sonuç sayısı
            
        Returns:
            (Profile, similarity_score) tuple listesi
        """
        if not self.is_ready:
            logger.warning("Embedding servisi hazır değil")
            return []
        
        try:
            # Query'yi embedding'e çevir
            query_embedding = self.vectorizer.transform([query])
            
            # Cosine similarity hesapla
            similarities = cosine_similarity(query_embedding, self.embeddings)[0]
            
            # En yüksek skorları bul
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            # Threshold uygula
            threshold = settings.rag_similarity_threshold
            results = []
            
            for idx in top_indices:
                score = float(similarities[idx])
                if score >= threshold:
                    results.append((self.profiles[idx], score))
            
            logger.info(f"Arama: '{query[:50]}...' -> {len(results)} sonuç")
            return results
            
        except Exception as e:
            logger.error(f"Arama hatası: {e}")
            return []
    
    def search_by_code(self, code: str) -> List[Tuple[Profile, float]]:
        """
        Profil koduna göre ara
        
        Args:
            code: Profil kodu
            
        Returns:
            (Profile, similarity_score) tuple listesi
        """
        query = f"Profil Kodu: {code}"
        return self.search(query, top_k=3)
    
    def search_by_category(self, category: str) -> List[Tuple[Profile, float]]:
        """
        Kategoriye göre ara
        
        Args:
            category: Kategori adı
            
        Returns:
            (Profile, similarity_score) tuple listesi
        """
        query = f"Kategori: {category}"
        return self.search(query, top_k=10)
    
    def _save_to_disk(self):
        """Vectorizer ve embeddings'i diske kaydet"""
        try:
            # Vectorizer'ı kaydet
            with open(self.vectorizer_path, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            
            # Embeddings'i kaydet
            with open(self.embeddings_path, 'wb') as f:
                pickle.dump(self.embeddings, f)
            
            logger.info("Embeddings diske kaydedildi")
            
        except Exception as e:
            logger.error(f"Diske kaydetme hatası: {e}")
    
    def load_from_disk(self) -> bool:
        """Vectorizer ve embeddings'i diskten yükle"""
        try:
            if not self.vectorizer_path.exists() or not self.embeddings_path.exists():
                logger.warning("Disk'te kaydedilmiş embedding bulunamadı")
                return False
            
            # Vectorizer'ı yükle
            with open(self.vectorizer_path, 'rb') as f:
                self.vectorizer = pickle.load(f)
            
            # Embeddings'i yükle
            with open(self.embeddings_path, 'rb') as f:
                self.embeddings = pickle.load(f)
            
            self.is_ready = True
            logger.info("Embeddings diskten yüklendi")
            return True
            
        except Exception as e:
            logger.error(f"Diskten yükleme hatası: {e}")
            return False
    
    def get_stats(self) -> dict:
        """İstatistikleri döner"""
        return {
            "is_ready": self.is_ready,
            "total_profiles": len(self.profiles),
            "embedding_shape": str(self.embeddings.shape) if self.embeddings is not None else None,
            "vectorizer_features": self.vectorizer.max_features,
            "persist_dir": str(self.persist_dir)
        }


# Global instance
embedding_service = EmbeddingService()
