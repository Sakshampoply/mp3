# app/api/endpoints/search.py
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.endpoints.auth import UserRole, get_current_user, require_role
from app.db.postgres_client import get_db
from app.models.job import Job
from app.models.resume import Candidate
from app.models.user import User
from app.schemas.resume import CandidateResponse, ResumeResponse
from app.services.candidates import CandidateService

logger = logging.getLogger(__name__)


router = APIRouter()
candidate_service = CandidateService()


@router.get("/rank_candidates", response_model=list[dict])
async def rank_candidates(
    job_id: int,
    db: Session = Depends(get_db),
    limit: int = 10,
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
):
    try:
        # Get job details
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(404, "Job not found")

        # Create search query
        query_text = " ".join(
            [job.description or "", job.requirements or "", *job.skills_required]
        ).strip()

        if not query_text:
            raise HTTPException(400, "Job has no searchable content")

        # Get vector results
        vector_results = candidate_service.vector_search(query_text, limit * 2)
        if not vector_results:
            return []

        # Get candidate details
        candidate_ids = [res["metadata"]["candidate_id"] for res in vector_results]
        candidates = (
            db.query(Candidate)
            .options(joinedload(Candidate.resumes))
            .filter(Candidate.id.in_(candidate_ids))
            .all()
        )

        # Map candidates for quick lookup
        candidate_map = {c.id: c for c in candidates}

        # Build ranked results
        ranked = []
        for res in vector_results:
            candidate = (
                db.query(Candidate)
                .options(joinedload(Candidate.resumes))
                .get(res["metadata"]["candidate_id"])
            )

            if candidate:
                # Convert education entries to dicts
                resume_data = []
                for r in candidate.resumes:
                    resume_dict = ResumeResponse.model_validate(r).model_dump()
                    resume_dict["education"] = [
                        e if isinstance(e, dict) else {"degree": e}
                        for e in resume_dict.get("education", [])
                    ]
                    resume_data.append(resume_dict)

                ranked.append(
                    {
                        "score": res["score"],
                        "candidate": CandidateResponse.model_validate(
                            candidate
                        ).model_dump(),
                        "matching_resume": next(
                            (
                                r
                                for r in resume_data
                                if r["id"] == int(res["resume_id"])
                            ),
                            None,
                        ),
                    }
                )

        return sorted(
            [r for r in ranked if r["matching_resume"]],
            key=lambda x: x["score"],
            reverse=True,
        )[:limit]

    except Exception as e:
        logger.error(f"Ranking error: {str(e)}")
        raise HTTPException(500, "Ranking failed")
