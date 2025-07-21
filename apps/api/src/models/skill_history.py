"""
Skill History Models
Track user skill changes over time for alignment analysis
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base


class UserSkillHistory(Base):
    """Track all skill addition/removal/update events"""
    __tablename__ = "user_skill_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    emsi_skill_id = Column(String(50), nullable=False)  # EMSI skill identifier
    skill_name = Column(String(255), nullable=False)
    
    # Event details
    event_type = Column(String(20), nullable=False)  # 'added', 'removed', 'updated'
    proficiency_level = Column(Float, default=0.7)
    confidence = Column(Float, default=0.8)
    
    # Metadata
    source = Column(String(50), nullable=True)  # 'resume', 'manual', 'api'
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    extraction_method = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Previous values (for update events)
    previous_proficiency = Column(Float, nullable=True)
    previous_confidence = Column(Float, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="skill_history")
    resume = relationship("Resume", back_populates="skill_history_events")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_skill_history_user_time', 'user_id', 'created_at'),
        Index('idx_user_skill_history_skill', 'emsi_skill_id'),
        Index('idx_user_skill_history_event', 'event_type'),
    )


class UserIndustryAlignment(Base):
    """Calculated industry alignment scores over time"""
    __tablename__ = "user_industry_alignment"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Industry information
    industry_category = Column(String(100), nullable=False)  # e.g., "IT Jobs"
    
    # Alignment metrics
    alignment_score = Column(Float, nullable=False)  # 0.0 to 1.0
    total_industry_skills = Column(Integer, nullable=False)
    matched_skills = Column(Integer, nullable=False)
    skill_coverage = Column(Float, nullable=False)  # percentage
    
    # Skill breakdown
    matched_skill_ids = Column(Text, nullable=True)  # JSON array of matched EMSI skill IDs
    missing_skill_ids = Column(Text, nullable=True)  # JSON array of missing EMSI skill IDs
    
    # Calculation metadata
    calculation_method = Column(String(50), default='weighted_proficiency')
    skill_count_at_calculation = Column(Integer, nullable=False)
    
    # Timestamp
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="industry_alignments")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_industry_alignment_user_time', 'user_id', 'calculated_at'),
        Index('idx_user_industry_alignment_industry', 'industry_category'),
        Index('idx_user_industry_alignment_score', 'alignment_score'),
    )


class SkillAlignmentSnapshot(Base):
    """Periodic snapshots of user skill portfolio for trend analysis"""
    __tablename__ = "skill_alignment_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Snapshot metadata
    snapshot_date = Column(DateTime(timezone=True), server_default=func.now())
    trigger_event = Column(String(50), nullable=True)  # 'resume_upload', 'manual_update', 'scheduled'
    
    # Skill summary
    total_skills = Column(Integer, nullable=False)
    technical_skills = Column(Integer, nullable=False)
    soft_skills = Column(Integer, nullable=False)
    
    # Top alignments (JSON)
    top_industry_alignments = Column(Text, nullable=True)  # JSON with top 5 industry scores
    
    # Change indicators
    skills_added_since_last = Column(Integer, default=0)
    skills_removed_since_last = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="alignment_snapshots")
    
    # Indexes
    __table_args__ = (
        Index('idx_skill_alignment_snapshots_user_date', 'user_id', 'snapshot_date'),
    )