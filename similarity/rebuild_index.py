"""Rebuild FAISS index with enhanced features."""
from src.core.config import Config
from src.services.hybrid_engine import HybridSimilarityEngine
from src.core.logging_config import setup_logging
import time

# Setup logging
setup_logging()

# Load config from yaml
config = Config.load(yaml_path="config/config.yaml")

# Initialize engine
print("Initializing Hybrid Similarity Engine with enhanced features...")
print(f"- AI embedding: 2048 dims")
print(f"- Geometric features: 45 dims (13 inner contour features)")
print(f"- Total vector: 2093 dims")
print(f"- Score calibration: enabled (sigmoid k=10.0)")
print()

start_time = time.time()
engine = HybridSimilarityEngine(config)

# Rebuild index
print("Rebuilding index from all images...")
engine.initialize(force_rebuild=True)

elapsed = time.time() - start_time
print(f"\n✓ Index rebuilt successfully in {elapsed:.1f} seconds!")
print(f"✓ Total profiles indexed: {engine.faiss_manager.size()}")
print(f"✓ Index dimension: {engine.faiss_manager.dimension}")
print(f"\nYou can now start the API with: python main.py")
