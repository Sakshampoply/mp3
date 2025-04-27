from app.db.chroma_client import chroma_client
from app.models.resume import Resume
from typing import List, Dict, Any


class CandidateService:
    def vector_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            collection = chroma_client.get_collection()
            results = collection.query(
                query_texts=[query],
                n_results=limit,
                include=["documents", "metadatas", "distances"],
            )
            return self._format_results(results) if results else []
        except Exception as e:
            print(f"Vector search error: {str(e)}")
            return []

    def _format_results(self, chroma_results) -> List[Dict[str, Any]]:
        formatted = []
        # IDs are always returned even when not explicitly included
        for ids, distances, metadatas, documents in zip(
            chroma_results["ids"],  # Now directly accessed
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
