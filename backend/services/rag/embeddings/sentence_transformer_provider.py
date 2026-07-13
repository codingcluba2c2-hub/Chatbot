from typing import List
from .base import BaseEmbeddingProvider
from core.logger import get_logger
from core.config import EMBEDDING_MODEL

logger = get_logger(__name__)

class SentenceTransformerProvider(BaseEmbeddingProvider):
    def __init__(self, model_name: str = None):
        self.model_name = model_name or EMBEDDING_MODEL
        self._dimension = 384
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            # Override dimension if possible
            if hasattr(self.model, 'get_sentence_embedding_dimension'):
                self._dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Loaded embedding model {self.model_name} (dim: {self._dimension})")
        except ImportError:
            logger.error("sentence-transformers not installed. Please install it to use SentenceTransformerProvider.")
            self.model = None
            
    @property
    def dimension(self) -> int:
        return self._dimension
        
    def embed_query(self, text: str) -> List[float]:
        if not self.model: return [0.0] * self._dimension
        # encode returns a numpy array, convert to list of floats
        return self.model.encode(text).tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not self.model: return [[0.0] * self._dimension for _ in texts]
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
