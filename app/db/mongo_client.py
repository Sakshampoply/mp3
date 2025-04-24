from pymongo import MongoClient
from app.core.config import settings
import certifi

client = MongoClient(
    settings.MONGO_URI,
    tls=True,
    tlsAllowInvalidCertificates=True,
    tlsCAFile=certifi.where(),
)

db = client[settings.MONGO_DB_NAME]


def get_resume_collection():
    return db[settings.MONGO_RESUME_COLLECTION]
