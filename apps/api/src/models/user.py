from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base


class User(Base):
    """User model for resume processing and job matching"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255))
    hashed_password = Column(String(255))
    phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    transcripts = relationship("Transcript", back_populates="user")
    skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    job_matches = relationship("JobMatch", back_populates="user", cascade="all, delete-orphan")
    
    # Skill history and alignment tracking
    skill_history = relationship("UserSkillHistory", back_populates="user", cascade="all, delete-orphan")
    industry_alignments = relationship("UserIndustryAlignment", back_populates="user", cascade="all, delete-orphan")
    alignment_snapshots = relationship("SkillAlignmentSnapshot", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.full_name}')>"


class UserSkill(Base):
    """User skills extracted from resumes or manually added"""
    __tablename__ = "user_skills"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    skill_id = Column(Integer, ForeignKey('skills.id', ondelete='CASCADE'), nullable=False)
    
    # Skill proficiency and metadata
    proficiency_level = Column(Float, nullable=False, default=0.5)  # 0.0 to 1.0
    years_experience = Column(Float, nullable=True)
    confidence = Column(Float, nullable=False, default=1.0)  # Extraction confidence
    
    # Source information
    source = Column(String(50), nullable=False)  # 'resume', 'manual', 'linkedin'
    resume_id = Column(Integer, ForeignKey('resumes.id', ondelete='SET NULL'), nullable=True)
    extraction_method = Column(String(50), nullable=True)  # 'skillner', 'sbert', 'regex'
    context = Column(Text, nullable=True)  # Text context where skill was found
    
    # Validation
    is_verified = Column(Boolean, default=False, nullable=False)  # User confirmed this skill
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="skills")
    skill = relationship("Skill")
    resume = relationship("Resume")
    
    def __repr__(self):
        return f"<UserSkill(user_id={self.user_id}, skill_id={self.skill_id})>"


# JobMatch is now defined in models/job_match.py to avoid duplication


class SkillGap(Base):
    """Detailed skill gap analysis for specific job matches"""
    __tablename__ = "skill_gaps"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('job_matches.id', ondelete='CASCADE'), nullable=False)
    skill_id = Column(Integer, ForeignKey('skills.id', ondelete='CASCADE'), nullable=False)
    
    # Gap details
    gap_type = Column(String(50), nullable=False)  # 'missing', 'low_proficiency', 'outdated'
    importance = Column(Float, nullable=False)  # How important this skill is for the job
    user_proficiency = Column(Float, nullable=True)  # User's current proficiency (if any)
    required_proficiency = Column(Float, nullable=False)  # Required proficiency for job
    
    # Recommendations
    priority = Column(String(20), nullable=False)  # 'high', 'medium', 'low'
    learning_resources = Column(JSON, nullable=True)  # Suggested courses, tutorials
    estimated_learning_time = Column(Integer, nullable=True)  # Hours to learn
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    match = relationship("JobMatch")
    skill = relationship("Skill")
    
    def __repr__(self):
        return f"<SkillGap(match_id={self.match_id}, skill_id={self.skill_id})>"