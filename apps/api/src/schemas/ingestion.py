from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class JobDTO(BaseModel):
    """Common DTO for job data from any source"""
    external_id: str
    source: str
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    description: str
    requirements: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    category: Optional[str] = None
    posted_date: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None
    
    # Extracted skills will be processed separately
    extracted_skills: Optional[List[str]] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class GitHubJobDTO(BaseModel):
    """GitHub jobs specific format"""
    id: str
    type: str
    url: str
    created_at: str
    company: str
    company_url: Optional[str] = None
    location: str
    title: str
    description: str
    how_to_apply: Optional[str] = None
    company_logo: Optional[str] = None
    
    def to_job_dto(self) -> JobDTO:
        """Convert GitHub job to common JobDTO"""
        return JobDTO(
            external_id=f"github_{self.id}",
            source="github",
            title=self.title,
            company=self.company,
            location=self.location,
            description=self.description,
            requirements=self.how_to_apply,
            job_type=self.type,
            posted_date=datetime.fromisoformat(self.created_at.replace('Z', '+00:00')),
            raw_data=self.model_dump()
        )


class IndeedJobDTO(BaseModel):
    """Indeed jobs format from scraper"""
    job_key: str
    title: str
    company: str
    location: str
    summary: str
    posted_date: Optional[str] = None
    salary: Optional[str] = None
    job_type: Optional[str] = None
    
    def to_job_dto(self) -> JobDTO:
        """Convert Indeed job to common JobDTO"""
        # Parse salary if present
        salary_min = None
        salary_max = None
        if self.salary:
            # Simple salary parsing logic - can be enhanced
            import re
            numbers = re.findall(r'\d+(?:,\d+)*', self.salary.replace(',', ''))
            if len(numbers) >= 2:
                salary_min = float(numbers[0])
                salary_max = float(numbers[1])
            elif len(numbers) == 1:
                salary_min = salary_max = float(numbers[0])
        
        return JobDTO(
            external_id=f"indeed_{self.job_key}",
            source="indeed",
            title=self.title,
            company=self.company,
            location=self.location,
            description=self.summary,
            salary_min=salary_min,
            salary_max=salary_max,
            job_type=self.job_type,
            posted_date=datetime.now() if not self.posted_date else None,
            raw_data=self.model_dump()
        )