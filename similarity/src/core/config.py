"""Configuration management for the application."""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import yaml
from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration."""
    
    # Paths
    image_directory: str = ""
    faiss_index_path: str = "./data/faiss_index.bin"
    metadata_path: str = "./data/profile_metadata.json"
    
    # Model settings
    ai_model: str = "resnet50"  # Options: "resnet18", "resnet50", "ensemble" - resnet50 for best accuracy
    ai_weight: float = 0.3  # Reduced from 0.7 - technical drawings need more geometry
    geo_weight: float = 0.7  # Increased from 0.3 - geometry is more important for profiles
    device: str = "cpu"
    
    # API settings
    host: str = "0.0.0.0"
    port: int = 8000
    top_k_results: int = 30
    
    # Processing settings
    batch_size: int = 32
    num_workers: int = 4
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "[%(asctime)s] %(levelname)s - %(message)s"
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate()
    
    def validate(self):
        """Validate configuration values."""
        # Validate weights sum to 1.0
        total_weight = self.ai_weight + self.geo_weight
        if not (0.99 <= total_weight <= 1.01):  # Allow small floating point errors
            raise ValueError(
                f"AI weight ({self.ai_weight}) + Geo weight ({self.geo_weight}) "
                f"must equal 1.0, got {total_weight}"
            )
        
        # Validate weights are positive
        if self.ai_weight < 0 or self.geo_weight < 0:
            raise ValueError("Weights must be non-negative")
        
        # Validate top_k_results
        if self.top_k_results < 1:
            raise ValueError("top_k_results must be at least 1")
        
        # Validate batch_size
        if self.batch_size < 1:
            raise ValueError("batch_size must be at least 1")
        
        # Validate device
        if self.device not in ["cpu", "cuda"]:
            raise ValueError(f"device must be 'cpu' or 'cuda', got '{self.device}'")
        
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            raise ValueError(
                f"log_level must be one of {valid_levels}, got '{self.log_level}'"
            )
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Config":
        """
        Load configuration from YAML file.
        
        Args:
            yaml_path: Path to YAML configuration file
            
        Returns:
            Config instance
        """
        if not Path(yaml_path).exists():
            raise FileNotFoundError(f"Config file not found: {yaml_path}")
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Flatten nested structure
        config_dict = {}
        
        if 'paths' in data:
            config_dict['image_directory'] = data['paths'].get('image_directory', '')
            config_dict['faiss_index_path'] = data['paths'].get('faiss_index_path', './data/faiss_index.bin')
            config_dict['metadata_path'] = data['paths'].get('metadata_path', './data/profile_metadata.json')
        
        if 'model' in data:
            config_dict['ai_model'] = data['model'].get('ai_model', 'resnet50')
            config_dict['ai_weight'] = data['model'].get('ai_weight', 0.3)
            config_dict['geo_weight'] = data['model'].get('geo_weight', 0.7)
            config_dict['device'] = data['model'].get('device', 'cpu')
        
        if 'api' in data:
            config_dict['host'] = data['api'].get('host', '0.0.0.0')
            config_dict['port'] = data['api'].get('port', 8000)
            config_dict['top_k_results'] = data['api'].get('top_k_results', 30)
        
        if 'processing' in data:
            config_dict['batch_size'] = data['processing'].get('batch_size', 32)
            config_dict['num_workers'] = data['processing'].get('num_workers', 4)
        
        if 'logging' in data:
            config_dict['log_level'] = data['logging'].get('level', 'INFO')
            config_dict['log_format'] = data['logging'].get('format', '[%(asctime)s] %(levelname)s - %(message)s')
        
        return cls(**config_dict)
    
    @classmethod
    def from_env(cls) -> "Config":
        """
        Load configuration from environment variables.
        
        Returns:
            Config instance
        """
        # Load .env file if it exists
        load_dotenv()
        
        return cls(
            image_directory=os.getenv('IMAGE_DIRECTORY') or os.getenv('IMAGE_DIR', ''),
            faiss_index_path=os.getenv('FAISS_INDEX_PATH', './data/faiss_index.bin'),
            metadata_path=os.getenv('METADATA_PATH', './data/profile_metadata.json'),
            ai_model=os.getenv('AI_MODEL', 'resnet50'),  # Default to resnet50 for best accuracy
            ai_weight=float(os.getenv('AI_WEIGHT', '0.3')),
            geo_weight=float(os.getenv('GEO_WEIGHT', '0.7')),
            device=os.getenv('DEVICE', 'cpu'),
            host=os.getenv('API_HOST', '0.0.0.0'),
            port=int(os.getenv('API_PORT', '8000')),
            top_k_results=int(os.getenv('TOP_K_RESULTS', '30')),
            batch_size=int(os.getenv('BATCH_SIZE', '32')),
            num_workers=int(os.getenv('NUM_WORKERS', '4')),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
        )
    
    @classmethod
    def load(cls, yaml_path: Optional[str] = None) -> "Config":
        """
        Load configuration with priority: env vars > yaml file > defaults.
        
        Args:
            yaml_path: Optional path to YAML config file
            
        Returns:
            Config instance
        """
        # Start with defaults
        config = cls()
        
        # Override with YAML if provided
        if yaml_path and Path(yaml_path).exists():
            config = cls.from_yaml(yaml_path)
        
        # Override with environment variables (highest priority)
        load_dotenv()
        
        # Support both IMAGE_DIRECTORY and IMAGE_DIR for flexibility
        if os.getenv('IMAGE_DIRECTORY'):
            config.image_directory = os.getenv('IMAGE_DIRECTORY')
        elif os.getenv('IMAGE_DIR'):
            config.image_directory = os.getenv('IMAGE_DIR')
        if os.getenv('FAISS_INDEX_PATH'):
            config.faiss_index_path = os.getenv('FAISS_INDEX_PATH')
        if os.getenv('METADATA_PATH'):
            config.metadata_path = os.getenv('METADATA_PATH')
        if os.getenv('AI_MODEL'):
            config.ai_model = os.getenv('AI_MODEL')
        if os.getenv('AI_WEIGHT'):
            config.ai_weight = float(os.getenv('AI_WEIGHT'))
        if os.getenv('GEO_WEIGHT'):
            config.geo_weight = float(os.getenv('GEO_WEIGHT'))
        if os.getenv('DEVICE'):
            config.device = os.getenv('DEVICE')
        if os.getenv('API_HOST'):
            config.host = os.getenv('API_HOST')
        if os.getenv('API_PORT'):
            config.port = int(os.getenv('API_PORT'))
        if os.getenv('TOP_K_RESULTS'):
            config.top_k_results = int(os.getenv('TOP_K_RESULTS'))
        if os.getenv('BATCH_SIZE'):
            config.batch_size = int(os.getenv('BATCH_SIZE'))
        if os.getenv('NUM_WORKERS'):
            config.num_workers = int(os.getenv('NUM_WORKERS'))
        if os.getenv('LOG_LEVEL'):
            config.log_level = os.getenv('LOG_LEVEL')
        
        # Validate final configuration
        config.validate()
        
        return config
