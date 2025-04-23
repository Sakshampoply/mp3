import os
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.api.endpoints import resumes, jobs
from app.core.config import settings
from app.db.postgres_client import engine, Base, get_db
from app.models import resume, job  # Import models to be created

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(
    resumes.router,
    prefix=f"{settings.API_V1_STR}/resumes",
    tags=["resumes"]
)

app.include_router(
    jobs.router,
    prefix=f"{settings.API_V1_STR}/jobs",
    tags=["jobs"]
)

# Create uploads directory if it doesn't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Resume Screener API",
        "version": "0.1.0",
        "docs": "/docs"
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
    
    return {
        "status": "ok",
        "database": db_status,
        "version": "0.1.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)