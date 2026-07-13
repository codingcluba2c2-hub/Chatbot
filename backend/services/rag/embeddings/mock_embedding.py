import hashlib
from typing import List
from .base import BaseEmbeddingProvider

class MockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Since we cannot call Gemini/OpenAI, we use a mock embedding that generates 
    deterministic pseudo-random vectors based on the text hash.
    For a production system without API access, one would use SentenceTransformers here.
    """
    def embed_query(self, text: str) -> List[float]:
        # Generate a deterministic vector based on text
        h = int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16)
        vec = []
        for i in range(self.dimension):
            vec.append(((h >> (i % 32)) & 1) - 0.5)
        
        # Normalize
        norm = sum([v**2 for v in vec])**0.5
        if norm > 0:
            return [v/norm for v in vec]
        return vec

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_query(t) for t in texts]
