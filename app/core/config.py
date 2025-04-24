from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    PROJECT_NAME: str = "Resume Parser"
    API_V1_STR: str = "/api/v1"

    # MongoDB Configuration
    MONGO_URI: str
    MONGO_DB_NAME: str
    MONGO_RESUME_COLLECTION: str
    # PostgreSQL (for metadata only)
    POSTGRES_URL: str = "postgresql://postgres:11008712@localhost:5433/resumes"

    OLLAMA_HOST: str = "http://localhost:11434"
    EXTRACTION_MODEL: str = "llama3"
    EMBEDDING_MODEL: str = "nomic-embed-text"

    # ChromaDB
    CHROMA_PERSIST_PATH: str = "./chroma_db"
    CHROMA_COLLECTION: str = "resumes"

    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 5242880  # 5MB

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
