from typing import List, Dict, Any
from .vector_store import get_vector_store
from .embeddings import get_embedding_provider
from core.logger import get_logger

logger = get_logger(__name__)

from typing import List, Dict, Any
from .vector_store import get_vector_store
from .embeddings import get_embedding_provider
from core.logger import get_logger

logger = get_logger(__name__)

class Retriever:
    def __init__(self):
        self.vector_store = get_vector_store()
        self.embedding_provider = get_embedding_provider()

    def retrieve(self, query: str, top_k: int = 5, threshold: float = 0.45, filter_dict: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.embedding_provider:
            raise RuntimeError("Embedding provider is not configured.")
        if not self.vector_store:
            raise RuntimeError("Vector store is not configured.")
            
        logger.info(f"Retrieving for query: {query}")
        
        # Embed Query
        query_embedding = self.embedding_provider.embed_query(query)
        
        # Vector Store Hybrid Search (fetches dense + local TF-IDF rerank)
        # We pass query to search so it can perform the keyword hybrid steps
        if hasattr(self.vector_store.__class__, 'search') and 'query' in self.vector_store.__class__.search.__code__.co_varnames:
            rescored_results = self.vector_store.search(
                query=query,
                query_embedding=query_embedding, 
                top_k=top_k * 2,
                filter_dict=filter_dict
            )
        else:
            dense_results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k * 2,
                filter_dict=filter_dict
            )
            
            # Hybrid Keyword Search Fallback
            try:
                from core.database import SessionLocal
                from models.knowledge import DocumentChunkDB
                from sqlalchemy import or_
                db = SessionLocal()
                try:
                    keywords = [w.strip('?"\',.').lower() for w in query.split() if len(w.strip('?"\',.')) > 4]
                    if keywords:
                        conditions = [DocumentChunkDB.content.ilike(f"%{kw}%") for kw in keywords]
                        
                        db_query = db.query(DocumentChunkDB).filter(or_(*conditions))
                        if filter_dict and "document_id" in filter_dict:
                            db_query = db_query.filter(DocumentChunkDB.document_id == filter_dict["document_id"])
                            
                        # Fetch up to 1000 candidate chunks that match at least one keyword
                        candidate_chunks = db_query.limit(1000).all()
                        
                        # Rank them by how many keywords they contain
                        scored_candidates = []
                        for c in candidate_chunks:
                            text_lower = (c.content or "").lower()
                            match_count = sum(1 for kw in keywords if kw in text_lower)
                            scored_candidates.append((match_count, c))
                            
                        # Sort by highest match count first
                        scored_candidates.sort(key=lambda x: x[0], reverse=True)
                        
                        # Take the best matches (up to top_k)
                        for match_count, c in scored_candidates[:top_k]:
                            hybrid_score = 0.85 + (match_count * 0.01)
                            
                            # Check if Qdrant already returned this chunk
                            existing_idx = next((i for i, dr in enumerate(dense_results) if dr.get("id") == c.id), -1)
                            
                            if existing_idx != -1:
                                # Chunk exists in Qdrant, boost its score to whichever is higher
                                dense_results[existing_idx]["score"] = max(dense_results[existing_idx].get("score", 0), hybrid_score)
                            else:
                                # Chunk doesn't exist, append it
                                payload_dict = dict(c.metadata_col) if c.metadata_col else {}
                                payload_dict["content"] = c.content
                                payload_dict["chunk_id"] = c.id
                                
                                dense_results.append({
                                    "id": c.id,
                                    "score": hybrid_score,  
                                    "text": c.content,
                                    "payload": payload_dict
                                })
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Keyword search fallback failed: {e}")
                
            rescored_results = sorted(dense_results, key=lambda x: x.get("score", 0), reverse=True)
        
        # Adaptive Thresholding & Fallback
        HARD_MIN_THRESHOLD = 0.20
        
        valid_chunks = []
        # Merge nearby/duplicate chunks if they belong to same section
        seen_contents = set()
        for c in rescored_results:
            if c.get("score", 0) >= HARD_MIN_THRESHOLD:
                content_hash = hash(c.get("payload", {}).get("content", ""))
                if content_hash not in seen_contents:
                    valid_chunks.append(c)
                    seen_contents.add(content_hash)
                    
        valid_chunks = valid_chunks[:top_k]
        
        rejection_reason = "None"
        if not valid_chunks and rescored_results:
            rejection_reason = f"All chunks fell below strict threshold ({HARD_MIN_THRESHOLD})."
            
        return {
            "accepted": valid_chunks,
            "rejected": [c for c in rescored_results if c not in valid_chunks],
            "threshold": HARD_MIN_THRESHOLD,
            "query": query
        }

_retriever_instance = None

def get_retriever() -> Retriever:
    global _retriever_instance
    if not _retriever_instance:
        _retriever_instance = Retriever()
        print("Retriever Ready")
    return _retriever_instance

_retriever_instance = None

def get_retriever() -> Retriever:
    global _retriever_instance
    if not _retriever_instance:
        _retriever_instance = Retriever()
        print("Retriever Ready")
    return _retriever_instance
