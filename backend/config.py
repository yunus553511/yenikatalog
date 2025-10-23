from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # LM Studio Configuration
    lm_studio_url: str = "http://localhost:1234"
    lm_studio_model: str = "local-model"
    
    # Google Drive Configuration
    google_drive_file_id: str = "1RcUAmXf7VNqzh7Pv1Zo8zoQ7zuf2_t3FJXkT_tCLixw"
    
    # Vector Database Configuration
    vector_db_type: str = "chromadb"
    chroma_persist_dir: str = "./data/chroma"
    
    # Application Configuration
    app_host: str = "0.0.0.0"
    app_port: int = 8001
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    
    # Embedding Configuration
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    embedding_batch_size: int = 50
    
    # RAG Configuration
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.0
    
    # Cache Configuration
    excel_cache_path: str = "./data/cache/standart.xlsx"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS origins string to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()
