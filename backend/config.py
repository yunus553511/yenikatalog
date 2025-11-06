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
    app_port: int = 8004
    cors_origins: str = "http://localhost:3000,http://localhost:4000,http://localhost:8000,http://localhost:8080"
    
    # Embedding Configuration
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    embedding_batch_size: int = 50
    
    # RAG Configuration
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.0
    
    # Cache Configuration
    excel_cache_path: str = "./data/cache/standart.xlsx"
    
    # Groq LLM Configuration
    groq_api_key: str = ""
    groq_model: str = "llama3-groq-70b-8192-tool-use-preview"  # Function calling için optimize edilmiş model
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_timeout: int = 10
    groq_temperature: float = 0.7
    groq_max_tokens: int = 1000
    llm_enabled: bool = True
    
    # Supabase Configuration
    supabase_url: str = ""  # https://xxxxx.supabase.co
    supabase_key: str = ""  # Optional - public bucket için gerekli değil
    
    # Similarity API Configuration
    similarity_api_url: str = "http://localhost:8003"  # Benzerlik API URL'i
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS origins string to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_llm_available(self) -> bool:
        """LLM kullanılabilir mi?"""
        return self.llm_enabled and bool(self.groq_api_key)


# Global settings instance
settings = Settings()
