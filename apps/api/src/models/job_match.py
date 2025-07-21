from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base


class JobMatch(Base):
    __tablename__ = "job_matches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    
    # Legacy field for backward compatibility
    alignment_score = Column(Float, nullable=True)
    
    # New TF-IDF fields
    similarity_score = Column(Float, nullable=True)
    jaccard_score = Column(Float, nullable=True)
    cosine_score = Column(Float, nullable=True)
    weighted_score = Column(Float, nullable=True)
    skill_coverage = Column(Float, nullable=True)
    
    # Algorithm version tracking
    algorithm_version = Column(String(50), nullable=True, default="basic")
    
    # Skill data
    skill_match_details = Column(JSON)
    missing_skills = Column(JSON)
    matched_skills = Column(JSON)  # This should map to matching_skills
    matching_skills = Column(JSON)  # Add this for clarity
    
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    computed_at = Column(DateTime(timezone=True), nullable=True)
    
    user = relationship("User", back_populates="job_matches")
    job = relationship("JobPosting", back_populates="matches")