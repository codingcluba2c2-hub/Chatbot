"""
Purpose: Embedding generation integration.
Responsibilities: Connect to embedding providers (e.g. HuggingFace, OpenAI).
Flow: Used by RAG and Knowledge parsing.
"""

from typing import List

class DummyEmbeddingProvider:
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[0.0] * 384 for _ in texts]
        
    def embed_query(self, text: str) -> List[float]:
        return [0.0] * 384

_provider = None

def get_embedding_provider():
    global _provider
    if _provider is None:
        try:
            from sentence_transformers import SentenceTransformer
            class RealProvider:
                def __init__(self):
                    self.model = SentenceTransformer('all-MiniLM-L6-v2')
                def embed_documents(self, texts: List[str]) -> List[List[float]]:
                    return self.model.encode(texts).tolist()
                def embed_query(self, text: str) -> List[float]:
                    return self.model.encode([text])[0].tolist()
            _provider = RealProvider()
        except ImportError:
            _provider = DummyEmbeddingProvider()
    return _provider
