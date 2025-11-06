"""Hybrid similarity engine combining AI and geometric features."""
import cv2
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm

from src.core.config import Config
from src.core.exceptions import ProfileNotFoundError, ImageProcessingError, IndexNotInitializedError
from src.core.logging_config import get_logger
from src.services.ai_embedder import AIEmbedder
from src.services.geometric_extractor import GeometricFeatureExtractor
from src.services.faiss_manager import FAISSIndexManager
from src.models.similarity_result import SimilarityResult

logger = get_logger(__name__)


class HybridSimilarityEngine:
    """Core engine for hybrid similarity search."""
    
    def __init__(self, config: Config):
        """
        Initialize hybrid similarity engine with aggressive calibration and inner contour amplification.
        
        Args:
            config: Application configuration
        """
        self.config = config
        
        # Initialize components
        logger.info("Initializing Hybrid Similarity Engine with aggressive calibration")
        self.ai_embedder = AIEmbedder(
            model_name=config.ai_model,
            device=config.device
        )
        self.geo_extractor = GeometricFeatureExtractor()
        
        # Calculate total dimension based on model
        if config.ai_model == "ensemble":
            ai_dims = 4288  # ResNet50(2048) + EfficientNet(1280) + MobileNetV3(960)
        else:
            ai_dims = 2048  # Single model
        
        total_dims = ai_dims + 55  # AI + 55 geometric features (enhanced with contour matching & shape context)
        
        # Initialize FAISS with aggressive calibration (k=20.0, threshold=0.90)
        self.faiss_manager = FAISSIndexManager(dimension=total_dims)
        
        # Metadata storage
        self.profile_metadata: Dict[str, Dict] = {}
        
        # Weights
        self.ai_weight = config.ai_weight
        self.geo_weight = config.geo_weight
        
        # Inner contour amplification factor
        self.inner_contour_amplification = 3.0
        
        logger.info(
            f"Hybrid engine initialized with weights: "
            f"AI={self.ai_weight}, Geometric={self.geo_weight}, "
            f"Inner contour amplification={self.inner_contour_amplification}x"
        )
        logger.info(
            f"FAISS calibration: k={self.faiss_manager.score_calibration_k}, "
            f"threshold={self.faiss_manager.score_calibration_threshold}"
        )

    def _compute_hybrid_vector(self, image: np.ndarray) -> np.ndarray:
        """
        Compute hybrid vector combining AI embedding and advanced geometric features.
        Applies 3.0x amplification to inner contour features for stronger differentiation.
        
        Args:
            image: Input image as numpy array (H, W, C) in BGR format
            
        Returns:
            Hybrid vector (AI dims + 55 geometric with amplified inner contours & advanced features)
        """
        # Extract AI embedding (ensemble: 4288 dims, single: 2048 dims)
        ai_embedding = self.ai_embedder.extract_embedding(image)
        
        # Extract advanced geometric features (55 dims - with contour matching & shape context)
        geo_features = self.geo_extractor.extract_features(image)
        
        # CRITICAL: Apply 3.0x amplification to inner contour features (indices 10-22)
        # This increases the impact of inner contour differences on similarity scores
        inner_contour_amplification = 3.0
        geo_features_amplified = geo_features.copy()
        geo_features_amplified[10:23] *= inner_contour_amplification
        
        # CRITICAL: Apply 2.0x amplification to contour matching features (indices 45-49)
        # These features capture shape complexity and are important for technical drawings
        contour_matching_amplification = 2.0
        geo_features_amplified[45:50] *= contour_matching_amplification
        
        logger.debug(f"Applied {inner_contour_amplification}x amplification to inner contour features (10-22)")
        logger.debug(f"Applied {contour_matching_amplification}x amplification to contour matching features (45-49)")
        
        # Apply weights (30% AI, 70% geometric - geometry is more important for technical drawings)
        ai_weighted = ai_embedding * self.ai_weight
        geo_weighted = geo_features_amplified * self.geo_weight
        
        # Concatenate into hybrid vector
        hybrid_vector = np.concatenate([ai_weighted, geo_weighted])
        
        logger.debug(f"Hybrid vector: AI={len(ai_embedding)} dims ({self.ai_weight*100}%), "
                    f"Geo={len(geo_features)} dims ({self.geo_weight*100}%), Total={len(hybrid_vector)} dims")
        
        return hybrid_vector
    
    def _extract_profile_code(self, filename: str) -> str:
        """
        Extract profile code from filename.
        
        Args:
            filename: Image filename (e.g., "AP0001.png", "A 3703.png")
            
        Returns:
            Profile code without extension
        """
        return Path(filename).stem

    def initialize(self, force_rebuild: bool = False):
        """
        Initialize the engine by processing all images and building index.
        
        Args:
            force_rebuild: If True, rebuild index even if it exists
        """
        # Check if index already exists
        index_path = Path(self.config.faiss_index_path)
        metadata_path = Path(self.config.metadata_path)
        
        if not force_rebuild and index_path.exists() and metadata_path.exists():
            logger.info("Loading existing index and metadata")
            try:
                self._load_index_and_metadata()
                logger.info(f"Loaded index with {self.faiss_manager.size()} profiles")
                return
            except Exception as e:
                logger.warning(f"Failed to load existing index: {e}. Rebuilding...")
        
        # Build new index
        logger.info("Building new index from images")
        self._build_index_from_images()
    
    def _load_index_and_metadata(self):
        """Load FAISS index and metadata from disk."""
        # Load FAISS index
        self.faiss_manager.load(self.config.faiss_index_path)
        
        # Load metadata
        with open(self.config.metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.profile_metadata = data['profiles']
            self.faiss_manager.profile_codes = data['profile_codes']
        
        logger.info(f"Loaded metadata for {len(self.profile_metadata)} profiles")
    
    def _build_index_from_images(self):
        """Build FAISS index from all images in directory."""
        image_dir = Path(self.config.image_directory)
        
        if not image_dir.exists():
            raise FileNotFoundError(f"Image directory not found: {image_dir}")
        
        # Find all PNG files
        png_files = list(image_dir.glob("*.png"))
        
        if len(png_files) == 0:
            raise ValueError(f"No PNG files found in {image_dir}")
        
        logger.info(f"Found {len(png_files)} PNG files")
        
        # Process images in batches
        all_vectors = []
        all_codes = []
        
        for png_file in tqdm(png_files, desc="Processing images"):
            try:
                # Extract profile code
                profile_code = self._extract_profile_code(png_file.name)
                
                # Load image using numpy to handle Turkish characters
                import numpy as np
                with open(png_file, 'rb') as f:
                    file_bytes = np.frombuffer(f.read(), dtype=np.uint8)
                    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                
                if image is None:
                    logger.warning(f"Failed to load image: {png_file}, skipping")
                    continue
                
                # Compute hybrid vector
                hybrid_vector = self._compute_hybrid_vector(image)
                
                # CRITICAL: Verify vector dimension before adding
                expected_dim = self.faiss_manager.dimension
                if len(hybrid_vector) != expected_dim:
                    logger.error(f"Vector dimension mismatch for {profile_code}: expected {expected_dim}, got {len(hybrid_vector)}, SKIPPING")
                    continue
                
                # Store metadata
                self.profile_metadata[profile_code] = {
                    'file_path': str(png_file),
                    'file_size': png_file.stat().st_size,
                    'image_shape': image.shape
                }
                
                all_vectors.append(hybrid_vector)
                all_codes.append(profile_code)
                
            except Exception as e:
                logger.error(f"Failed to process {png_file}: {e}, SKIPPING")
                continue
        
        if len(all_vectors) == 0:
            raise ValueError("No images were successfully processed")
        
        # Build FAISS index
        vectors_array = np.vstack(all_vectors)
        self.faiss_manager.build_index(vectors_array, all_codes)
        
        # Save index and metadata
        self._save_index_and_metadata()
        
        logger.info(f"Index built with {len(all_codes)} profiles")
    
    def _save_index_and_metadata(self):
        """Save FAISS index and metadata to disk."""
        # Save FAISS index
        self.faiss_manager.save(self.config.faiss_index_path)
        
        # Save metadata
        metadata_path = Path(self.config.metadata_path)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'profile_codes': self.faiss_manager.profile_codes,
            'profiles': self.profile_metadata
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Metadata saved to {metadata_path}")

    def find_similar(self, profile_code: str, top_k: int = 30) -> List[SimilarityResult]:
        """
        Find similar profiles for a given profile code.
        
        Args:
            profile_code: Profile code to search for (case-insensitive)
            top_k: Number of similar profiles to return
            
        Returns:
            List of SimilarityResult objects ranked by similarity
        """
        if self.faiss_manager.size() == 0:
            raise IndexNotInitializedError("Index is not initialized. Call initialize() first.")
        
        # Normalize profile code (case-insensitive search)
        profile_code_upper = profile_code.upper()
        
        # Try to find the actual profile code (case-insensitive)
        actual_profile_code = None
        for code in self.profile_metadata.keys():
            if code.upper() == profile_code_upper:
                actual_profile_code = code
                break
        
        if actual_profile_code is None:
            raise ProfileNotFoundError(f"Profile '{profile_code}' not found in database")
        
        profile_code = actual_profile_code  # Use the actual code from metadata
        
        # Get index of query profile
        try:
            query_index = self.faiss_manager.get_index_by_code(profile_code)
        except ValueError:
            raise ProfileNotFoundError(f"Profile '{profile_code}' not found in index")
        
        # Load query image and compute vector
        profile_info = self.profile_metadata[profile_code]
        
        # Load image using numpy to handle Turkish characters
        with open(profile_info['file_path'], 'rb') as f:
            file_bytes = np.frombuffer(f.read(), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ImageProcessingError(f"Failed to load image for profile '{profile_code}'")
        
        query_vector = self._compute_hybrid_vector(image)
        
        # Search with calibrated scores
        calibrated_scores, indices = self.faiss_manager.search(query_vector, top_k)
        
        # Build results with calibrated scores
        results = []
        for score, index in zip(calibrated_scores, indices):
            if index == query_index:
                continue
            
            result_code = self.faiss_manager.get_profile_code(index)
            
            # Create similarity result with calibrated score
            result = SimilarityResult(
                profile_code=result_code,
                similarity_score=float(score),
                ai_score=0.0,  # Not separately calculated
                geo_score=0.0  # Not separately calculated
            )
            results.append(result)
            
            if len(results) >= top_k:
                break
        
        logger.info(f"Found {len(results)} similar profiles for '{profile_code}' with calibrated scores")
        logger.debug(f"Score range: [{results[-1].similarity_score:.2f}, {results[0].similarity_score:.2f}]")
        
        return results



    def add_profile(self, image_path: str, profile_code: Optional[str] = None):
        """
        Add a new profile to the index.
        
        Args:
            image_path: Path to the image file
            profile_code: Optional profile code (extracted from filename if not provided)
        """
        image_path_obj = Path(image_path)
        
        if not image_path_obj.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Extract profile code if not provided
        if profile_code is None:
            profile_code = self._extract_profile_code(image_path_obj.name)
        
        # Check if profile already exists
        if profile_code in self.profile_metadata:
            logger.warning(f"Profile '{profile_code}' already exists. Skipping.")
            return
        
        # Load image using numpy to handle Turkish characters
        with open(image_path_obj, 'rb') as f:
            file_bytes = np.frombuffer(f.read(), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ImageProcessingError(f"Failed to load image: {image_path}")
        
        # Compute hybrid vector
        hybrid_vector = self._compute_hybrid_vector(image)
        
        # Add to FAISS index
        self.faiss_manager.add_vector(hybrid_vector, profile_code)
        
        # Store metadata
        self.profile_metadata[profile_code] = {
            'file_path': str(image_path_obj),
            'file_size': image_path_obj.stat().st_size,
            'image_shape': image.shape
        }
        
        # Save updated index and metadata
        self._save_index_and_metadata()
        
        logger.info(f"Added profile '{profile_code}' to index")
