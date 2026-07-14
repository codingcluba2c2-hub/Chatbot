import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import get_logger
from services.rag.vector_store import get_vector_store
from services.rag.embeddings import get_embedding_provider
from services.rag.retriever import RetrieverEngine
from services.rag.reranker import RerankerEngine
import time

logger = get_logger("RetrievalTest")

def main():
    queries = [
        "Working Hours",
        "Leave Policy",
        "HR Email",
        "Office Address",
        "Technology Stack",
        "Founder",
        "Company Name"
    ]
    
    logger.info("Initializing vector store and embedding provider...")
    vector_store = get_vector_store()
    embedding_provider = get_embedding_provider()
    
    retriever_engine = RetrieverEngine(vector_store, embedding_provider)
    reranker = RerankerEngine.get_instance()
    
    total_queries = len(queries)
    successful_retrievals = 0
    
    for query in queries:
        logger.info(f"\n--- Testing Query: '{query}' ---")
        t0 = time.time()
        
        # We skip LLM expansion here just to test pure retriever baseline
        hybrid_res = retriever_engine.retrieve(query, top_k=15)
        chunks = hybrid_res["accepted"]
        
        if not chunks:
            logger.warning(f"Failed to retrieve ANY chunks for '{query}'")
            continue
            
        reranked = reranker.rerank(query, chunks, top_k=5, threshold=0.0)
        
        duration = time.time() - t0
        logger.info(f"Retrieved {len(reranked)} valid chunks in {duration*1000:.2f}ms")
        
        if reranked:
            successful_retrievals += 1
            for i, chunk in enumerate(reranked, 1):
                score = chunk.get("cross_encoder_score", 0)
                content = chunk["payload"].get("content", "").replace("\n", " ")[:100]
                logger.info(f" [{i}] Score: {score:.4f} | {content}...")
        else:
            logger.warning(f"Reranker filtered out all chunks for '{query}'")
            
    recall_at_5 = (successful_retrievals / total_queries) * 100
    logger.info(f"\n=============================")
    logger.info(f"Final Recall@5: {recall_at_5:.2f}%")
    logger.info(f"=============================")

if __name__ == "__main__":
    main()
