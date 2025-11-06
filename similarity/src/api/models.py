"""API request and response models."""
from typing import List, Dict, Union
from pydantic import BaseModel, Field


class SimilarityResponse(BaseModel):
    """Response model for similarity search."""
    query_profile: str = Field(..., description="Profile code that was queried")
    results: List[Dict[str, Union[str, float]]] = Field(..., description="List of similar profiles")
    count: int = Field(..., description="Number of results returned")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str = Field(..., description="Error type")
    error_code: str = Field(..., description="Error code")
    detail: str = Field(..., description="Detailed error message")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    indexed_profiles: int = Field(..., description="Number of indexed profiles")
    watcher_active: bool = Field(..., description="Whether file watcher is active")


class FeedbackRequest(BaseModel):
    """Request model for negative feedback."""
    query_profile: str = Field(..., description="Profile code that was queried")
    dissimilar_profile: str = Field(..., description="Profile code marked as dissimilar")


class FeedbackResponse(BaseModel):
    """Response model for feedback submission."""
    success: bool = Field(..., description="Whether feedback was saved")
    message: str = Field(..., description="Response message")
