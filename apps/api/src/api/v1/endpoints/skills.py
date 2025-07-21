from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional

from ....db.database import get_db
from ....models.skill import Skill
from ....schemas.skill import (
    Skill as SkillSchema,
    SkillCreate
)

router = APIRouter()


@router.get("/", response_model=List[SkillSchema])
def get_skills(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    skill_type: Optional[str] = Query(None, description="Filter by skill type: 'Soft Skill' or 'Technical'"),
    search: Optional[str] = Query(None, description="Search skills by name"),
    order_by: str = Query("times_mentioned", description="Order by: 'name', 'times_mentioned', 'created_at'"),
    db: Session = Depends(get_db)
):
    """Get skills with filtering and search capabilities"""
    query = db.query(Skill)
    
    # Filter by skill type
    if skill_type:
        if skill_type not in ['Soft Skill', 'Technical']:
            raise HTTPException(status_code=400, detail="skill_type must be 'Soft Skill' or 'Technical'")
        query = query.filter(Skill.skill_type == skill_type)
    
    # Search by name
    if search:
        query = query.filter(Skill.name.ilike(f"%{search}%"))
    
    # Only show skills that are mentioned in jobs
    query = query.filter(Skill.times_mentioned > 0)
    
    # Order results
    if order_by == "name":
        query = query.order_by(Skill.name)
    elif order_by == "created_at":
        query = query.order_by(desc(Skill.created_at))
    else:  # default to times_mentioned
        query = query.order_by(desc(Skill.times_mentioned))
    
    return query.offset(skip).limit(limit).all()


@router.get("/stats")
def get_skill_stats(db: Session = Depends(get_db)):
    """Get statistics about the skill system"""
    total_skills = db.query(Skill).filter(Skill.times_mentioned > 0).count()
    technical_skills = db.query(Skill).filter(
        Skill.skill_type == 'Technical',
        Skill.times_mentioned > 0
    ).count()
    soft_skills = db.query(Skill).filter(
        Skill.skill_type == 'Soft Skill',
        Skill.times_mentioned > 0
    ).count()
    
    # Top 10 most mentioned skills
    top_skills = db.query(Skill).filter(
        Skill.times_mentioned > 0
    ).order_by(desc(Skill.times_mentioned)).limit(10).all()
    
    return {
        "total_skills": total_skills,
        "technical_skills": technical_skills,
        "soft_skills": soft_skills,
        "skill_types": ["Soft Skill", "Technical"],
        "top_skills": [
            {
                "name": skill.name,
                "skill_type": skill.skill_type,
                "times_mentioned": skill.times_mentioned
            } for skill in top_skills
        ]
    }


@router.get("/{skill_id}", response_model=SkillSchema)
def get_skill(skill_id: int, db: Session = Depends(get_db)):
    """Get a specific skill by ID"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.post("/", response_model=SkillSchema)
def create_skill(
    skill: SkillCreate,
    db: Session = Depends(get_db)
):
    """Create a new skill"""
    # Validate skill_type
    if skill.skill_type not in ['Soft Skill', 'Technical']:
        raise HTTPException(
            status_code=400, 
            detail="skill_type must be 'Soft Skill' or 'Technical'"
        )
    
    # Check if skill already exists
    existing_skill = db.query(Skill).filter(Skill.name == skill.name).first()
    if existing_skill:
        raise HTTPException(status_code=400, detail="Skill already exists")
    
    db_skill = Skill(**skill.model_dump())
    db.add(db_skill)
    db.commit()
    db.refresh(db_skill)
    return db_skill


@router.get("/types/")
def get_skill_types():
    """Get available skill types"""
    return {
        "skill_types": [
            {
                "value": "Technical",
                "label": "Technical Skills",
                "description": "Programming languages, tools, frameworks, technical abilities"
            },
            {
                "value": "Soft Skill", 
                "label": "Soft Skills",
                "description": "Communication, leadership, teamwork, interpersonal abilities"
            }
        ]
    }