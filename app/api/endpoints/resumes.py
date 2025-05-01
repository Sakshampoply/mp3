import logging
import os
import traceback
from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql import func, or_

from app.api.endpoints.auth import UserRole, require_role
from app.celery_app import process_resume_task
from app.db.chroma_client import chroma_client
from app.db.mongo_client import get_resume_collection
from app.db.postgres_client import get_db
from app.models.resume import Candidate, Resume
from app.models.user import User
from app.schemas.resume import CandidateResponse
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


@router.get("/candidates", response_model=list[CandidateResponse])
def filter_candidates_by_skill(
    skills: str = Query(..., description="Comma-separated skills"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
):
    try:
        # 1. Normalize and validate input
        search_terms = [s for s in skills.split(",") if s.strip()]
        logger.debug(f"Normalized search terms: {search_terms}")

        if not search_terms:
            raise HTTPException(400, "At least one skill required")

        # 2. Build debug query
        base_query = db.query(Candidate).join(Resume)

        # 3. First: Try exact array matches
        exact_condition = Resume.skills.op("&&")(search_terms)
        exact_candidates = (
            base_query.filter(exact_condition)
            .options(joinedload(Candidate.resumes))
            .all()
        )
        logger.debug(f"Found {len(exact_candidates)} exact matches")

        # 4. Second: Try fuzzy matches if no exact results
        candidates = exact_candidates
        if not candidates:
            logger.debug("Attempting fuzzy search")
            fuzzy_condition = (
                func.similarity(
                    func.array_to_string(Resume.skills, "|"),  # Use | as separator
                    "|".join(search_terms),
                )
                > 0.1
            )  # Lower threshold

            candidates = (
                base_query.filter(fuzzy_condition)
                .options(joinedload(Candidate.resumes))
                .order_by(
                    func.similarity(
                        func.array_to_string(Resume.skills, "|"), "|".join(search_terms)
                    ).desc()
                )
                .limit(50)  # Safety limit
                .all()
            )
            logger.debug(f"Found {len(candidates)} fuzzy matches")

        # 5. Final verification
        logger.debug(f"Final candidate count: {len(candidates)}")
        for candidate in candidates:
            logger.debug(
                f"Candidate {candidate.id} skills: {candidate.resumes[0].skills}"
            )

        return candidates or []

    except Exception as e:
        logger.error(f"Search failed: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(500, "Search failed")
