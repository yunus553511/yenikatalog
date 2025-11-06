"""Manage user feedback for dissimilar profiles."""
import json
from pathlib import Path
from typing import Set, Dict
from threading import Lock
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class FeedbackManager:
    """Manage negative feedback to filter out dissimilar profiles."""
    
    def __init__(self, feedback_path: str = "./data/feedback.json"):
        """
        Initialize feedback manager.
        
        Args:
            feedback_path: Path to feedback JSON file
        """
        self.feedback_path = Path(feedback_path)
        self.feedback_data: Dict[str, Set[str]] = {}
        self.lock = Lock()
        
        # Load existing feedback
        self._load_feedback()
    
    def _load_feedback(self):
        """Load feedback from disk."""
        if self.feedback_path.exists():
            try:
                with open(self.feedback_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert lists to sets for faster lookup
                self.feedback_data = {
                    query: set(dissimilar_list)
                    for query, dissimilar_list in data.items()
                }
                
                total_feedback = sum(len(v) for v in self.feedback_data.values())
                logger.info(f"Loaded {total_feedback} feedback entries for {len(self.feedback_data)} profiles")
                
            except Exception as e:
                logger.error(f"Failed to load feedback: {e}")
                self.feedback_data = {}
        else:
            logger.info("No existing feedback file found, starting fresh")
            self.feedback_data = {}
    
    def _save_feedback(self):
        """Save feedback to disk."""
        try:
            # Ensure directory exists
            self.feedback_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert sets to lists for JSON serialization
            data = {
                query: list(dissimilar_set)
                for query, dissimilar_set in self.feedback_data.items()
            }
            
            with open(self.feedback_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Feedback saved to {self.feedback_path}")
            
        except Exception as e:
            logger.error(f"Failed to save feedback: {e}")
    
    def add_negative_feedback(self, query_profile: str, dissimilar_profile: str):
        """
        Add negative feedback for a profile pair.
        
        Args:
            query_profile: The profile that was queried
            dissimilar_profile: The profile marked as dissimilar
        """
        with self.lock:
            if query_profile not in self.feedback_data:
                self.feedback_data[query_profile] = set()
            
            self.feedback_data[query_profile].add(dissimilar_profile)
            self._save_feedback()
            
            logger.info(f"Added negative feedback: {query_profile} -> {dissimilar_profile}")
    
    def get_dissimilar_profiles(self, query_profile: str) -> Set[str]:
        """
        Get all profiles marked as dissimilar for a query.
        
        Args:
            query_profile: The profile being queried
            
        Returns:
            Set of profile codes marked as dissimilar
        """
        return self.feedback_data.get(query_profile, set())
    
    def filter_results(self, query_profile: str, results: list) -> list:
        """
        Filter out dissimilar profiles from results.
        
        Args:
            query_profile: The profile being queried
            results: List of result dictionaries with 'profile_code' key
            
        Returns:
            Filtered list of results
        """
        dissimilar = self.get_dissimilar_profiles(query_profile)
        
        if not dissimilar:
            return results
        
        filtered = [r for r in results if r['profile_code'] not in dissimilar]
        
        removed_count = len(results) - len(filtered)
        if removed_count > 0:
            logger.info(f"Filtered out {removed_count} dissimilar profiles for {query_profile}")
        
        return filtered
    
    def get_stats(self) -> Dict:
        """Get feedback statistics."""
        total_queries = len(self.feedback_data)
        total_feedback = sum(len(v) for v in self.feedback_data.values())
        
        return {
            'total_queries_with_feedback': total_queries,
            'total_negative_feedback': total_feedback
        }
