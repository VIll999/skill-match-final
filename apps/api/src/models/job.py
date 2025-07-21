from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base


class JobPosting(Base):
    __tablename__ = "job_postings"
    __table_args__ = (UniqueConstraint('source', 'external_id', name='uq_source_external_id'),)

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), index=True)
    source = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255))
    location = Column(String(255))
    description = Column(Text)
    requirements = Column(Text)
    salary_min = Column(Float)
    salary_max = Column(Float)
    job_type = Column(String(50))
    experience_level = Column(String(50))
    category = Column(String(100), index=True)  # Job category/industry
    posted_date = Column(DateTime(timezone=True))
    scraped_date = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Integer, default=1)
    raw_data = Column(JSON)
    
    skills = relationship("JobSkill", back_populates="job")
    matches = relationship("JobMatch", back_populates="job")