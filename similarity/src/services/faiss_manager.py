"""FAISS index management for efficient similarity search."""
import faiss
import numpy as np
from pathlib import Path
from typing import List, Tuple
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class FAISSIndexManager:
    """Manage FAISS index for fast similarity search."""
    
    def __init__(self, dimension: int = 2093):
        """
        Initialize FAISS index manager with aggressive score calibration.
        
        Args:
            dimension: Dimension of feature vectors (2048 AI + 45 geometric = 2093)
        """
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product for cosine similarity
        self.profile_codes = []
        
        # Aggressive score calibration parameters (updated for stricter scoring)
        self.score_calibration_k = 20.0  # Steepness of sigmoid (increased from 15.0 for more aggressive calibration)
        self.score_calibration_threshold = 0.90  # Center point of sigmoid (increased from 0.85 for lower scores)
        
        logger.info(f"FAISS index manager initialized with dimension {dimension}")
        logger.info(f"Aggressive score calibration: k={self.score_calibration_k}, threshold={self.score_calibration_threshold}")
    
    def build_index(self, vectors: np.ndarray, profile_codes: List[str]):
        """
        Build FAISS index from vectors.
        
        Args:
            vectors: Array of feature vectors with shape (num_vectors, dimension)
            profile_codes: List of profile codes corresponding to vectors
        """
        if len(vectors) != len(profile_codes):
            raise ValueError(
                f"Number of vectors ({len(vectors)}) must match "
                f"number of profile codes ({len(profile_codes)})"
            )
        
        if vectors.shape[1] != self.dimension:
            raise ValueError(
                f"Vector dimension ({vectors.shape[1]}) must match "
                f"index dimension ({self.dimension})"
            )
        
        logger.info(f"Building FAISS index with {len(vectors)} vectors")
        
        # Normalize vectors for cosine similarity
        vectors_normalized = vectors.astype(np.float32)
        faiss.normalize_L2(vectors_normalized)
        
        # Add to index
        self.index.add(vectors_normalized)
        self.profile_codes = profile_codes.copy()
        
        logger.info(f"FAISS index built successfully with {self.index.ntotal} vectors")
    
    def search(self, query_vector: np.ndarray, k: int = 30) -> Tuple[np.ndarray, np.ndarray]:
        """
        Search k nearest neighbors with calibrated similarity scores.
        
        Args:
            query_vector: Query feature vector with shape (dimension,) or (1, dimension)
            k: Number of nearest neighbors to return
            
        Returns:
            Tuple of (calibrated_scores, indices) arrays
            - calibrated_scores: Calibrated similarity scores (0-100%)
            - indices: Indices of nearest neighbors in the index
        """
        if self.index.ntotal == 0:
            raise ValueError("Index is empty. Build index first.")
        
        # Reshape if needed
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        
        # Normalize query vector
        query_normalized = query_vector.astype(np.float32)
        faiss.normalize_L2(query_normalized)
        
        # Search for k+1 to account for the query itself
        search_k = min(k + 1, self.index.ntotal)
        raw_distances, indices = self.index.search(query_normalized, search_k)
        
        # Apply score calibration to prevent inflation
        calibrated_scores = self._calibrate_scores(raw_distances[0])
        
        return calibrated_scores, indices[0]
    
    def _calibrate_scores(self, raw_distances: np.ndarray) -> np.ndarray:
        """
        Apply aggressive non-linear calibration to prevent score inflation.
        
        Uses sigmoid transformation to spread out similarity distribution:
        score = 100 / (1 + exp(-k * (distance - threshold)))
        
        With aggressive parameters (k=20.0, threshold=0.90), this ensures:
        - Distinct profiles: < 60%
        - Moderately similar: 60-80%
        - Highly similar: > 80%
        - Average similarity: < 65%
        
        Args:
            raw_distances: Raw cosine similarity scores from FAISS (0-1 range)
            
        Returns:
            Calibrated scores in 0-100% range
        """
        # Convert cosine similarity (0-1) to calibrated percentage (0-100)
        # Apply AGGRESSIVE calibration with k=20.0 and threshold=0.90
        # Formula: score = 100 * (1 / (1 + exp(-k * (distance - threshold))))
        calibrated = 100 * (1 / (1 + np.exp(-self.score_calibration_k * 
                                            (raw_distances - self.score_calibration_threshold))))
        
        # Clip to valid range
        calibrated = np.clip(calibrated, 0.0, 100.0)
        
        # Calculate average for monitoring
        avg_score = np.mean(calibrated)
        
        logger.debug(f"Aggressive score calibration: raw range [{raw_distances.min():.4f}, {raw_distances.max():.4f}] "
                    f"-> calibrated range [{calibrated.min():.2f}, {calibrated.max():.2f}], avg={avg_score:.2f}%")
        
        # Warn if average is too high
        if avg_score > 65.0:
            logger.warning(f"Average similarity score ({avg_score:.2f}%) exceeds target threshold (65%). "
                          f"Consider increasing calibration parameters.")
        
        return calibrated
    
    def get_profile_code(self, index: int) -> str:
        """
        Get profile code by index.
        
        Args:
            index: Index in the FAISS index
            
        Returns:
            Profile code string
        """
        if index < 0 or index >= len(self.profile_codes):
            raise IndexError(f"Index {index} out of range [0, {len(self.profile_codes)})")
        
        return self.profile_codes[index]
    
    def get_index_by_code(self, profile_code: str) -> int:
        """
        Get index by profile code.
        
        Args:
            profile_code: Profile code string
            
        Returns:
            Index in the FAISS index
        """
        try:
            return self.profile_codes.index(profile_code)
        except ValueError:
            raise ValueError(f"Profile code '{profile_code}' not found in index")
    
    def save(self, filepath: str):
        """
        Persist index to disk.
        
        Args:
            filepath: Path to save the index file
        """
        try:
            # Create directory if it doesn't exist
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.index, filepath)
            
            logger.info(f"FAISS index saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")
            raise
    
    def load(self, filepath: str):
        """
        Load index from disk.
        
        Args:
            filepath: Path to the index file
        """
        try:
            if not Path(filepath).exists():
                raise FileNotFoundError(f"Index file not found: {filepath}")
            
            # Load FAISS index
            self.index = faiss.read_index(filepath)
            
            logger.info(f"FAISS index loaded from {filepath} with {self.index.ntotal} vectors")
            
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            raise
    
    def add_vector(self, vector: np.ndarray, profile_code: str):
        """
        Add a single vector to the index incrementally.
        
        Args:
            vector: Feature vector with shape (dimension,) or (1, dimension)
            profile_code: Profile code for the vector
        """
        # Reshape if needed
        if vector.ndim == 1:
            vector = vector.reshape(1, -1)
        
        if vector.shape[1] != self.dimension:
            raise ValueError(
                f"Vector dimension ({vector.shape[1]}) must match "
                f"index dimension ({self.dimension})"
            )
        
        # Normalize vector
        vector_normalized = vector.astype(np.float32)
        faiss.normalize_L2(vector_normalized)
        
        # Add to index
        self.index.add(vector_normalized)
        self.profile_codes.append(profile_code)
        
        logger.debug(f"Added vector for profile {profile_code} to index")
    
    def size(self) -> int:
        """
        Get the number of vectors in the index.
        
        Returns:
            Number of vectors
        """
        return self.index.ntotal
