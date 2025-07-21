from fastapi import APIRouter
from .endpoints import jobs, skills
from ...routers import resume, matching, skill_demand, profile, scheduler

api_router = APIRouter()

api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
api_router.include_router(resume.router, tags=["resumes"])
api_router.include_router(matching.router, prefix="/match", tags=["matching"])
api_router.include_router(skill_demand.router, tags=["skill_demand"])
api_router.include_router(profile.router, tags=["profile"])
api_router.include_router(scheduler.router, tags=["scheduler"])