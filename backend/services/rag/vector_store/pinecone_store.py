from typing import List, Dict, Any
from .base import VectorStoreProvider
from core.logger import get_logger

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
