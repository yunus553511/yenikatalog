"""API route handlers."""
import time
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from src.api.models import SimilarityResponse, HealthResponse, FeedbackRequest, FeedbackResponse
from src.core.exceptions import ProfileNotFoundError, ImageProcessingError, IndexNotInitializedError
from src.core.logging_config import get_logger

logger = get_logger(__name__)

# Router will be initialized with dependencies in main.py
router = APIRouter()

# Global references (will be set in main.py)
similarity_engine = None
file_watcher = None
feedback_manager = None


def set_dependencies(engine, watcher, feedback_mgr):
    """Set global dependencies for routes."""
    global similarity_engine, file_watcher, feedback_manager
    similarity_engine = engine
    file_watcher = watcher
    feedback_manager = feedback_mgr


@router.get("/api/similar/{profile_code}", response_model=SimilarityResponse)
async def get_similar_profiles(
    profile_code: str,
    top_k: int = Query(30, ge=1, le=200, description="Number of similar profiles to return")
):
    """
    Find similar aluminum profiles.
    
    Args:
        profile_code: Profile code to search for (e.g., "AP0001", "A 3703")
        top_k: Number of similar profiles to return (default: 30, max: 200)
        
    Returns:
        SimilarityResponse with ranked similar profiles
    """
    start_time = time.time()
    
    try:
        logger.info(f"Similarity search request for profile: {profile_code}")
        
        # Find similar profiles
        results = similarity_engine.find_similar(profile_code, top_k)
        
        # Format results
        formatted_results = [
            {
                "profile_code": result.profile_code,
                "similarity_score": round(result.similarity_score, 2)
            }
            for result in results
        ]
        
        # Filter out dissimilar profiles based on feedback
        if feedback_manager:
            formatted_results = feedback_manager.filter_results(profile_code, formatted_results)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        logger.info(
            f"Found {len(formatted_results)} similar profiles for '{profile_code}' "
            f"in {processing_time:.2f}ms"
        )
        
        return SimilarityResponse(
            query_profile=profile_code,
            results=formatted_results,
            count=len(formatted_results),
            processing_time_ms=round(processing_time, 2)
        )
        
    except ProfileNotFoundError as e:
        logger.warning(f"Profile not found: {profile_code}")
        raise HTTPException(status_code=404, detail=str(e))
        
    except ImageProcessingError as e:
        logger.error(f"Image processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")
        
    except IndexNotInitializedError as e:
        logger.error(f"Index not initialized: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    except Exception as e:
        logger.exception(f"Unexpected error in similarity search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        HealthResponse with system status
    """
    try:
        indexed_count = similarity_engine.faiss_manager.size() if similarity_engine else 0
        watcher_active = file_watcher.is_alive() if file_watcher else False
        
        return HealthResponse(
            status="healthy",
            indexed_profiles=indexed_count,
            watcher_active=watcher_active
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/api/image/{profile_code}")
async def get_profile_image(profile_code: str):
    """
    Get profile image by code.
    
    Args:
        profile_code: Profile code (e.g., "AP0001")
        
    Returns:
        Image file
    """
    from fastapi.responses import FileResponse
    import os
    
    try:
        # Get profile metadata
        if profile_code not in similarity_engine.profile_metadata:
            raise HTTPException(status_code=404, detail=f"Profile '{profile_code}' not found")
        
        # Get image path
        image_path = similarity_engine.profile_metadata[profile_code]['file_path']
        
        # Check if file exists
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail=f"Image file not found for '{profile_code}'")
        
        return FileResponse(image_path, media_type="image/png")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving image: {e}")
        raise HTTPException(status_code=500, detail="Failed to load image")


@router.post("/api/feedback", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackRequest):
    """
    Submit negative feedback for a dissimilar profile.
    
    Args:
        feedback: Feedback data with query and dissimilar profile codes
        
    Returns:
        FeedbackResponse confirming the feedback was saved
    """
    try:
        if not feedback_manager:
            raise HTTPException(status_code=500, detail="Feedback manager not initialized")
        
        # Add negative feedback
        feedback_manager.add_negative_feedback(
            feedback.query_profile,
            feedback.dissimilar_profile
        )
        
        return FeedbackResponse(
            success=True,
            message=f"Feedback saved: {feedback.dissimilar_profile} will not appear for {feedback.query_profile}"
        )
        
    except Exception as e:
        logger.error(f"Failed to save feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to save feedback")
