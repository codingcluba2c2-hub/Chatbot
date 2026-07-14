from typing import List
from .base import BaseEmbeddingProvider
from core.logger import get_logger
from core.config import EMBEDDING_MODEL

logger = get_logger(__name__)

class SentenceTransformerProvider(BaseEmbeddingProvider):
    _cached_model = None

    def __init__(self, model_name: str = None):
        self.model_name = model_name or EMBEDDING_MODEL
        self._dimension = 384
        try:
            from sentence_transformers import SentenceTransformer
            if SentenceTransformerProvider._cached_model is None:
                logger.info(f"Loading embedding model {self.model_name}...")
                SentenceTransformerProvider._cached_model = SentenceTransformer(self.model_name)
                logger.info("Embedding model loaded successfully.")
            
            self.model = SentenceTransformerProvider._cached_model
            # Override dimension if possible
            if hasattr(self.model, 'get_sentence_embedding_dimension'):
                self._dimension = self.model.get_sentence_embedding_dimension()
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
        import os
        os.environ["OMP_NUM_THREADS"] = "1"
        embeddings = self.model.encode(texts, batch_size=8, show_progress_bar=False)
        return embeddings.tolist()
