from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class CandidateBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None


class CandidateCreate(CandidateBase):
    pass


class CandidateUpdate(CandidateBase):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class Candidate(CandidateBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResumeBase(BaseModel):
    candidate_id: int
    filename: str


class ResumeCreate(ResumeBase):
    pass


class ResumeUpdate(BaseModel):
    skills: Optional[List[str]] = None
    experience_years: Optional[float] = None
    education: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None


class Resume(ResumeBase):
    id: int
    mongo_id: str
    skills: Optional[List[str]] = None
    experience_years: Optional[float] = None
    education: Optional[List[Dict[str, Any]]] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResumeWithCandidate(Resume):
    candidate: Candidate

    class Config:
        from_attributes = True


class CandidateWithResumes(Candidate):
    resumes: List[Resume]

    class Config:
        from_attributes = True


class EducationEntry(BaseModel):
    degree: str
    institute: str
    field: Optional[str] = None
    duration: Optional[str] = None


class ResumeResponse(BaseModel):
    id: int
    skills: list[str]
    experience: int
    education: List[EducationEntry]
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
