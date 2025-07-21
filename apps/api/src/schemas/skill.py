from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SkillBase(BaseModel):
    name: str
    skill_type: str
    description: Optional[str] = None
    emsi_id: Optional[str] = None


class SkillCreate(SkillBase):
    pass


class Skill(SkillBase):
    id: int
    times_mentioned: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True