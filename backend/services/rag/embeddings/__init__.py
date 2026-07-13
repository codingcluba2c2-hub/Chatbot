from .base import BaseEmbeddingProvider
from .mock_embedding import MockEmbeddingProvider
from .sentence_transformer_provider import SentenceTransformerProvider

def get_embedding_provider() -> BaseEmbeddingProvider:
    # Use real embeddings if installed
    try:
        import sentence_transformers
        return SentenceTransformerProvider()
    except ImportError:
        return MockEmbeddingProvider()
