"""File watcher service for automatic profile indexing."""
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class ProfileImageHandler(FileSystemEventHandler):
    """Handler for profile image file events."""
    
    def __init__(self, watcher_service):
        """
        Initialize handler.
        
        Args:
            watcher_service: Reference to FileWatcherService
        """
        self.watcher_service = watcher_service
        super().__init__()
    
    def on_created(self, event):
        """
        Handle file creation event.
        
        Args:
            event: File system event
        """
        if isinstance(event, FileCreatedEvent) and not event.is_directory:
            file_path = event.src_path
            
            # Check if it's a PNG file
            if file_path.lower().endswith('.png'):
                logger.info(f"New PNG file detected: {file_path}")
                # Small delay to ensure file is fully written
                time.sleep(0.5)
                self.watcher_service.on_new_file(file_path)


class FileWatcherService:
    """Monitor image directory for new PNG files."""
    
    def __init__(self, image_dir: str, similarity_engine):
        """
        Initialize file watcher service.
        
        Args:
            image_dir: Directory to monitor
            similarity_engine: HybridSimilarityEngine instance
        """
        self.image_dir = image_dir
        self.similarity_engine = similarity_engine
        self.observer = Observer()
        self.processed_files = set()
        self.is_running = False
        
        logger.info(f"File watcher initialized for directory: {image_dir}")

    def on_new_file(self, file_path: str):
        """
        Process newly added PNG file.
        
        Args:
            file_path: Path to the new file
        """
        # Check if already processed
        if file_path in self.processed_files:
            logger.debug(f"File already processed: {file_path}")
            return
        
        try:
            # Verify file exists and is readable
            path_obj = Path(file_path)
            if not path_obj.exists():
                logger.warning(f"File does not exist: {file_path}")
                return
            
            # Add to similarity engine
            logger.info(f"Processing new profile: {file_path}")
            self.similarity_engine.add_profile(file_path)
            
            # Mark as processed
            self.processed_files.add(file_path)
            
            logger.info(f"Successfully indexed new profile from {path_obj.name}")
            
        except Exception as e:
            logger.error(f"Failed to process new file {file_path}: {e}")

    def start(self):
        """Start watching directory for new files."""
        if self.is_running:
            logger.warning("File watcher is already running")
            return
        
        try:
            # Verify directory exists
            if not Path(self.image_dir).exists():
                logger.error(f"Directory does not exist: {self.image_dir}")
                return
            
            # Set up event handler
            event_handler = ProfileImageHandler(self)
            self.observer.schedule(event_handler, self.image_dir, recursive=False)
            
            # Start observer
            self.observer.start()
            self.is_running = True
            
            logger.info(f"File watcher started for directory: {self.image_dir}")
            
        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}")
            raise
    
    def stop(self):
        """Stop watching directory."""
        if not self.is_running:
            logger.warning("File watcher is not running")
            return
        
        try:
            self.observer.stop()
            self.observer.join(timeout=5)
            self.is_running = False
            
            logger.info("File watcher stopped")
            
        except Exception as e:
            logger.error(f"Error stopping file watcher: {e}")
    
    def is_alive(self) -> bool:
        """
        Check if watcher is running.
        
        Returns:
            True if watcher is running
        """
        return self.is_running and self.observer.is_alive()
