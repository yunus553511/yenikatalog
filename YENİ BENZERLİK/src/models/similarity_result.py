"""Data models for similarity search results."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class SimilarityResult:
    """Result of a similarity search."""
    profile_code: str
    similarity_score: float  # 0-100
    ai_score: Optional[float] = None
    geo_score: Optional[float] = None
