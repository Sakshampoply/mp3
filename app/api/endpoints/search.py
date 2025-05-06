# app/api/endpoints/search.py
import logging
from typing import List
import traceback

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql import func

from app.api.endpoints.auth import UserRole, get_current_user, require_role
from app.db.postgres_client import get_db
from app.models.job import Job
from app.models.user import User
from app.models.resume import Resume
from app.models.resume import Candidate
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
        # Get job details - single query
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(404, "Job not found")

        # Create search query
        query_parts = [
            job.description or "",
            job.requirements or "",
            *job.skills_required,
        ]
        query_text = " ".join(query_parts).strip()

        if not query_text:
            raise HTTPException(400, "Job has no searchable content")

        # Get vector results
        vector_results = candidate_service.vector_search(query_text, limit * 2)
        if not vector_results:
            return []

        # Single optimized query for all candidates with their resumes
        candidate_ids = [res["metadata"]["candidate_id"] for res in vector_results]
        resume_ids = [res["resume_id"] for res in vector_results]

        candidates = (
            db.query(Candidate)
            .options(joinedload(Candidate.resumes))
            .filter(Candidate.id.in_(candidate_ids))
            .all()
        )

        # Create lookup dictionaries in single passes
        candidate_map = {c.id: c for c in candidates}
        resume_map = {r.id: r for c in candidates for r in c.resumes}

        # Build ranked results in one pass
        ranked = []
        for res in vector_results:
            candidate = candidate_map.get(res["metadata"]["candidate_id"])
            if not candidate:
                continue

            matching_resume = resume_map.get(int(res["resume_id"]))
            if not matching_resume:
                continue

            # Convert resume data
            resume_dict = ResumeResponse.model_validate(matching_resume).model_dump()
            resume_dict["education"] = [
                e if isinstance(e, dict) else {"degree": e}
                for e in resume_dict.get("education", [])
            ]

            ranked.append(
                {
                    "score": res["score"],
                    "candidate": CandidateResponse.model_validate(
                        candidate
                    ).model_dump(),
                    "matching_resume": resume_dict,
                }
            )

        # Sort and limit results
        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked[:limit]

    except Exception as e:
        logger.error(f"Ranking error: {str(e)}", exc_info=True)
        raise HTTPException(500, "Ranking failed")


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
