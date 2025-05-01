import os
import uvicorn
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.api.endpoints import resumes, jobs, search, auth
from app.core.config import settings
from app.db.postgres_client import engine, Base, get_db
from app.models import resume, job
from app.db.postgres_client import Base, engine
from app.services.firebase_auth import initialize_firebase
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    initialize_firebase()  # Explicit initialization


def create_tables():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables()


# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(
    auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"]
)

app.include_router(
    resumes.router, prefix=f"{settings.API_V1_STR}/resumes", tags=["resumes"]
)

app.include_router(jobs.router, prefix=f"{settings.API_V1_STR}/jobs", tags=["jobs"])

app.include_router(
    search.router, prefix=f"{settings.API_V1_STR}/search", tags=["search"]
)

# Create uploads directory if it doesn't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Resume Screener API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check database connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {"status": "ok", "database": db_status, "version": "0.1.0"}


if __name__ == "__main__":

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
