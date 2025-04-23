from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class JobBase(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    description: str
    requirements: Optional[str] = None


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    skills_required: Optional[List[str]] = None
    experience_required: Optional[int] = None
    education_required: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None


class Job(JobBase):
    id: int
    skills_required: Optional[List[str]] = None
    experience_required: Optional[int] = None
    education_required: Optional[List[Dict[str, Any]]] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True