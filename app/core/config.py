import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Resume Screener API"
    API_V1_STR: str = "/api/v1"
    
    # PostgreSQL
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_DB: str
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: Optional[str] = None
    
    # MongoDB
    MONGO_CONNECTION_STRING: str
    MONGO_DB_NAME: str = "resume_screener"
    MONGO_RESUME_COLLECTION: str = "resumes"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    
    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **data):
        super().__init__(**data)
        # Create database URL for SQLAlchemy if not provided
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
        # Ensure upload directory exists
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)


settings = Settings()