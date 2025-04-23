from pymongo import MongoClient
from pymongo.collection import Collection

from app.core.config import settings

# Create MongoDB client
client = MongoClient(settings.MONGO_CONNECTION_STRING)
db = client[settings.MONGO_DB_NAME]


def get_resume_collection() -> Collection:
    """Get the resume collection"""
    return db[settings.MONGO_RESUME_COLLECTION]