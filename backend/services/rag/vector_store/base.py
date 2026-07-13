from abc import ABC, abstractmethod
from typing import List, Dict, Any

class VectorStoreProvider(ABC):
    @abstractmethod
    def upsert(self, ids: List[str], embeddings: List[List[float]], payloads: List[Dict[str, Any]]):
        pass

    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int = 5, filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        pass
        
    @abstractmethod
    def delete(self, ids: List[str]):
        pass
