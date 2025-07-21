"""
Job Matching and Gap Analysis API Endpoints
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..models.user import User
from ..models.job import JobPosting
try:
    from ..services.job_matching import JobMatchingService
except ImportError:
    from ..services.job_matching_simple import JobMatchingService

try:
    from ..services.tfidf_matching import TFIDFJobMatcher
except ImportError:
    TFIDFJobMatcher = None
from pydantic import BaseModel, Field

router = APIRouter(tags=["matching"])

# Configure logging
logger = logging.getLogger(__name__)


class JobMatchResponse(BaseModel):
    """Response model for job matches"""
    match_id: Optional[int] = None
    job_id: int
    job_title: str
    job_company: str
    job_location: str
    job_source: str
    similarity_score: float
    jaccard_score: float
    cosine_score: float
    weighted_score: float
    skill_coverage: float
    matching_skills: List[str]
    missing_skills: List[str]
    total_job_skills: int
    total_user_skills: int
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    experience_level: Optional[str] = None
    computed_at: Optional[str] = None


class SkillGapDetail(BaseModel):
    """Detailed skill gap information"""
    skill_id: str
    skill_name: str
    skill_type: str
    gap_type: str
    importance: float
    user_proficiency: Optional[float] = None
    required_proficiency: float
    priority: str
    learning_resources: List[Dict[str, str]] = []
    estimated_learning_time: Optional[int] = None


class SkillGapResponse(BaseModel):
    """Response model for skill gap analysis"""
    match_id: Optional[int] = None
    job_id: int
    user_id: int
    similarity_score: float
    skill_coverage: float
    gaps_by_category: Dict[str, List[SkillGapDetail]]
    total_gaps: int
    high_priority_gaps: int
    medium_priority_gaps: int
    low_priority_gaps: int


class MatchingStatsResponse(BaseModel):
    """Response model for matching statistics"""
    total_matches: int
    avg_similarity: float
    high_matches: int
    medium_matches: int
    low_matches: int
    best_match_score: float


@router.post("/{user_id}")
async def compute_job_matches(
    user_id: int,
    limit: int = Query(default=100, ge=1, le=5000),
    save_results: bool = Query(default=True),
    algorithm: str = Query(default="basic", regex="^(tfidf|basic)$"),
    db: Session = Depends(get_db)
):
    """
    Compute job matches for a user
    
    - **user_id**: ID of the user
    - **limit**: Maximum number of matches to return
    - **save_results**: Whether to save matches to database
    - **algorithm**: Matching algorithm to use ('tfidf' or 'basic')
    """
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Initialize matching service based on algorithm
        if algorithm == "tfidf":
            matcher = TFIDFJobMatcher(db)
            matches = matcher.compute_matches(user_id, limit)
        else:
            matching_service = JobMatchingService(db)
            matches = matching_service.match_user_to_jobs(user_id, limit)
        
        if not matches:
            return JSONResponse(
                status_code=200,
                content={
                    "message": "No matches found",
                    "matches": [],
                    "total_matches": 0
                }
            )
        
        # Save matches if requested
        saved_count = 0
        if save_results:
            if algorithm == "tfidf":
                saved_count = matcher.save_matches(user_id, matches)
            else:
                saved_count = matching_service.save_job_matches(user_id, matches)
        
        # Convert to response format
        response_matches = []
        for match in matches:
            response_matches.append(JobMatchResponse(**match))
        
        return {
            "message": f"Found {len(matches)} job matches",
            "matches": response_matches,
            "total_matches": len(matches),
            "saved_matches": saved_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error computing job matches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute job matches"
        )


@router.get("/{user_id}", response_model=List[JobMatchResponse])
async def get_job_matches(
    user_id: int,
    limit: int = Query(default=100, ge=1, le=5000),
    db: Session = Depends(get_db)
):
    """
    Get saved job matches for a user (sorted by similarity score desc)
    
    - **user_id**: ID of the user
    - **limit**: Maximum number of matches to return
    """
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get matches
        matching_service = JobMatchingService(db)
        matches = matching_service.get_job_matches(user_id, limit)
        
        # Convert to response format
        response_matches = []
        for match in matches:
            response_matches.append(JobMatchResponse(**match))
        
        return response_matches
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job matches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job matches"
        )


@router.get("/skills/gaps/{job_id}/{user_id}", response_model=SkillGapResponse)
async def get_skill_gaps(
    job_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get skill gap analysis for a specific job match (calculated on-the-fly)
    
    - **job_id**: ID of the job
    - **user_id**: ID of the user
    """
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate job exists
        job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Calculate skill gaps dynamically
        matching_service = JobMatchingService(db)
        gaps = matching_service.calculate_skill_gaps_dynamic(user_id, job_id)
        
        # Convert gaps_by_category to proper format
        formatted_gaps = {}
        for category, gap_list in gaps['gaps_by_category'].items():
            formatted_gaps[category] = [
                SkillGapDetail(**gap_data) for gap_data in gap_list
            ]
        
        response = SkillGapResponse(
            match_id=None,  # No saved match required
            job_id=gaps['job_id'],
            user_id=gaps['user_id'],
            similarity_score=gaps['similarity_score'],
            skill_coverage=gaps['skill_coverage'],
            gaps_by_category=formatted_gaps,
            total_gaps=gaps['total_gaps'],
            high_priority_gaps=gaps['high_priority_gaps'],
            medium_priority_gaps=gaps['medium_priority_gaps'],
            low_priority_gaps=gaps['low_priority_gaps']
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skill gaps: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get skill gaps"
        )


@router.get("/stats/{user_id}", response_model=MatchingStatsResponse)
async def get_matching_stats(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get matching statistics for a user
    
    - **user_id**: ID of the user
    """
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get stats
        matching_service = JobMatchingService(db)
        stats = matching_service.get_matching_stats(user_id)
        
        return MatchingStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting matching stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get matching statistics"
        )


@router.get("/jobs/{job_id}/matches")
async def get_job_candidates(
    job_id: int,
    limit: int = Query(default=20, ge=1, le=5000),
    min_similarity: float = Query(default=0.3, ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    """
    Get candidates for a specific job (reverse matching)
    
    - **job_id**: ID of the job
    - **limit**: Maximum number of candidates to return
    - **min_similarity**: Minimum similarity score threshold
    """
    try:
        # Validate job exists
        job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Get all users with matches for this job
        from ..models.user import JobMatch
        
        job_matches = db.query(JobMatch).filter(
            JobMatch.job_id == job_id,
            JobMatch.similarity_score >= min_similarity
        ).order_by(JobMatch.similarity_score.desc()).limit(limit).all()
        
        candidates = []
        for match in job_matches:
            user = db.query(User).filter(User.id == match.user_id).first()
            if user:
                candidates.append({
                    "user_id": user.id,
                    "user_name": user.full_name,
                    "user_email": user.email,
                    "similarity_score": match.similarity_score,
                    "jaccard_score": match.jaccard_score,
                    "cosine_score": match.cosine_score,
                    "weighted_score": match.weighted_score,
                    "skill_coverage": match.skill_coverage,
                    "matching_skills": match.matching_skills,
                    "missing_skills": match.missing_skills,
                    "computed_at": match.computed_at.isoformat() if match.computed_at else None
                })
        
        return {
            "job_id": job_id,
            "job_title": job.title,
            "job_company": job.company,
            "candidates": candidates,
            "total_candidates": len(candidates)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job candidates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job candidates"
        )


@router.delete("/{user_id}")
async def clear_job_matches(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Clear all job matches for a user
    
    - **user_id**: ID of the user
    """
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Delete matches
        from ..models.user import JobMatch
        deleted_count = db.query(JobMatch).filter(JobMatch.user_id == user_id).delete()
        db.commit()
        
        return {
            "message": f"Cleared {deleted_count} job matches for user {user_id}",
            "deleted_count": deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing job matches: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear job matches"
        )


@router.get("/features/importance")
async def get_feature_importance(
    top_n: int = Query(default=20, ge=1, le=5000),
    db: Session = Depends(get_db)
):
    """
    Get TF-IDF feature importance for skills
    
    - **top_n**: Number of top features to return
    """
    try:
        # Initialize TF-IDF matcher
        matcher = TFIDFJobMatcher(db)
        
        # Get feature importance
        importance = matcher.get_feature_importance(top_n)
        
        return {
            "message": f"Top {len(importance)} important features",
            "features": importance,
            "total_features": len(importance)
        }
        
    except Exception as e:
        logger.error(f"Error getting feature importance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get feature importance"
        )