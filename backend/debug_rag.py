import asyncio
from services.rag.retriever import RetrieverEngine
from services.rag.reranker import RerankerEngine
from services.rag.vector_store import get_vector_store
from services.rag.embeddings import get_embedding_provider
import logging

logging.basicConfig(level=logging.INFO)

async def test():
    vector_store = get_vector_store()
    embedding_provider = get_embedding_provider()
    retriever = RetrieverEngine(vector_store, embedding_provider)
    reranker = RerankerEngine.get_instance()
    
    query = "How many earned leaves?"
    
    print(f"Query: {query}")
    retrieval_result = retriever.retrieve(query, top_k=15)
    retrieved_chunks = retrieval_result["accepted"]
    
    print(f"Hybrid Retriever found {len(retrieved_chunks)} chunks.")
    for i, c in enumerate(retrieved_chunks):
        print(f"[{i}] {c.get('content', '')[:100]}...")
        
    reranked = reranker.rerank(query, retrieved_chunks, top_k=5, threshold=0.0)
    print(f"\nReranker returned {len(reranked)} chunks.")
    for i, c in enumerate(reranked):
        print(f"[{i}] Score: {c.get('cross_encoder_score')} | {c.get('content', '')[:100]}...")

if __name__ == "__main__":
    asyncio.run(test())
