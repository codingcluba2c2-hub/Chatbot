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
        else:
            # Fallback to pgvector anyway as it's the only supported one now
            print(f"Warning: {VECTOR_PROVIDER} is not supported. Using pgvector.")
            _vector_store_instance = PgVectorProvider(collection_name)
            
    return _vector_store_instance
