from core.config import VECTOR_PROVIDER
from .base import VectorStoreProvider
from .qdrant_store import QdrantProvider
from .pinecone_store import PineconeProvider

_vector_store_instance = None

def get_vector_store(collection_name: str = None) -> VectorStoreProvider:
    global _vector_store_instance
    if not _vector_store_instance:
        print("Connecting Qdrant...")
        if VECTOR_PROVIDER.lower() == "pinecone":
            _vector_store_instance = PineconeProvider(collection_name)
        else:
            _vector_store_instance = QdrantProvider(collection_name)
    return _vector_store_instance
