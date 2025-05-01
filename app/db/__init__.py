from .mongo_client import get_resume_collection
from .postgres_client import Base, SessionLocal, engine


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Add this for Celery compatibility
def get_db_session():
    return SessionLocal()
