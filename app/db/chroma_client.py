import chromadb
from app.core.config import settings


class ChromaClient:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_PATH)
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION, metadata={"hnsw:space": "cosine"}
        )

    def get_collection(self):
        return self.collection


chroma_client = ChromaClient()
