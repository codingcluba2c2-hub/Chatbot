from typing import List, Dict, Any
from .base import VectorStoreProvider
from core.database import SessionLocal
from models.knowledge import DocumentChunkDB
from sqlalchemy import select, delete, text
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
                
            db.bulk_save_objects(chunks)
            db.commit()
            logger.info(f"Upserted {len(ids)} chunks into pgvector.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error upserting to pgvector: {e}")
            raise e
        finally:
            db.close()

    def search(self, query: str, query_embedding: List[float], top_k: int = 5, filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            # 1. Vector Search
            stmt = select(DocumentChunkDB)
            if filter_dict:
                for k, v in filter_dict.items():
                    if k == "document_id":
                        stmt = stmt.where(DocumentChunkDB.document_id == v)
                    else:
                        stmt = stmt.where(DocumentChunkDB.metadata_col[k].astext == str(v))
                        
            stmt_vector = stmt.order_by(DocumentChunkDB.embedding.cosine_distance(query_embedding)).limit(top_k * 2)
            vector_results = db.execute(stmt_vector).scalars().all()
            
            # 2. Keyword/Full-Text Search (Fallback using ilike for simplicity and robustness without schema changes)
            # A more robust FTS requires TSVector column, but we can do a quick memory-based keyword match or basic SQL filtering on the top docs
            # Since we want enterprise hybrid, we will fetch top K*2 by vector, then re-score them using BM25-like logic in Python.
            
            # Reconstruct response
            import numpy as np
            q_vec = np.array(query_embedding)
            
            scored_results = []
            query_terms = [t.lower() for t in query.replace('-', ' ').split() if len(t) > 2]
            
            for chunk in vector_results:
                c_vec = np.array(chunk.embedding)
                cosine_sim = np.dot(q_vec, c_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(c_vec))
                
                # BM25-lite keyword scoring on the fetched chunks
                text_content = chunk.content.lower()
                keyword_score = 0.0
                for term in query_terms:
                    count = text_content.count(term)
                    if count > 0:
                        # Simple TF normalization
                        tf = count / (count + 0.5 + 1.5 * (len(text_content.split()) / 50))
                        keyword_score += tf * 0.2  # weight
                
                hybrid_score = float(cosine_sim) + keyword_score
                
                scored_results.append({
                    "id": chunk.id,
                    "raw_score": float(cosine_sim),
                    "keyword_score": keyword_score,
                    "score": hybrid_score,
                    "payload": chunk.metadata_col
                })
                
            # Sort by hybrid score
            scored_results.sort(key=lambda x: x["score"], reverse=True)
            return scored_results[:top_k]
        finally:
            db.close()
            
    def delete(self, ids: List[str]):
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
