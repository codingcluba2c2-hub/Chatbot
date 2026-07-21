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
            # Native Postgres Hybrid Search using pgvector distance and ts_rank_cd for full-text search
            # We use a raw SQL query for optimal performance and access to FTS functions
            
            filter_clauses = ""
            params = {
                "query": query, 
                "query_vec": str(query_embedding), 
                "top_k": top_k
            }
            
            if filter_dict:
                filters = []
                for idx, (k, v) in enumerate(filter_dict.items()):
                    if k == "document_id":
                        filters.append(f"document_id = :f_val_{idx}")
                    else:
                        filters.append(f"metadata_col->>'{k}' = :f_val_{idx}")
                    params[f"f_val_{idx}"] = str(v)
                
                if filters:
                    filter_clauses = "WHERE " + " AND ".join(filters)

            sql = f"""
                SELECT 
                    id, 
                    metadata_col,
                    1.0 - (embedding <=> :query_vec::vector) AS cosine_sim,
                    ts_rank_cd(to_tsvector('english', content), plainto_tsquery('english', :query)) AS keyword_score
                FROM document_chunks
                {filter_clauses}
                ORDER BY (1.0 - (embedding <=> :query_vec::vector)) + ts_rank_cd(to_tsvector('english', content), plainto_tsquery('english', :query)) * 0.2 DESC
                LIMIT :top_k
            """
            
            results = db.execute(text(sql), params).fetchall()
            
            scored_results = []
            for row in results:
                hybrid_score = float(row.cosine_sim) + (float(row.keyword_score) * 0.2)
                scored_results.append({
                    "id": row.id,
                    "raw_score": float(row.cosine_sim),
                    "keyword_score": float(row.keyword_score),
                    "score": hybrid_score,
                    "payload": row.metadata_col
                })
                
            return scored_results
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []
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
