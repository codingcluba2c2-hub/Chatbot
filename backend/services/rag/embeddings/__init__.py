from .base import BaseEmbeddingProvider
from .mock_embedding import MockEmbeddingProvider
from .sentence_transformer_provider import SentenceTransformerProvider

_embedding_instance = None

def get_embedding_provider() -> BaseEmbeddingProvider:
    global _embedding_instance
    if not _embedding_instance:
        print("Loading Embedding Model...")
        try:
            import sentence_transformers
            _embedding_instance = SentenceTransformerProvider()
        except ImportError:
            _embedding_instance = MockEmbeddingProvider()
        print("Embedding Loaded")
    return _embedding_instance
