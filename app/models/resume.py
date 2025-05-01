from sqlalchemy import ARRAY, JSON, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.config import settings
from app.db.postgres_client import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    phone = Column(String)
    location = Column(String)

    resumes = relationship("Resume", back_populates="candidate")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    mongo_id = Column(String)
    filename = Column(String)
    skills = Column(ARRAY(String))
    experience = Column(JSON)
    education = Column(JSONB)

    candidate = relationship("Candidate", back_populates="resumes")
