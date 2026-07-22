from core.logger import get_logger
"""
Purpose: Vector DB integration.
Responsibilities: Qdrant/PGVector connections.
Flow: Used by RAG.
"""


from abc import ABC, abstractmethod
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, PointIdsList
from sqlalchemy import select, delete, text
from typing import List, Dict, Any
import time
from core.config import VECTOR_PROVIDER
from core.database import SessionLocal
from core.models import DocumentChunkDB


class VectorStoreProvider(ABC):
    @abstractmethod
    def upsert(self, ids: List[str], embeddings: List[List[float]], payloads: List[Dict[str, Any]]):
        pass

    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int = 5, filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        pass
        
    @abstractmethod
    def delete(self, ids: List[str]):
        pass



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



logger = get_logger(__name__)

class PineconeProvider(VectorStoreProvider):
    def __init__(self, collection_name: str = "knowledge_base"):
        self.collection_name = collection_name
        
    def upsert(self, ids: List[str], embeddings: List[List[float]], payloads: List[Dict[str, Any]]):
        raise NotImplementedError("Pinecone provider requires a Pinecone API key and Pinecone client.")

    def search(self, query_embedding: List[float], top_k: int = 5, filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError("Pinecone provider requires a Pinecone API key and Pinecone client.")
        
    def delete(self, ids: List[str]):
        raise NotImplementedError("Pinecone provider requires a Pinecone API key and Pinecone client.")



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
        from core.models import DocumentChunkDB
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

    def get_document_embeddings(self, doc_id: str) -> List[Dict[str, Any]]:
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue
        
        try:
            results, next_page = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id", match=MatchValue(value=doc_id)
                        )
                    ]
                ),
                with_vectors=True,
                limit=10000
            )
            
            embeddings_list = []
            for point in results:
                embeddings_list.append({
                    "id": str(point.id),
                    "vector": point.vector,
                    "payload": point.payload
                })
            return embeddings_list
        except Exception as e:
            logger.error(f"Failed to fetch embeddings from Qdrant: {e}")
            return []

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
        from core.models import DocumentChunkDB
        from sqlalchemy import delete as sql_delete
        
        db = SessionLocal()
        try:
            stmt = sql_delete(DocumentChunkDB).where(DocumentChunkDB.id.in_(ids))
            db.execute(stmt)
            db.commit()
            logger.info(f"Deleted chunks from Neon DB: {ids}")
        finally:
            db.close()



_vector_store_instance = None

def get_vector_store(collection_name: str = None) -> VectorStoreProvider:
    global _vector_store_instance
    if _vector_store_instance is None:
        if VECTOR_PROVIDER == "pgvector":
            print("Connecting pgvector...")
            _vector_store_instance = PgVectorProvider(collection_name)
        elif VECTOR_PROVIDER == "qdrant":
            print("Connecting qdrant...")
            from core.config import QDRANT_URL, QDRANT_API_KEY, VECTOR_COLLECTION
            _vector_store_instance = QdrantProvider(
                collection_name=collection_name or VECTOR_COLLECTION,
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY
            )
        else:
            # Fallback to pgvector anyway as it's the only supported one now
            print(f"Warning: {VECTOR_PROVIDER} is not supported. Using pgvector.")
            _vector_store_instance = PgVectorProvider(collection_name)
            
    return _vector_store_instance


