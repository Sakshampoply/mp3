from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from app.services.llm_parser import LLMParser
from app.models.resume import Candidate, Resume
from app.db.postgres_client import get_db
from sqlalchemy.orm import Session
from app.db.mongo_client import get_resume_collection
from fastapi import APIRouter, UploadFile, File, Depends
from app.services.llm_parser import LLMParser
from app.db.chroma_client import chroma_client
from app.models.resume import Resume, Candidate
from app.db.postgres_client import get_db
import os
from app.services.pdf_parser import ResumeParser
from bson import ObjectId
from typing import List
from app.schemas.resume import CandidateResponse
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func, or_
import logging

logger = logging.getLogger(__name__)

resume_parser = ResumeParser()
router = APIRouter()
llm_parser = LLMParser()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Read file contents and validate
        contents = await file.read()
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in (".pdf", ".docx"):
            raise HTTPException(400, "Unsupported file type")

        # Store raw data in MongoDB first
        mongo_collection = get_resume_collection()
        mongo_doc = {
            "filename": file.filename,
            "raw_data": contents,
            "processed": False,
        }
        mongo_id = str(mongo_collection.insert_one(mongo_doc).inserted_id)

        try:
            # Extract text
            raw_text = resume_parser.extract_text_from_bytes(contents, ext)
            parsed_data = llm_parser.extract_entities(raw_text)

            if "error" in parsed_data:
                raise HTTPException(400, detail=parsed_data)

            # Check for existing candidate
            existing_candidate = (
                db.query(Candidate)
                .filter(Candidate.email == parsed_data["email"])
                .first()
            )

            if existing_candidate:
                candidate = existing_candidate
                action = "updated"

            if "skills" in parsed_data:
                parsed_data["skills"] = [
                    s.strip().lower() for s in parsed_data["skills"]
                ]

            else:
                # Create new candidate
                candidate = Candidate(
                    name=parsed_data["name"],
                    email=parsed_data["email"],
                    phone=parsed_data.get("phone"),
                    location=parsed_data.get("location"),
                )
                db.add(candidate)
                db.commit()
                action = "created"

            db.refresh(candidate)

            # Create resume record
            resume = Resume(
                candidate_id=candidate.id,
                mongo_id=mongo_id,
                filename=file.filename,
                skills=parsed_data.get("skills", []),
                experience=parsed_data.get("experience_years", 0),
                education=parsed_data.get("education", []),
            )
            db.add(resume)
            db.commit()
            db.refresh(resume)
            try:
                collection = chroma_client.get_collection()
                collection.add(
                    documents=[raw_text],
                    metadatas=[{"resume_id": resume.id, "candidate_id": candidate.id}],
                    ids=[str(resume.id)],
                )
            except Exception as e:
                logger.error(f"ChromaDB Error: {str(e)}")
                # Remove the MongoDB record if Chroma fails
                mongo_collection.delete_one({"_id": ObjectId(mongo_id)})
                raise HTTPException(500, "Failed to index resume")

            # Update MongoDB processed status
            mongo_collection.update_one(
                {"_id": ObjectId(mongo_id)}, {"$set": {"processed": True}}
            )

            return {
                "message": f"Resume processed successfully (candidate {action})",
                "resume_id": resume.id,
                "candidate_id": candidate.id,
            }

        except Exception as e:
            # Update MongoDB with error details
            mongo_collection.update_one(
                {"_id": ObjectId(mongo_id)},
                {
                    "$set": {
                        "processed": False,
                        "error": str(e),
                        "parsed_data": (
                            parsed_data if "parsed_data" in locals() else None
                        ),
                    }
                },
            )
            raise

    except HTTPException as he:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/candidates", response_model=List[CandidateResponse])
def filter_candidates_by_skill(
    skills: str = Query(
        ..., description="Comma-separated skills (supports partial matches)"
    ),
    db: Session = Depends(get_db),
):
    try:
        skill_list = [s.strip().lower() for s in skills.split(",") if s.strip()]
        if not skill_list:
            raise HTTPException(400, "At least one skill required")

        # Combined exact and fuzzy search
        candidates = (
            db.query(Candidate)
            .join(Resume)
            .filter(
                or_(
                    Resume.skills.op("&&")(skill_list),  # Exact array match
                    func.similarity(
                        func.array_to_string(Resume.skills, " "), " ".join(skill_list)
                    )
                    > 0.3,  # Fuzzy match threshold
                )
            )
            .options(joinedload(Candidate.resumes))
            .order_by(
                func.array_length(Resume.skills, 1).desc(),
                func.similarity(
                    func.array_to_string(Resume.skills, " "), " ".join(skill_list)
                ).desc(),
            )
            .distinct()
            .all()
        )

        return candidates or []

    except Exception as e:
        logger.error(f"Skill search error: {str(e)}")
        raise HTTPException(500, "Search failed")
