"""API endpoints for skill demand analysis"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..db.database import get_db
from ..services.skill_demand_service import SkillDemandService
from ..services.skill_alignment_service import SkillAlignmentService
from pydantic import BaseModel, Field

router = APIRouter(prefix="/skill-demand", tags=["skill-demand"])
logger = logging.getLogger(__name__)


class SkillDemandResponse(BaseModel):
    """Response model for skill demand data"""
    skill_id: str  # Changed to string for EMSI IDs
    skill_name: str
    skill_type: str
    category_name: str
    total_postings: int
    source_count: int
    avg_importance: float
    postings_last_30_days: int
    postings_last_7_days: int


class SkillTrendResponse(BaseModel):
    """Response model for skill trend data"""
    day: str
    skill_name: str
    postings: int
    avg_importance: float
    source: str


class TrendingSkillResponse(BaseModel):
    """Response model for trending skills"""
    skill_id: str  # Changed to string for EMSI IDs
    skill_name: str
    skill_type: str
    recent_postings: int
    older_postings: int
    growth_rate: float


class MarketInsightsResponse(BaseModel):
    """Response model for market insights"""
    total_jobs: int
    total_skills: int
    top_categories: List[dict]
    recent_activity: dict
    last_updated: str


class JobCategoryResponse(BaseModel):
    """Response model for job categories"""
    category_name: str
    total_jobs: int
    percentage: float


class AlignmentTimelineResponse(BaseModel):
    """Response model for skill alignment timeline"""
    date: str
    industries: dict  # Industry name -> alignment data


class IndustryAlignmentData(BaseModel):
    """Response model for industry alignment data"""
    alignment_score: float
    skill_coverage: float
    matched_skills: int
    total_industry_skills: int


class SkillAlignmentHistoryResponse(BaseModel):
    """Response model for complete skill alignment history"""
    user_id: int
    timeline_data: List[AlignmentTimelineResponse]
    top_industries: List[str]
    date_range: dict


@router.get("/top-skills", response_model=List[SkillDemandResponse])
def get_top_skills(
    limit: int = Query(default=20, ge=1, le=100),
    category: Optional[str] = Query(default=None),
    job_category: Optional[str] = Query(default=None),
    days_back: Optional[int] = Query(default=None, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get top skills by demand"""
    service = SkillDemandService(db)
    
    try:
        skills = service.get_top_skills(
            limit=limit,
            category=category,
            job_category=job_category,
            days_back=days_back
        )
        
        return [SkillDemandResponse(**skill) for skill in skills]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/skill/{skill_id}/trend", response_model=List[SkillTrendResponse])
def get_skill_trend(
    skill_id: int,
    days_back: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get demand trend for a specific skill"""
    service = SkillDemandService(db)
    
    try:
        trend = service.get_skill_trend(skill_id, days_back)
        
        if not trend:
            raise HTTPException(status_code=404, detail="Skill not found or no trend data")
        
        return [SkillTrendResponse(**item) for item in trend]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending", response_model=List[TrendingSkillResponse])
def get_trending_skills(
    days_back: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Get skills that are trending upward"""
    service = SkillDemandService(db)
    
    try:
        trending = service.get_trending_skills(days_back)
        
        return [TrendingSkillResponse(**skill) for skill in trending]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/skill/{skill_id}/sources")
def get_skill_demand_by_source(
    skill_id: int,
    db: Session = Depends(get_db)
):
    """Get demand breakdown by source for a specific skill"""
    service = SkillDemandService(db)
    
    try:
        sources = service.get_skill_demand_by_source(skill_id)
        
        if not sources:
            raise HTTPException(status_code=404, detail="Skill not found or no data")
        
        return sources
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-insights", response_model=MarketInsightsResponse)
def get_market_insights(db: Session = Depends(get_db)):
    """Get overall market insights"""
    service = SkillDemandService(db)
    
    try:
        insights = service.get_market_insights()
        
        if not insights:
            raise HTTPException(status_code=500, detail="Unable to fetch market insights")
        
        return MarketInsightsResponse(**insights)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job-categories", response_model=List[JobCategoryResponse])
def get_all_job_categories(db: Session = Depends(get_db)):
    """Get all job categories with their job counts"""
    service = SkillDemandService(db)
    
    try:
        categories = service.get_all_job_categories()
        
        if not categories:
            return []
        
        return [JobCategoryResponse(**category) for category in categories]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alignment-timeline/{user_id}")
def get_skill_alignment_timeline(
    user_id: int,
    days_back: int = Query(365, description="Number of days to look back"),
    top_industries: int = Query(5, description="Number of top industries to include"),
    db: Session = Depends(get_db)
):
    """Get user's skill alignment timeline with industries over time"""
    try:
        alignment_service = SkillAlignmentService(db)
        
        # Get timeline data for top industries
        timeline_data = alignment_service.get_top_industries_timeline(
            user_id=user_id,
            top_n=top_industries,
            days_back=days_back
        )
        
        if not timeline_data:
            # If no historical data, calculate current alignment to start tracking
            current_alignment = alignment_service.calculate_current_alignment(user_id)
            if current_alignment:
                # Return current state as single data point
                from datetime import datetime
                current_date = datetime.utcnow().strftime('%Y-%m-%d')
                timeline_data = {}
                for industry, score in current_alignment.items():
                    # Score is already 0-1 from calculate_current_alignment, so multiply by 100
                    timeline_data[industry] = [{
                        'date': current_date,
                        'alignment_score': round(score * 100, 1),
                        'timestamp': datetime.utcnow().isoformat()
                    }]
        
        # Format response
        industry_names = list(timeline_data.keys())
        
        # Convert to timeline format
        timeline_points = []
        all_dates = set()
        
        # Collect all unique dates
        for industry_data in timeline_data.values():
            for point in industry_data:
                all_dates.add(point['date'])
        
        # Create timeline points
        for date in sorted(all_dates):
            industries_data = {}
            for industry, data_points in timeline_data.items():
                # Find data for this date
                date_data = next((p for p in data_points if p['date'] == date), None)
                if date_data:
                    industries_data[industry] = {
                        'alignment_score': date_data['alignment_score'],
                        'timestamp': date_data['timestamp']
                    }
            
            if industries_data:  # Only add if we have data for this date
                timeline_points.append({
                    'date': date,
                    'industries': industries_data
                })
        
        return {
            'user_id': user_id,
            'timeline_data': timeline_points,
            'top_industries': industry_names,
            'date_range': {
                'start_date': min(all_dates) if all_dates else None,
                'end_date': max(all_dates) if all_dates else None,
                'days_back': days_back
            },
            'message': f"Found {len(timeline_points)} data points for {len(industry_names)} industries"
        }
        
    except Exception as e:
        logger.error(f"Error getting alignment timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alignment-timeline/{user_id}/recalculate")
def recalculate_user_alignment(user_id: int, db: Session = Depends(get_db)):
    """Manually trigger recalculation of user's current industry alignment"""
    try:
        alignment_service = SkillAlignmentService(db)
        current_alignment = alignment_service.calculate_current_alignment(user_id)
        
        if not current_alignment:
            raise HTTPException(status_code=404, detail="No skills found for user")
        
        # Get current skills to count total
        current_skills = alignment_service._get_current_user_skills(user_id)
        total_skills = len(current_skills)
        
        # Create a new alignment snapshot with the updated scores
        alignment_service._create_alignment_snapshot(user_id, current_alignment, total_skills)
        
        # Commit the snapshot to database
        db.commit()
        
        # Format alignment scores as percentages
        formatted_alignment = {
            industry: round(score * 100, 1) 
            for industry, score in current_alignment.items()
        }
        
        return {
            'user_id': user_id,
            'current_alignment': formatted_alignment,
            'calculated_at': datetime.utcnow().isoformat(),
            'message': f"Calculated alignment for {len(current_alignment)} industries and saved to timeline"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recalculating alignment: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh-views")
def refresh_materialized_views(db: Session = Depends(get_db)):
    """Refresh materialized views (admin endpoint)"""
    service = SkillDemandService(db)
    
    try:
        results = service.refresh_materialized_views()
        
        return {
            "success": all(results.values()),
            "results": results,
            "message": "Materialized views refreshed"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))