"""
User Profile Management API
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..models.user import User, UserSkill
from ..models.skill import Skill
from sqlalchemy import text
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter(prefix="/profile", tags=["profile"])

# Configure logging
logger = logging.getLogger(__name__)


class UserSkillUpdate(BaseModel):
    """Model for updating user skills"""
    skill_id: int
    proficiency_level: float = Field(..., ge=0.0, le=1.0, description="Proficiency level (0.0 to 1.0)")
    years_experience: Optional[float] = Field(None, ge=0.0, description="Years of experience")
    is_verified: bool = Field(True, description="User has verified this skill")
    source: str = Field(default="manual", description="Source of skill addition")


class UserSkillAdd(BaseModel):
    """Model for adding new user skills"""
    skill_id: int
    proficiency_level: float = Field(..., ge=0.0, le=1.0, description="Proficiency level (0.0 to 1.0)")
    years_experience: Optional[float] = Field(None, ge=0.0, description="Years of experience")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in skill assessment")
    source: str = Field(default="manual", description="Source of skill addition")


class UserSkillResponse(BaseModel):
    """Response model for user skills"""
    id: int
    skill_id: int
    skill_name: str
    skill_type: str
    category_name: str
    proficiency_level: float
    years_experience: Optional[float]
    confidence: float
    source: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class EMSIUserSkillResponse(BaseModel):
    """Response model for EMSI user skills"""
    id: int
    emsi_skill_id: str
    skill_name: str
    skill_type: Optional[str] = None
    category_name: Optional[str] = None
    proficiency_level: float
    years_experience: Optional[float] = None
    confidence: float
    source: str
    extraction_method: str
    resume_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class ProfileUpdateRequest(BaseModel):
    """Request model for profile updates"""
    skills_to_add: List[UserSkillAdd] = []
    skills_to_update: List[UserSkillUpdate] = []
    skills_to_delete: List[int] = []


class ProfileUpdateResponse(BaseModel):
    """Response model for profile updates"""
    message: str
    added_skills: int
    updated_skills: int
    deleted_skills: int
    total_skills: int
    skills: List[UserSkillResponse]


@router.get("/skills/{user_id}", response_model=List[UserSkillResponse])
async def get_user_skills(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get all skills for a user"""
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get user skills with skill details
        user_skills = db.query(UserSkill).filter(
            UserSkill.user_id == user_id
        ).all()
        
        response = []
        for user_skill in user_skills:
            skill = db.query(Skill).filter(Skill.id == user_skill.skill_id).first()
            if skill:
                response.append(UserSkillResponse(
                    id=user_skill.id,
                    skill_id=user_skill.skill_id,
                    skill_name=skill.name,
                    skill_type=skill.skill_type,
                    category_name=skill.skill_type,  # Use skill_type as category in simplified schema
                    proficiency_level=user_skill.proficiency_level,
                    years_experience=user_skill.years_experience,
                    confidence=user_skill.confidence,
                    source=user_skill.source,
                    is_verified=user_skill.is_verified,
                    created_at=user_skill.created_at,
                    updated_at=user_skill.updated_at
                ))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user skills: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user skills"
        )


@router.get("/skills/emsi/{user_id}", response_model=List[EMSIUserSkillResponse])
async def get_user_emsi_skills(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get all EMSI skills for a user"""
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get EMSI user skills with skill type information
        query = text("""
            SELECT 
                ues.id,
                ues.emsi_skill_id,
                ues.skill_name,
                es.skill_type,
                es.skill_type as category_name,
                ues.proficiency_level,
                ues.years_experience,
                ues.confidence,
                ues.source,
                ues.extraction_method,
                ues.resume_id,
                ues.created_at,
                ues.updated_at
            FROM user_skills_emsi ues
            LEFT JOIN emsi_skills es ON ues.emsi_skill_id = es.skill_id
            WHERE ues.user_id = :user_id
            ORDER BY ues.confidence DESC, ues.skill_name ASC
        """)
        
        result = db.execute(query, {"user_id": user_id})
        rows = result.fetchall()
        
        response = []
        for row in rows:
            response.append(EMSIUserSkillResponse(
                id=row.id,
                emsi_skill_id=row.emsi_skill_id,
                skill_name=row.skill_name,
                skill_type=row.skill_type or "General",
                category_name=row.category_name or "General",
                proficiency_level=row.proficiency_level,
                years_experience=row.years_experience,
                confidence=row.confidence,
                source=row.source,
                extraction_method=row.extraction_method,
                resume_id=row.resume_id,
                created_at=row.created_at,
                updated_at=row.updated_at
            ))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user EMSI skills: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user EMSI skills"
        )


@router.patch("/skills/{user_id}", response_model=ProfileUpdateResponse)
async def update_user_skills(
    user_id: int,
    update_request: ProfileUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update user skills (add, update, delete)"""
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        added_count = 0
        updated_count = 0
        deleted_count = 0
        
        # Add new skills
        for skill_add in update_request.skills_to_add:
            # Check if skill exists
            skill = db.query(Skill).filter(Skill.id == skill_add.skill_id).first()
            if not skill:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Skill with ID {skill_add.skill_id} not found"
                )
            
            # Check if user already has this skill
            existing_skill = db.query(UserSkill).filter(
                UserSkill.user_id == user_id,
                UserSkill.skill_id == skill_add.skill_id
            ).first()
            
            if existing_skill:
                # Update existing skill instead of adding duplicate
                existing_skill.proficiency_level = skill_add.proficiency_level
                existing_skill.years_experience = skill_add.years_experience
                existing_skill.confidence = skill_add.confidence
                existing_skill.source = skill_add.source
                existing_skill.is_verified = True
                existing_skill.updated_at = datetime.utcnow()
                updated_count += 1
            else:
                # Add new skill
                new_skill = UserSkill(
                    user_id=user_id,
                    skill_id=skill_add.skill_id,
                    proficiency_level=skill_add.proficiency_level,
                    years_experience=skill_add.years_experience,
                    confidence=skill_add.confidence,
                    source=skill_add.source,
                    is_verified=True
                )
                db.add(new_skill)
                added_count += 1
        
        # Update existing skills
        for skill_update in update_request.skills_to_update:
            user_skill = db.query(UserSkill).filter(
                UserSkill.user_id == user_id,
                UserSkill.skill_id == skill_update.skill_id
            ).first()
            
            if not user_skill:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User skill with ID {skill_update.skill_id} not found"
                )
            
            # Update skill
            user_skill.proficiency_level = skill_update.proficiency_level
            user_skill.years_experience = skill_update.years_experience
            user_skill.is_verified = skill_update.is_verified
            user_skill.source = skill_update.source
            user_skill.updated_at = datetime.utcnow()
            updated_count += 1
        
        # Delete skills
        for skill_id in update_request.skills_to_delete:
            user_skill = db.query(UserSkill).filter(
                UserSkill.user_id == user_id,
                UserSkill.skill_id == skill_id
            ).first()
            
            if user_skill:
                db.delete(user_skill)
                deleted_count += 1
        
        # Commit changes
        db.commit()
        
        # Get updated skills list
        updated_skills = await get_user_skills(user_id, db)
        
        return ProfileUpdateResponse(
            message=f"Profile updated successfully. Added: {added_count}, Updated: {updated_count}, Deleted: {deleted_count}",
            added_skills=added_count,
            updated_skills=updated_count,
            deleted_skills=deleted_count,
            total_skills=len(updated_skills),
            skills=updated_skills
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user skills: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user skills"
        )


@router.post("/skills/{user_id}/verify", response_model=ProfileUpdateResponse)
async def verify_user_skill(
    user_id: int,
    skill_id: int,
    proficiency_level: Optional[float] = None,
    years_experience: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Verify and optionally update a user skill"""
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Find the skill
        user_skill = db.query(UserSkill).filter(
            UserSkill.user_id == user_id,
            UserSkill.skill_id == skill_id
        ).first()
        
        if not user_skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User skill not found"
            )
        
        # Update skill
        user_skill.is_verified = True
        if proficiency_level is not None:
            user_skill.proficiency_level = proficiency_level
        if years_experience is not None:
            user_skill.years_experience = years_experience
        user_skill.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Get updated skills list
        updated_skills = await get_user_skills(user_id, db)
        
        return ProfileUpdateResponse(
            message=f"Skill verified successfully",
            added_skills=0,
            updated_skills=1,
            deleted_skills=0,
            total_skills=len(updated_skills),
            skills=updated_skills
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying user skill: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify user skill"
        )


@router.delete("/skills/{user_id}/{skill_id}")
async def delete_user_skill(
    user_id: int,
    skill_id: int,
    db: Session = Depends(get_db)
):
    """Delete a specific user skill"""
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Find and delete the skill
        user_skill = db.query(UserSkill).filter(
            UserSkill.user_id == user_id,
            UserSkill.skill_id == skill_id
        ).first()
        
        if not user_skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User skill not found"
            )
        
        db.delete(user_skill)
        db.commit()
        
        return {"message": "Skill deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user skill: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user skill"
        )


@router.get("/summary/{user_id}")
async def get_user_profile_summary(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user profile summary with stats"""
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get skill counts by category and source
        skills_query = db.query(UserSkill).filter(UserSkill.user_id == user_id)
        
        total_skills = skills_query.count()
        verified_skills = skills_query.filter(UserSkill.is_verified == True).count()
        resume_skills = skills_query.filter(UserSkill.source == 'resume').count()
        manual_skills = skills_query.filter(UserSkill.source == 'manual').count()
        
        # Get skills by category
        skills_by_category = {}
        user_skills = skills_query.all()
        
        for user_skill in user_skills:
            skill = db.query(Skill).filter(Skill.id == user_skill.skill_id).first()
            if skill:
                category = skill.skill_type  # Use skill_type as category in simplified schema
                if category not in skills_by_category:
                    skills_by_category[category] = 0
                skills_by_category[category] += 1
        
        # Calculate average proficiency
        proficiencies = [skill.proficiency_level for skill in user_skills]
        avg_proficiency = sum(proficiencies) / len(proficiencies) if proficiencies else 0.0
        
        return {
            "user_id": user_id,
            "user_name": user.full_name,
            "user_email": user.email,
            "total_skills": total_skills,
            "verified_skills": verified_skills,
            "unverified_skills": total_skills - verified_skills,
            "resume_skills": resume_skills,
            "manual_skills": manual_skills,
            "skills_by_category": skills_by_category,
            "avg_proficiency": round(avg_proficiency, 3),
            "profile_completeness": round((verified_skills / total_skills * 100) if total_skills > 0 else 0, 1)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile summary"
        )


class EMSISkillUpdate(BaseModel):
    """Model for updating EMSI skills"""
    emsi_skill_id: str
    proficiency_level: float = Field(..., ge=0.0, le=1.0, description="Proficiency level (0.0 to 1.0)")
    years_experience: Optional[float] = Field(None, ge=0.0, description="Years of experience")


class EMSISkillsUpdateRequest(BaseModel):
    """Request model for updating EMSI skills"""
    skills_to_update: List[EMSISkillUpdate]


class EMSISkillsUpdateResponse(BaseModel):
    """Response model for EMSI skills update"""
    message: str
    updated_skills: int
    skills: List[EMSIUserSkillResponse]


@router.patch("/skills/emsi/{user_id}", response_model=EMSISkillsUpdateResponse)
async def update_user_emsi_skills(
    user_id: int,
    update_request: EMSISkillsUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update EMSI skills for a user"""
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        updated_count = 0
        
        # Update EMSI skills
        for skill_update in update_request.skills_to_update:
            # Update the skill using raw SQL since we don't have an ORM model for user_skills_emsi
            update_query = text("""
                UPDATE user_skills_emsi 
                SET proficiency_level = :proficiency_level,
                    years_experience = :years_experience,
                    updated_at = :updated_at
                WHERE user_id = :user_id 
                AND emsi_skill_id = :emsi_skill_id
            """)
            
            result = db.execute(update_query, {
                "user_id": user_id,
                "emsi_skill_id": skill_update.emsi_skill_id,
                "proficiency_level": skill_update.proficiency_level,
                "years_experience": skill_update.years_experience,
                "updated_at": datetime.utcnow()
            })
            
            if result.rowcount > 0:
                updated_count += 1
        
        # Commit changes
        db.commit()
        
        # Get updated skills list
        updated_skills = await get_user_emsi_skills(user_id, db)
        
        return EMSISkillsUpdateResponse(
            message=f"Updated {updated_count} EMSI skills successfully",
            updated_skills=updated_count,
            skills=updated_skills
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user EMSI skills: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user EMSI skills"
        )


@router.delete("/{user_id}/clear-all-skills")
async def clear_all_user_skills(user_id: int, db: Session = Depends(get_db)):
    """Clear all skill-related data for a user (for testing purposes)"""
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        deleted_counts = {}
        
        # Delete in order to respect foreign key constraints
        # First: Clear skill history events (references user_skills and resumes)
        history_result = db.execute(text("DELETE FROM user_skill_history WHERE user_id = :user_id"), {"user_id": user_id})
        deleted_counts["skill_history"] = history_result.rowcount
        
        # Clear user skills (references resumes)
        user_skills_result = db.execute(text("DELETE FROM user_skills WHERE user_id = :user_id"), {"user_id": user_id})
        deleted_counts["user_skills"] = user_skills_result.rowcount
        
        # Clear EMSI skills
        emsi_result = db.execute(text("DELETE FROM user_skills_emsi WHERE user_id = :user_id"), {"user_id": user_id})
        deleted_counts["emsi_skills"] = emsi_result.rowcount
        
        # Clear skill alignment history
        alignment_result = db.execute(text("DELETE FROM user_industry_alignment WHERE user_id = :user_id"), {"user_id": user_id})
        deleted_counts["alignment_records"] = alignment_result.rowcount
        
        # Clear skill alignment snapshots
        snapshots_result = db.execute(text("DELETE FROM skill_alignment_snapshots WHERE user_id = :user_id"), {"user_id": user_id})
        deleted_counts["snapshots"] = snapshots_result.rowcount
        
        # Clear resumes (after clearing dependent records)
        resumes_result = db.execute(text("DELETE FROM resumes WHERE user_id = :user_id"), {"user_id": user_id})
        deleted_counts["resumes"] = resumes_result.rowcount
        
        # Clear job matches
        job_matches_result = db.execute(text("DELETE FROM job_matches WHERE user_id = :user_id"), {"user_id": user_id})
        deleted_counts["job_matches"] = job_matches_result.rowcount
        
        # Reset user profile to default values
        user_update_result = db.execute(text("""
            UPDATE users 
            SET full_name = :default_name, 
                email = :default_email 
            WHERE id = :user_id
        """), {"user_id": user_id, "default_name": "Handsome User", "default_email": "handsome@user.com"})
        deleted_counts["user_profile_reset"] = user_update_result.rowcount > 0
        
        # Commit all deletions
        db.commit()
        
        logger.info(f"Cleared all skill data for user {user_id}: {deleted_counts}")
        
        return {
            "message": f"Successfully cleared all skill data for user {user_id}",
            "deleted_counts": deleted_counts,
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing user skill data: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear user skill data: {str(e)}"
        )