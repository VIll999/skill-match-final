from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ....db.database import get_db
from ....models.job import JobPosting
from ....schemas.job import JobPosting as JobPostingSchema, JobPostingCreate

router = APIRouter()


@router.get("/", response_model=List[JobPostingSchema])
def get_jobs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    jobs = db.query(JobPosting).offset(skip).limit(limit).all()
    return jobs


@router.get("/{job_id}", response_model=JobPostingSchema)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/", response_model=JobPostingSchema)
def create_job(job: JobPostingCreate, db: Session = Depends(get_db)):
    db_job = JobPosting(**job.model_dump())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job