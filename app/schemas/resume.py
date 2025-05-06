from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CandidateBase(BaseModel):
    name: str
    email: str
    phone: str | None = None
    location: str | None = None


class CandidateCreate(CandidateBase):
    pass


class CandidateUpdate(CandidateBase):
    name: str | None = None
    email: EmailStr | None = None


class Candidate(CandidateBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ResumeBase(BaseModel):
    candidate_id: int
    filename: str


class ResumeCreate(ResumeBase):
    pass


class ResumeUpdate(BaseModel):
    skills: list[str] | None = None
    experience_years: float | None = None
    education: list[dict[str, Any]] | None = None
    is_active: bool | None = None


class Resume(ResumeBase):
    id: int
    mongo_id: str
    skills: list[str] | None = None
    experience_years: float | None = None
    education: list[dict[str, Any]] | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ResumeWithCandidate(Resume):
    candidate: Candidate

    class Config:
        from_attributes = True


class CandidateWithResumes(Candidate):
    resumes: list[Resume]

    class Config:
        from_attributes = True


class EducationEntry(BaseModel):
    degree: str
    institute: str
    field: str | None = None
    duration: str | None = None


class ResumeResponse(BaseModel):
    id: int
    skills: list[str]
    experience: float
    education: list[EducationEntry]
    filename: str

    model_config = ConfigDict(from_attributes=True)


class CandidateResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None
    location: str | None
    resumes: list[ResumeResponse] = []  # Or use a ResumeResponse schema

    model_config = ConfigDict(from_attributes=True)
