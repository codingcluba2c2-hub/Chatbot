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

    def retrieve(self, query: str, top_k: int = 5, threshold: float = 0.45) -> Dict[str, Any]:
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
                top_k=top_k * 2
            )
        else:
            # Fallback for old vector stores
            dense_results = self.vector_store.search(
                query_embedding=query_embedding, 
                top_k=top_k * 2
            )
            rescored_results = sorted(dense_results, key=lambda x: x.get("score", 0), reverse=True)
        
        # Adaptive Thresholding & Fallback
        HARD_MIN_THRESHOLD = 0.50
        
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
