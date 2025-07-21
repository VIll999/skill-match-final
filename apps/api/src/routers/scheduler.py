"""
Match Scheduler Management API
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..services.match_scheduler import MatchScheduler
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/scheduler", tags=["scheduler"])

# Configure logging
logger = logging.getLogger(__name__)


class SchedulerStatsResponse(BaseModel):
    """Response model for scheduler statistics"""
    total_matches: int
    recent_matches_24h: int
    users_with_matches: int
    algorithm_breakdown: Dict[str, int]
    similarity_stats: Dict[str, float]
    top_users: list


class RecomputeResponse(BaseModel):
    """Response model for recomputation results"""
    message: str
    total_users: int
    processed_users: int
    failed_users: int
    total_matches: int
    duration_seconds: float
    algorithm: str


class HealthCheckResponse(BaseModel):
    """Response model for health check"""
    status: str
    database_connected: bool
    active_jobs: int
    total_skills: int
    total_users: int
    recent_matches_24h: int
    timestamp: datetime


@router.post("/recompute/all", response_model=RecomputeResponse)
async def recompute_all_matches(
    limit_per_user: int = Query(default=50, ge=1, le=100),
    algorithm: str = Query(default="tfidf", regex="^(tfidf|basic)$"),
    db: Session = Depends(get_db)
):
    """
    Recompute job matches for all users
    
    - **limit_per_user**: Maximum matches per user
    - **algorithm**: Algorithm to use ('tfidf' or 'basic')
    """
    try:
        scheduler = MatchScheduler(db)
        
        # Run recomputation
        stats = await scheduler.recompute_all_matches(limit_per_user, algorithm)
        
        if 'error' in stats:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Recomputation failed: {stats['error']}"
            )
        
        return RecomputeResponse(
            message=f"Recomputed matches for {stats['processed_users']} users",
            total_users=stats['total_users'],
            processed_users=stats['processed_users'],
            failed_users=stats['failed_users'],
            total_matches=stats['total_matches'],
            duration_seconds=stats['duration_seconds'],
            algorithm=stats['algorithm']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in recompute all matches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to recompute matches"
        )


@router.post("/recompute/user/{user_id}")
async def recompute_user_matches(
    user_id: int,
    algorithm: str = Query(default="tfidf", regex="^(tfidf|basic)$"),
    db: Session = Depends(get_db)
):
    """
    Recompute job matches for a specific user
    
    - **user_id**: ID of the user
    - **algorithm**: Algorithm to use ('tfidf' or 'basic')
    """
    try:
        scheduler = MatchScheduler(db)
        
        # Run recomputation
        result = await scheduler.recompute_user_matches(user_id, algorithm)
        
        if 'error' in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Recomputation failed: {result['error']}"
            )
        
        return {
            "message": f"Recomputed {result['matches_saved']} matches for user {user_id}",
            "user_id": result['user_id'],
            "matches_found": result['matches_found'],
            "matches_saved": result['matches_saved'],
            "duration_seconds": result['duration_seconds'],
            "algorithm": result['algorithm'],
            "computed_at": result['computed_at']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in recompute user matches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to recompute user matches"
        )


@router.get("/stats", response_model=SchedulerStatsResponse)
async def get_scheduler_stats(
    db: Session = Depends(get_db)
):
    """Get scheduler and matching statistics"""
    try:
        scheduler = MatchScheduler(db)
        stats = scheduler.get_match_statistics()
        
        if 'error' in stats:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get statistics: {stats['error']}"
            )
        
        return SchedulerStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scheduler stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scheduler statistics"
        )


@router.delete("/cleanup")
async def cleanup_old_matches(
    days_old: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    Clean up old matches
    
    - **days_old**: Delete matches older than this many days
    """
    try:
        scheduler = MatchScheduler(db)
        deleted_count = scheduler.cleanup_old_matches(days_old)
        
        return {
            "message": f"Cleaned up {deleted_count} matches older than {days_old} days",
            "deleted_count": deleted_count,
            "days_old": days_old
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old matches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clean up old matches"
        )


@router.get("/health", response_model=HealthCheckResponse)
async def scheduler_health_check(
    db: Session = Depends(get_db)
):
    """Health check for the matching system"""
    try:
        scheduler = MatchScheduler(db)
        health = await scheduler.health_check()
        
        return HealthCheckResponse(**health)
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            database_connected=False,
            active_jobs=0,
            total_skills=0,
            total_users=0,
            recent_matches_24h=0,
            timestamp=datetime.utcnow()
        )


@router.get("/cron/nightly")
async def run_nightly_cron(
    db: Session = Depends(get_db)
):
    """
    Endpoint for cron job to run nightly match updates
    This should be called by your cron scheduler
    """
    try:
        scheduler = MatchScheduler(db)
        
        # Run nightly recomputation
        stats = await scheduler.recompute_all_matches(algorithm="tfidf")
        
        # Clean up old matches (older than 7 days)
        cleanup_count = scheduler.cleanup_old_matches(days_old=7)
        
        return {
            "message": "Nightly cron job completed successfully",
            "recomputation_stats": stats,
            "cleanup_count": cleanup_count,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error in nightly cron job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nightly cron job failed"
        )