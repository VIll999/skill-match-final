"""
Simplified Job Matching Service
"""
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class JobMatchingService:
    """Simplified job matching service for development"""
    
    def __init__(self, db: Session):
        self.db = db
        logger.info("Using simplified JobMatchingService")
    
    def compute_matches(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Return empty matches for now
        """
        logger.warning("Job matching not implemented in simple mode")
        return []
    
    def compute_similarity(self, user_skills: List[str], job_skills: List[str]) -> float:
        """
        Simple Jaccard similarity
        """
        if not user_skills or not job_skills:
            return 0.0
        
        user_set = set(user_skills)
        job_set = set(job_skills)
        
        intersection = len(user_set & job_set)
        union = len(user_set | job_set)
        
        return intersection / union if union > 0 else 0.0