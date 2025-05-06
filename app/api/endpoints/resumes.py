import logging
import os

from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from app.api.endpoints.auth import UserRole, require_role
from app.celery_app import process_resume_task
from app.db.mongo_client import get_resume_collection
from app.db.postgres_client import get_db
from app.models.resume import Resume
from app.models.user import User
from app.schemas.resume import ResumeResponse
from app.services.llm_parser import LLMParser
from app.services.pdf_parser import ResumeParser

logger = logging.getLogger(__name__)

resume_parser = ResumeParser()
router = APIRouter()
llm_parser = LLMParser()


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CANDIDATE)),
):
    try:
        # Validate file type first
        contents = await file.read()
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in (".pdf", ".docx"):
            raise HTTPException(400, "Unsupported file type")

        # Store raw data in MongoDB
        mongo_collection = get_resume_collection()
        mongo_doc = {
            "filename": file.filename,
            "raw_data": contents,
            "processed": False,
            "error": None,
        }
        mongo_id = str(mongo_collection.insert_one(mongo_doc).inserted_id)

        # Start background task
        process_resume_task.delay(mongo_id)
        return {"task_id": mongo_id, "status": "processing"}

    except HTTPException as he:
        raise
    except Exception as e:
        # Cleanup MongoDB entry if creation failed
        if "mongo_id" in locals():
            mongo_collection.delete_one({"_id": ObjectId(mongo_id)})
        raise HTTPException(500, detail=str(e))


@router.get("/upload/status/{mongo_id}")
async def check_upload_status(mongo_id: str):
    doc = get_resume_collection().find_one({"_id": ObjectId(mongo_id)})
    if not doc:
        raise HTTPException(404, "Resume not found")

    return {
        "processed": doc.get("processed", False),
        "error": doc.get("error"),
        "resume_id": doc.get("resume_id"),
        "candidate_id": doc.get("candidate_id"),
    }


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
):
    """
    Get parsed resume data by ID from PostgreSQL
    """
    try:
        # Get resume with candidate relationship
        resume = (
            db.query(Resume)
            .options(joinedload(Resume.candidate))  # Eager load candidate
            .filter(Resume.id == resume_id)
            .first()
        )

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found"
            )

        # Convert education entries to consistent format
        if resume.education:
            resume.education = [
                e if isinstance(e, dict) else {"degree": e} for e in resume.education
            ]

        return resume

    except Exception as e:
        logger.error(f"Error fetching resume: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving resume data",
        )
