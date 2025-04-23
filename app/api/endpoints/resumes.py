from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
import os
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.postgres_client import get_db
from app.db.mongo_client import get_resume_collection
from app.models.resume import Resume, Candidate
from app.services.candidates import CandidateService
from app.services.pdf_parser import ResumeParser

router = APIRouter()
candidate_service = CandidateService()
resume_parser = ResumeParser()

@router.get("/by_skill/")
def filter_candidates_by_skill(
    skill: str = Query(..., description="Skill to filter by"),
    db: Session = Depends(get_db)
):
    """Filter candidates by a specific skill"""
    candidates = candidate_service.filter_candidates_by_skill(db, skill)
    return {"skill": skill, "count": len(candidates), "candidates": candidates}

@router.get("/rank_for_job/{job_id}")
def rank_candidates_for_job(
    job_id: int,
    limit: int = Query(10, description="Maximum number of candidates to return"),
    db: Session = Depends(get_db)
):
    """Rank candidates based on their match to a specific job"""
    job = db.query(Resume)  # Note: Adjust if needed
    job = db.query(Candidate).filter(Candidate.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    ranked_candidates = candidate_service.rank_candidates_for_job(db, job_id, limit)
    return {"job_id": job_id, "job_title": job.title, "count": len(ranked_candidates), "candidates": ranked_candidates}

@router.post("/upload_resume", status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload a resume file, store its raw text in MongoDB, and candidate + resume metadata in PostgreSQL."""
    # Read file contents and validate extension
    contents = await file.read()
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".pdf", ".docx"):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported file type")

    # Parse resume bytes
    result = resume_parser.parse_resume_from_bytes(contents, ext)
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to parse resume")
        )

    raw_text = result["raw_text"]
    metadata = result["metadata"]  # {'skills': [...], 'experience_years': X, 'education': [...]}

    # Store raw text + metadata in MongoDB
    resume_collection = get_resume_collection()
    mongo_doc = {
        "raw_text": raw_text,
        "filename": file.filename,
        "metadata": metadata,
    }
    insert_result = resume_collection.insert_one(mongo_doc)
    mongo_id = insert_result.inserted_id

    # Create Candidate record
    candidate = Candidate(name=name, email=email, phone=phone, location=location)
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    # Create Resume record with extracted metadata
    resume = Resume(
        candidate_id=candidate.id,
        mongo_id=str(mongo_id),
        filename=file.filename,
        skills=metadata.get("skills"),
        experience_years=metadata.get("experience_years"),
        education=metadata.get("education")
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return {
        "resume_id": resume.id,
        "candidate_id": candidate.id,
        "mongo_id": str(mongo_id),
        "filename": file.filename
    }