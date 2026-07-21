# backend/agents/tools.py
from typing import Dict, Any, List
from core.logger import get_logger
from services.rag.retriever import get_retriever

logger = get_logger(__name__)

def search_knowledge_base(query: str, top_k: int = 5) -> str:
    """
    Search the enterprise vector database for relevant company information, policies, guidelines, or technical documentation.
    
    Args:
        query: The user's question or search terms.
        top_k: Number of results to return.
        
    Returns:
        A formatted string of retrieved chunks with their source contexts.
    """
    try:
        retriever = get_retriever()
        results = retriever.retrieve(query, top_k=top_k)
        
        chunks = results.get("accepted", [])
        if not chunks:
            return "No relevant information found in the knowledge base."
            
        formatted_chunks = []
        for i, chunk in enumerate(chunks):
            content = chunk.get("payload", {}).get("content", chunk.get("text", ""))
            formatted_chunks.append(f"--- Chunk {i+1} ---\n{content}")
            
        return "\n\n".join(formatted_chunks)
    except Exception as e:
        logger.error(f"Error in search_knowledge_base tool: {e}")
        return f"Error retrieving knowledge: {e}"

def query_sql_database(query: str) -> str:
    """
    Query the structured relational database for metrics, counts, user stats, or other tabular data.
    (This is a placeholder for future implementation).
    """
    return "SQL Tool is not fully connected yet."
