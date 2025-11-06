"""Main application entry point."""
import uvicorn
from src.api.app import create_app
from src.core.config import Config
from src.core.logging_config import setup_logging, get_logger


def main():
    """Main entry point for the application."""
    # Load configuration
    config = Config.load("config/config.yaml")
    
    # Setup logging
    setup_logging(config.log_level, config.log_format)
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("Aluminum Profile Similarity Search System")
    logger.info("=" * 60)
    logger.info(f"Image directory: {config.image_directory}")
    logger.info(f"AI Model: {config.ai_model}")
    logger.info(f"Device: {config.device}")
    logger.info(f"Weights: AI={config.ai_weight}, Geometric={config.geo_weight}")
    logger.info(f"API: {config.host}:{config.port}")
    logger.info("=" * 60)
    
    # Create FastAPI app
    app = create_app(config)
    
    # Run server
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level=config.log_level.lower()
    )


if __name__ == "__main__":
    main()
