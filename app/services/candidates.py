from app.db.chroma_client import chroma_client
from app.models.resume import Resume
from typing import List, Dict, Any


class CandidateService:
    def vector_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        collection = chroma_client.get_collection()
        results = collection.query(
            query_texts=[query], n_results=limit, include=["documents", "metadatas"]
        )
        return self._format_results(results)

    def _format_results(self, chroma_results) -> List[Dict[str, Any]]:
        formatted = []
        for ids, distances, metadatas, documents in zip(
            chroma_results["ids"],
            chroma_results["distances"],
            chroma_results["metadatas"],
            chroma_results["documents"],
        ):
            for i in range(len(ids)):
                formatted.append(
                    {
                        "resume_id": ids[i],
                        "score": 1 - distances[i],
                        "metadata": metadatas[i],
                        "content": documents[i],
                    }
                )
        return formatted
