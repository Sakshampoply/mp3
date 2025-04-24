# app/api/endpoints/search.py
from fastapi import APIRouter, Depends
from app.services.candidates import CandidateService
from app.db.postgres_client import get_db
from sqlalchemy.orm import Session

router = APIRouter()
candidate_service = CandidateService()


@router.get("/semantic-search")
async def semantic_search(query: str, limit: int = 10):
    return candidate_service.vector_search(query, limit)


@router.get("/hybrid-search")
async def hybrid_search(query: str, db: Session = Depends(get_db), limit: int = 10):
    vector_results = candidate_service.vector_search(query, limit * 2)
    keyword_results = (
        db.query(Resume)
        .filter(Resume.raw_text.ilike(f"%{query}%"))
        .limit(limit * 2)
        .all()
    )

    combined = {result.id: result for result in [*vector_results, *keyword_results]}
    return list(combined.values())[:limit]
