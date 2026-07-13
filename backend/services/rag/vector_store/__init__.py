from core.config import VECTOR_PROVIDER
from .base import VectorStoreProvider
from .qdrant_store import QdrantProvider
from .pinecone_store import PineconeProvider

def get_vector_store(collection_name: str = None) -> VectorStoreProvider:
    if VECTOR_PROVIDER.lower() == "pinecone":
        return PineconeProvider(collection_name)
    return QdrantProvider(collection_name)
