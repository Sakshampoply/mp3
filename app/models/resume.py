from sqlalchemy import Column, Integer, String, JSON, ARRAY
from app.db.postgres_client import Base
from app.core.config import settings


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    phone = Column(String)
    location = Column(String)


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer)
    mongo_id = Column(String)
    filename = Column(String)
    skills = Column(ARRAY(String))
    experience = Column(JSON)
    education = Column(JSON)
