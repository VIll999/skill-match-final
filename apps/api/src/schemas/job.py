from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class JobPostingBase(BaseModel):
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None


class JobPostingCreate(JobPostingBase):
    external_id: str
    source: str


class JobPostingUpdate(JobPostingBase):
    title: Optional[str] = None
    is_active: Optional[bool] = None


class JobPosting(JobPostingBase):
    id: int
    external_id: str
    source: str
    posted_date: Optional[datetime] = None
    scraped_date: datetime
    is_active: bool

    class Config:
        from_attributes = True