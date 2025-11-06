"""Custom exceptions for the application."""


class ProfileNotFoundError(Exception):
    """Raised when a profile code is not found."""
    pass


class ImageProcessingError(Exception):
    """Raised when image processing fails."""
    pass


class IndexNotInitializedError(Exception):
    """Raised when FAISS index is not initialized."""
    pass
