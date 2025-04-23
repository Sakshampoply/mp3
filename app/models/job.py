from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func

from app.db.postgres_client import Base


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    company = Column(String(255), index=True)
    location = Column(String(255), nullable=True)
    description = Column(Text)
    requirements = Column(Text, nullable=True)
    
    # Extracted keywords for matching
    skills_required = Column(JSON, nullable=True)
    experience_required = Column(Integer, nullable=True)
    education_required = Column(JSON, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())