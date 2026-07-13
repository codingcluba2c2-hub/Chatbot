from abc import ABC, abstractmethod
from typing import List

class BaseEmbeddingProvider(ABC):
    @property
    def dimension(self) -> int:
        return 384
        
    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass
