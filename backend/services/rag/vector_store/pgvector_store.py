from typing import List, Dict, Any
from .base import VectorStoreProvider
from core.database import SessionLocal
from models.knowledge import DocumentChunkDB
from sqlalchemy import select, delete
from core.logger import get_logger
import time

logger = get_logger(__name__)

class PgVectorProvider(VectorStoreProvider):
    def __init__(self, collection_name: str = None):
        self.collection_name = collection_name
        
    def upsert(self, ids: List[str], embeddings: List[List[float]], payloads: List[Dict[str, Any]]):
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
                
            # Perform a fast bulk insert
            db.bulk_save_objects(chunks)
            db.commit()
            logger.info(f"Upserted {len(ids)} chunks into pgvector.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error upserting to pgvector: {e}")
            raise e
        finally:
            db.close()

    def search(self, query_embedding: List[float], top_k: int = 5, filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            stmt = select(DocumentChunkDB)
            
            if filter_dict:
                for k, v in filter_dict.items():
                    if k == "document_id":
                        stmt = stmt.where(DocumentChunkDB.document_id == v)
                    else:
                        # For other JSON metadata
                        stmt = stmt.where(DocumentChunkDB.metadata_col[k].astext == str(v))
                        
            # Use pgvector <=> for cosine distance
            stmt = stmt.order_by(DocumentChunkDB.embedding.cosine_distance(query_embedding)).limit(top_k)
            
            # Add a resilient retry loop for transient Neon server connection drops
            import time
            from sqlalchemy.exc import OperationalError
            
            max_retries = 3
            results = []
            for attempt in range(max_retries):
                try:
                    results = db.execute(stmt).scalars().all()
                    break
                except OperationalError as e:
                    logger.warning(f"Transient DB connection error on attempt {attempt+1}/{max_retries}. Retrying in 1s...")
                    db.rollback()
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(1)
            # Reconstruct response to match what the old QdrantProvider returned
            response = []
            for chunk in results:
                # We can calculate score in python or just query it if needed, but doing it in python is fine for top_k
                import numpy as np
                q_vec = np.array(query_embedding)
                c_vec = np.array(chunk.embedding)
                cosine_sim = np.dot(q_vec, c_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(c_vec))
                
                response.append({
                    "id": chunk.id,
                    "score": float(cosine_sim),
                    "payload": chunk.metadata_col
                })
                
            return response
        finally:
            db.close()
            
    def delete(self, ids: List[str]):
        # The Qdrant implementation took a list of point IDs.
        db = SessionLocal()
        try:
            stmt = delete(DocumentChunkDB).where(DocumentChunkDB.id.in_(ids))
            db.execute(stmt)
            db.commit()
            logger.info(f"Deleted chunks from pgvector: {ids}")
        finally:
            db.close()

    def get_document_embeddings(self, doc_id: str) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            stmt = select(DocumentChunkDB).where(DocumentChunkDB.document_id == doc_id)
            results = db.execute(stmt).scalars().all()
            
            embeddings_list = []
            for chunk in results:
                vector_data = chunk.embedding.tolist() if hasattr(chunk.embedding, "tolist") else list(chunk.embedding) if chunk.embedding is not None else []
                embeddings_list.append({
                    "id": chunk.id,
                    "vector": vector_data,
                    "payload": chunk.metadata_col
                })
            return embeddings_list
        finally:
            db.close()
