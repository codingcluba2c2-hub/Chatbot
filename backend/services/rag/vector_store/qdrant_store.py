from typing import List, Dict, Any
from .base import VectorStoreProvider
from core.logger import get_logger
from core.config import QDRANT_URL, QDRANT_API_KEY, VECTOR_COLLECTION

logger = get_logger(__name__)

class QdrantProvider(VectorStoreProvider):
    def __init__(self, collection_name: str = None):
        self.collection_name = collection_name or VECTOR_COLLECTION
        self.client = None
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
            
            if QDRANT_URL and not QDRANT_URL.startswith("http://localhost:6333") and QDRANT_URL != ":memory:":
                # Production/Cloud Qdrant
                self.client = QdrantClient(
                    url=QDRANT_URL,
                    api_key=QDRANT_API_KEY
                )
            else:
                # Local Persistent or Memory Qdrant fallback
                path = ":memory:" if QDRANT_URL == ":memory:" else None
                self.client = QdrantClient(path if path else QDRANT_URL)
                
            # Create collection if not exists
            if not self.client.collection_exists(self.collection_name):
                logger.info(f"Collection {self.collection_name} does not exist. Creating it now...")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
                )
            logger.info("Qdrant client initialized.")
        except ImportError:
            logger.error("qdrant-client not installed.")
            
    def upsert(self, ids: List[str], embeddings: List[List[float]], payloads: List[Dict[str, Any]]):
        if not self.client: return
        from qdrant_client.http import models
        points = [
            models.PointStruct(id=uid, vector=emb, payload=payload) 
            for uid, emb, payload in zip(ids, embeddings, payloads)
        ]
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logger.info(f"Upserted {len(points)} points into Qdrant.")

    def search(self, query_embedding: List[float], top_k: int = 5, filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        if not self.client: return []
        from qdrant_client.http import models
        
        qdrant_filter = None
        if filter_dict:
            # Simple match filter builder
            must_conditions = []
            for k, v in filter_dict.items():
                must_conditions.append(models.FieldCondition(key=k, match=models.MatchValue(value=v)))
            qdrant_filter = models.Filter(must=must_conditions)
            
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            query_filter=qdrant_filter,
            limit=top_k
        )
        
        # Convert to standardized dict format
        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload
            }
            for hit in results.points
        ]
        
    def delete(self, ids: List[str]):
        if not self.client: return
        from qdrant_client.http import models
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(points=ids)
        )
