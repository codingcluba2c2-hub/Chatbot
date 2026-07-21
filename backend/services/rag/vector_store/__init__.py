from core.config import VECTOR_PROVIDER
from .base import VectorStoreProvider
from .pgvector_store import PgVectorProvider
from core.config import VECTOR_PROVIDER

_vector_store_instance = None

def get_vector_store(collection_name: str = None) -> VectorStoreProvider:
    global _vector_store_instance
    if _vector_store_instance is None:
        if VECTOR_PROVIDER == "pgvector":
            print("Connecting pgvector...")
            _vector_store_instance = PgVectorProvider(collection_name)
        elif VECTOR_PROVIDER == "qdrant":
            print("Connecting qdrant...")
            from core.config import QDRANT_URL, QDRANT_API_KEY, VECTOR_COLLECTION
            from .qdrant_store import QdrantProvider
            _vector_store_instance = QdrantProvider(
                collection_name=collection_name or VECTOR_COLLECTION,
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY
            )
        else:
            # Fallback to pgvector anyway as it's the only supported one now
            print(f"Warning: {VECTOR_PROVIDER} is not supported. Using pgvector.")
            _vector_store_instance = PgVectorProvider(collection_name)
            
    return _vector_store_instance
