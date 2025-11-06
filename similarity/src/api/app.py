"""FastAPI application setup."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from src.api.routes import router, set_dependencies
from src.core.config import Config
from src.core.logging_config import setup_logging, get_logger
from src.services.hybrid_engine import HybridSimilarityEngine
from src.services.file_watcher import FileWatcherService
from src.services.feedback_manager import FeedbackManager

# Global instances
similarity_engine = None
file_watcher = None
feedback_manager = None
logger = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance
    """
    global similarity_engine, file_watcher, feedback_manager, logger
    
    # Startup
    logger.info("Starting Aluminum Profile Similarity API")
    
    # Load configuration
    config = Config.load("config/config.yaml")
    
    # Initialize similarity engine
    logger.info("Initializing similarity engine...")
    similarity_engine = HybridSimilarityEngine(config)
    similarity_engine.initialize()
    
    # Initialize feedback manager
    logger.info("Initializing feedback manager...")
    feedback_manager = FeedbackManager()
    
    # Initialize file watcher
    logger.info("Starting file watcher...")
    file_watcher = FileWatcherService(
        config.image_directory,
        similarity_engine
    )
    file_watcher.start()
    
    # Set dependencies for routes
    set_dependencies(similarity_engine, file_watcher, feedback_manager)
    
    logger.info("API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API")
    
    if file_watcher:
        file_watcher.stop()
    
    logger.info("API shutdown complete")


def create_app(config: Config = None) -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Args:
        config: Optional configuration (loads from file if not provided)
        
    Returns:
        Configured FastAPI application
    """
    global logger
    
    # Load config if not provided
    if config is None:
        config = Config.load("config/config.yaml")
    
    # Setup logging
    setup_logging(config.log_level, config.log_format)
    logger = get_logger(__name__)
    
    # Create FastAPI app
    app = FastAPI(
        title="Aluminum Profile Similarity API",
        description="AI-powered similarity search for aluminum profile cross-sections",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes first (they have priority)
    app.include_router(router)
    
    # Mount static files last (catch-all)
    try:
        app.mount("/", StaticFiles(directory="static", html=True), name="static")
    except Exception as e:
        logger.warning(f"Could not mount static files: {e}")
    
    return app
