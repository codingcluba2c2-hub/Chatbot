from typing import List, Dict, Any
from .vector_store.base import BaseVectorStore
from .embeddings.base import BaseEmbeddingProvider
from core.logger import get_logger

logger = get_logger(__name__)

class RetrieverEngine:
    def __init__(self, vector_store: BaseVectorStore, embedding_provider: BaseEmbeddingProvider):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider

    def retrieve(self, query: str, top_k: int = 5, threshold: float = 0.80) -> List[Dict[str, Any]]:
        # 1. Embed Query
        logger.info(f"Embedding query: {query}")
        query_embedding = self.embedding_provider.embed_query(query)
        
        # 2. Vector Search (Filter only published documents)
        results = self.vector_store.search(
            query_embedding=query_embedding, 
            top_k=top_k, 
            filter_dict={"status": "published"}
        )
        
        # 3. Similarity Evaluation
        valid_chunks = []
        rejected_chunks = []
        for res in results:
            if res["score"] >= threshold:
                valid_chunks.append(res)
            else:
                rejected_chunks.append(res)
                
        logger.info(f"Retrieved {len(valid_chunks)} chunks above threshold {threshold}")
        return {
            "accepted": valid_chunks,
            "rejected": rejected_chunks,
            "threshold": threshold,
            "query": query
        }
