from sqlalchemy import Column, Integer, String, DateTime, Text, Float, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    skill_type = Column(String(20), nullable=False)
    emsi_id = Column(String(50), nullable=True, index=True)
    description = Column(Text, nullable=True)
    times_mentioned = Column(Integer, default=0, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Add constraint to ensure skill_type is only 'SOFT' or 'TECHNICAL'
    __table_args__ = (
        CheckConstraint("skill_type IN ('SOFT', 'TECHNICAL')", name='check_skill_type'),
    )
    
    job_skills = relationship("JobSkill", back_populates="skill")


class JobSkill(Base):
    __tablename__ = "job_skills"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    importance = Column(Float, default=1.0)
    is_required = Column(Integer, default=1)
    
    job = relationship("JobPosting", back_populates="skills")
    skill = relationship("Skill", back_populates="job_skills")


# UserSkill is now defined in models/user.py to avoid duplication