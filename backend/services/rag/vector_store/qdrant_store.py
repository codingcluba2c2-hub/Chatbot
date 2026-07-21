from typing import List, Dict, Any
from .base import VectorStoreProvider
from core.logger import get_logger
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, PointIdsList

logger = get_logger(__name__)

class QdrantProvider(VectorStoreProvider):
    def __init__(self, collection_name: str, url: str, api_key: str):
        self.collection_name = collection_name
        
        try:
            self.client = QdrantClient(url=url, api_key=api_key)
            logger.info(f"Connected to Qdrant Cloud at {url}")
            
            # Check if collection exists
            collections = self.client.get_collections()
            if not any(c.name == self.collection_name for c in collections.collections):
                logger.info(f"Collection {self.collection_name} not found. Creating it.")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                )
        except Exception as e:
            logger.error(f"Failed to initialize QdrantProvider: {str(e)}")
            raise

    def upsert(self, ids: List[str], embeddings: List[List[float]], payloads: List[Dict[str, Any]]):
        points = [
            PointStruct(id=str(idx), vector=emb, payload=payload)
            for idx, emb, payload in zip(ids, embeddings, payloads)
        ]
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        # Also persist to Neon DB so the UI can fetch chunks from the relational database
        from core.database import SessionLocal
        from models.knowledge import DocumentChunkDB
        import time
        
        db = SessionLocal()
        try:
            chunks = []
            for i in range(len(ids)):
                payload = payloads[i]
                doc_id = payload.get("document_id", "")
                
                chunk = DocumentChunkDB(
                    id=ids[i],
                    document_id=doc_id,
                    chunk_number=payload.get("chunk_number", i),
                    title=payload.get("title", ""),
                    content=payload.get("content", payload.get("text", "")),
                    embedding=embeddings[i],
                    metadata_col=payload,
                    token_count=payload.get("token_count", 0),
                    created_at=time.time(),
                    updated_at=time.time()
                )
                chunks.append(chunk)
                
            db.bulk_save_objects(chunks)
            db.commit()
            logger.info(f"Persisted {len(ids)} chunks to Neon DB.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error persisting chunks to Neon DB: {e}")
            raise e
        finally:
            db.close()

    def search(self, query_embedding: List[float], top_k: int = 5, filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        query_filter = None
        if filter_dict:
            must_conditions = []
            for key, value in filter_dict.items():
                must_conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
            query_filter = Filter(must=must_conditions)

        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            query_filter=query_filter,
            limit=top_k
        )
        
        results = []
        for hit in search_result.points:
            # We return the payload as the result, since that's what pgvector likely returns
            res_dict = hit.payload.copy() if hit.payload else {}
            res_dict["id"] = hit.id
            res_dict["score"] = hit.score
            
            # Map content to text if needed by the knowledge search step
            if "content" in res_dict and "text" not in res_dict:
                res_dict["text"] = res_dict["content"]
                
            # The retriever expects 'payload' directly in some cases, and 'metadata' in others
            res_dict["payload"] = hit.payload
            res_dict["metadata"] = hit.payload
                
            results.append(res_dict)
            
        return results

    def delete(self, ids: List[str]):
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=PointIdsList(
                points=[str(i) for i in ids],
            ),
        )
        
        # Also delete from Neon DB
        from core.database import SessionLocal
        from models.knowledge import DocumentChunkDB
        from sqlalchemy import delete as sql_delete
        
        db = SessionLocal()
        try:
            stmt = sql_delete(DocumentChunkDB).where(DocumentChunkDB.id.in_(ids))
            db.execute(stmt)
            db.commit()
            logger.info(f"Deleted chunks from Neon DB: {ids}")
        finally:
            db.close()
