from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobBase(BaseModel):
    title: str
    company: str
    location: str | None = None
    description: str
    requirements: str | None = None


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: str | None = None
    company: str | None = None
    location: str | None = None
    description: str | None = None
    requirements: str | None = None
    skills_required: list[str] | None = None
    experience_required: int | None = None
    education_required: list[dict[str, Any]] | None = None
    is_active: bool | None = None


class Job(JobBase):
    id: int
    skills_required: list[str] | None = None
    experience_required: int | None = None
    education_required: list[dict[str, Any]] | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
