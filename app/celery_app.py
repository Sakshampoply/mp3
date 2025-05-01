# app/celery_app.py
import logging
import os
from tempfile import NamedTemporaryFile

from bson import ObjectId
from celery import Celery
from sqlalchemy.orm import Session

# Initialize Celery first to avoid circular imports
celery = Celery(
    __name__,
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)

# Set up logging
logger = logging.getLogger(__name__)

# Late imports to avoid circular dependencies
from app.db import get_db, get_resume_collection
from app.db.chroma_client import chroma_client
from app.models.resume import Candidate, Resume
from app.services.llm_parser import LLMParser
from app.services.pdf_parser import ResumeParser


@celery.task(name="process_resume_task", max_retries=3)
def process_resume_task(mongo_id: str):
    """Background task that replicates original parsing logic"""
    mongo_collection = get_resume_collection()
    db_gen = get_db()
    db: Session = next(db_gen)

    try:
        # Retrieve file from MongoDB
        doc = mongo_collection.find_one({"_id": ObjectId(mongo_id)})
        if not doc or not doc.get("raw_data"):
            raise ValueError("No resume data found in MongoDB")

        # Original text extraction logic
        resume_parser = ResumeParser()
        raw_text = resume_parser.extract_text_from_bytes(
            doc["raw_data"], os.path.splitext(doc["filename"])[1].lower()
        )

        # Original LLM parsing logic
        llm_parser = LLMParser()
        parsed_data = llm_parser.extract_entities(raw_text)
        if "error" in parsed_data:
            raise ValueError(parsed_data["error"])

        # Original candidate handling
        existing_candidate = (
            db.query(Candidate).filter(Candidate.email == parsed_data["email"]).first()
        )

        if existing_candidate:
            candidate = existing_candidate
            action = "updated"
        else:
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

        # Original resume creation
        resume = Resume(
            candidate_id=candidate.id,
            mongo_id=mongo_id,
            filename=doc["filename"],
            skills=parsed_data.get("skills", []),
            experience=parsed_data.get("experience_years", 0),
            education=parsed_data.get("education", []),
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        # Original ChromaDB indexing
        try:
            collection = chroma_client.get_collection()
            collection.add(
                documents=[raw_text],
                metadatas=[{"resume_id": resume.id, "candidate_id": candidate.id}],
                ids=[str(resume.id)],
            )
        except Exception as e:
            db.rollback()
            raise RuntimeError(f"ChromaDB error: {str(e)}")

        # Update MongoDB status
        mongo_collection.update_one(
            {"_id": ObjectId(mongo_id)}, {"$set": {"processed": True}}
        )

        return {"status": "success", "resume_id": str(resume.id), "action": action}

    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        mongo_collection.update_one(
            {"_id": ObjectId(mongo_id)},
            {
                "$set": {
                    "processed": False,
                    "error": str(e),
                    "parsed_data": parsed_data if "parsed_data" in locals() else None,
                }
            },
        )
        db.rollback()
        raise  # Celery will handle retries

    finally:
        try:
            next(db_gen)  # Close the database session
        except StopIteration:
            pass
