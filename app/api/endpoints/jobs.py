from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.postgres_client import get_db
from app.models.job import Job
from app.schemas.job import JobCreate, Job as JobSchema, JobUpdate
from app.services.skill_extractor import (
    SkillExtractor,
)  # We'll reuse the skill extraction
from app.api.endpoints.auth import require_role, UserRole, get_current_user
from app.models.user import User

router = APIRouter()
skill_extractor = SkillExtractor()


@router.post("/", response_model=JobSchema, status_code=status.HTTP_201_CREATED)
def create_job(job: JobCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.RECRUITER))):
    """Create a new job posting"""
    # Extract skills from job description and requirements
    text_to_analyze = f"{job.description} {job.requirements or ''}"
    skills = skill_extractor.extract_skills(text_to_analyze)  # Use correct extractor

    # Create the job with extracted metadata
    db_job = Job(
        **job.model_dump(),
        skills_required=skills,
    )

    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


@router.get("/", response_model=List[JobSchema])
def get_jobs(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CANDIDATE))
):
    """Get a list of job postings"""
    query = db.query(Job)
    if active_only:
        query = query.filter(Job.is_active == True)

    jobs = query.offset(skip).limit(limit).all()
    return jobs


@router.get("/{job_id}", response_model=JobSchema)
def get_job(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.RECRUITER))):
    """Get a specific job by ID"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.put("/{job_id}", response_model=JobSchema)
def update_job(job_id: int, job_update: JobUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.RECRUITER))):
    """Update a job posting"""
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Update fields
    update_data = job_update.model_dump(exclude_unset=True)

    # If description or requirements are updated, re-extract skills
    if "description" in update_data or "requirements" in update_data:
        # Get the updated description and requirements
        description = update_data.get("description", db_job.description)
        requirements = update_data.get("requirements", db_job.requirements or "")

        # Extract skills from updated text
        text_to_analyze = f"{description} {requirements}"
        skills = skill_extractor.extract_skills(text_to_analyze)

        # Add skills to update data
        update_data["skills_required"] = skills

    # Apply updates
    for key, value in update_data.items():
        setattr(db_job, key, value)

    db.commit()
    db.refresh(db_job)
    return db_job


@router.delete("/{job_id}", response_model=JobSchema)
def delete_job(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.RECRUITER))):
    """Soft delete a job posting by setting is_active to False"""
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    db_job.is_active = False
    db.commit()
    db.refresh(db_job)
    return db_job
