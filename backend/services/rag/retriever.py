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
            raise RuntimeError("Embedding provider is not configured or failed to initialize.")
        if not self.vector_store:
            raise RuntimeError("Vector store is not configured or failed to initialize.")
            
        logger.info(f"Retrieving for query: {query}")
        
        # 1. Rule-Based Query Expansion
        expanded_query = query.lower()
        expansion_rules = {
            "earned leaves": "earned leave EL EL/PL privileged leave",
            "working hours": "business hours office timing office hours shift schedule",
            "hr": "human resources employee policy hr department contact"
        }
        for k, v in expansion_rules.items():
            if k in expanded_query:
                expanded_query += f" {v}"
                
        # 2. Embed Query and Vector Search (get more chunks for reranking)
        fetch_k = max(20, top_k * 2)
        query_embedding = self.embedding_provider.embed_query(expanded_query)
        dense_results = self.vector_store.search(
            query_embedding=query_embedding, 
            top_k=fetch_k
        )
        
        # 3. Hybrid Scoring (BM25-lite keyword bonus)
        rescored_results = []
        keywords = set(expanded_query.replace("/", " ").replace("-", " ").split())
        for res in dense_results:
            base_score = res.get("score", 0.0)
            text = res.get("payload", {}).get("content", "").lower()
            
            # Strong keyword bonus for exact matches
            bonus = 0.0
            for kw in keywords:
                if len(kw) > 3 and kw in text:
                    bonus += 0.15 # Stronger boost for exact keyword matches
                    
            hybrid_score = base_score + min(bonus, 0.45) # Higher max bonus
            
            rescored_results.append({
                "id": res["id"],
                "raw_score": base_score,
                "score": hybrid_score,
                "payload": res["payload"],
                "text": res.get("payload", {}).get("content", ""),
                "metadata": res.get("payload", {}).get("metadata", {})
            })
            
        # Sort by new hybrid score
        rescored_results.sort(key=lambda x: x["score"], reverse=True)
        
        # 4. Adaptive Thresholding & Fallback
        if rescored_results:
            highest_score = rescored_results[0]["score"]
            lowest_score = rescored_results[-1]["score"]
            avg_score = sum(r["score"] for r in rescored_results) / len(rescored_results)
        else:
            highest_score = lowest_score = avg_score = 0.0
            
        HARD_MIN_THRESHOLD = 0.55
        
        # Lower threshold for short keyword queries
        if len(expanded_query.split()) <= 3:
            HARD_MIN_THRESHOLD = 0.40
            
        valid_chunks = [c for c in rescored_results if c["score"] >= HARD_MIN_THRESHOLD]
        
        rejection_reason = "None"
        if not valid_chunks and rescored_results:
            rejection_reason = f"All {len(rescored_results)} chunks fell below strict threshold ({HARD_MIN_THRESHOLD}). Triggering Fallback."
        elif not valid_chunks:
            rejection_reason = "Qdrant returned 0 results."
            
        # Truncate to final top_k
        valid_chunks = valid_chunks[:top_k]
        
        # 5. Complete Diagnostics
        logger.info("\n" + "="*50)
        logger.info(f"RETRIEVAL DIAGNOSTICS")
        logger.info(f"Original Query: {query}")
        logger.info(f"Expanded Query: {expanded_query}")
        logger.info(f"Embedding Dimension: {self.embedding_provider.dimension if hasattr(self.embedding_provider, 'dimension') else 'Unknown'}")
        logger.info(f"Collection Name: {getattr(self.vector_store, 'collection_name', 'Unknown')}")
        logger.info(f"Top K Requested: {top_k} | Fetched: {fetch_k}")
        logger.info(f"Thresholds -> Hard: {HARD_MIN_THRESHOLD}")
        logger.info(f"Scores -> High: {highest_score:.3f} | Low: {lowest_score:.3f} | Avg: {avg_score:.3f}")
        logger.info(f"Returned Results Count: {len(valid_chunks)}")
        if rejection_reason != "None":
            logger.warning(f"Rejection Reason: {rejection_reason}")
            
        for i, c in enumerate(valid_chunks):
            logger.info(f"  Chunk {i+1} | ID: {c['id']} | Raw Score: {c['raw_score']:.3f} | Hybrid Score: {c['score']:.3f} | Doc: {c['metadata'].get('source', 'Unknown')}")
        logger.info("="*50 + "\n")
        
        return {
            "accepted": valid_chunks,
            "rejected": [c for c in rescored_results if c not in valid_chunks],
            "threshold": HARD_MIN_THRESHOLD,
            "query": expanded_query
        }

_retriever_instance = None

def get_retriever() -> Retriever:
    global _retriever_instance
    if not _retriever_instance:
        _retriever_instance = Retriever()
        print("Retriever Ready")
    return _retriever_instance
