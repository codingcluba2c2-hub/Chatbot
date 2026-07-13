import os

os.makedirs('backend/services/rag/vector_store', exist_ok=True)
os.makedirs('backend/services/rag/embeddings', exist_ok=True)
os.makedirs('backend/services/rag/reranker', exist_ok=True)

with open('backend/services/rag/vector_store/base.py', 'w') as f:
    f.write('''\
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseVectorStore(ABC):
    @abstractmethod
    def upsert(self, ids: List[str], embeddings: List[List[float]], payloads: List[Dict[str, Any]]):
        pass

    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int = 5, filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        pass
        
    @abstractmethod
    def delete(self, ids: List[str]):
        pass
''')

with open('backend/services/rag/vector_store/qdrant_store.py', 'w') as f:
    f.write('''\
from typing import List, Dict, Any
from .base import BaseVectorStore
from core.logger import get_logger

logger = get_logger(__name__)

class QdrantVectorStore(BaseVectorStore):
    def __init__(self, collection_name: str = "knowledge_base"):
        self.collection_name = collection_name
        self.client = None
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
            self.client = QdrantClient(":memory:") # Using in-memory for zero-dependency local dev
            
            # Create collection if not exists
            try:
                self.client.get_collection(self.collection_name)
            except Exception:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
                )
            logger.info("Qdrant client initialized.")
        except ImportError:
            logger.error("qdrant-client not installed.")
            
    def upsert(self, ids: List[str], embeddings: List[List[float]], payloads: List[Dict[str, Any]]):
        if not self.client: return
        from qdrant_client.http import models
        points = [
            models.PointStruct(id=uid, vector=emb, payload=payload) 
            for uid, emb, payload in zip(ids, embeddings, payloads)
        ]
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logger.info(f"Upserted {len(points)} points into Qdrant.")

    def search(self, query_embedding: List[float], top_k: int = 5, filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        if not self.client: return []
        from qdrant_client.http import models
        
        qdrant_filter = None
        if filter_dict:
            # Simple match filter builder
            must_conditions = []
            for k, v in filter_dict.items():
                must_conditions.append(models.FieldCondition(key=k, match=models.MatchValue(value=v)))
            qdrant_filter = models.Filter(must=must_conditions)
            
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=qdrant_filter,
            limit=top_k
        )
        
        # Convert to standardized dict format
        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload
            }
            for hit in results
        ]
        
    def delete(self, ids: List[str]):
        if not self.client: return
        from qdrant_client.http import models
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(points=ids)
        )
''')

with open('backend/services/rag/embeddings/base.py', 'w') as f:
    f.write('''\
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
''')

with open('backend/services/rag/embeddings/mock_embedding.py', 'w') as f:
    f.write('''\
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
''')

with open('backend/services/rag/retriever.py', 'w') as f:
    f.write('''\
from typing import List, Dict, Any
from .vector_store.base import BaseVectorStore
from .embeddings.base import BaseEmbeddingProvider
from core.logger import get_logger

logger = get_logger(__name__)

class RetrieverEngine:
    def __init__(self, vector_store: BaseVectorStore, embedding_provider: BaseEmbeddingProvider):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider

    def retrieve(self, query: str, top_k: int = 5, threshold: float = 0.80) -> List[Dict[str, Any]]:
        # 1. Embed Query
        logger.info(f"Embedding query: {query}")
        query_embedding = self.embedding_provider.embed_query(query)
        
        # 2. Vector Search (Filter only published documents)
        results = self.vector_store.search(
            query_embedding=query_embedding, 
            top_k=top_k, 
            filter_dict={"status": "published"}
        )
        
        # 3. Similarity Evaluation
        valid_chunks = []
        rejected_chunks = []
        for res in results:
            if res["score"] >= threshold:
                valid_chunks.append(res)
            else:
                rejected_chunks.append(res)
                
        logger.info(f"Retrieved {len(valid_chunks)} chunks above threshold {threshold}")
        return {
            "accepted": valid_chunks,
            "rejected": rejected_chunks,
            "threshold": threshold,
            "query": query
        }
''')

with open('backend/services/rag/response_builder.py', 'w') as f:
    f.write('''\
from typing import List, Dict, Any

class RAGResponseBuilder:
    @staticmethod
    def build_fallback() -> str:
        return "I don't have enough information regarding this topic."

    @staticmethod
    def build_response(accepted_chunks: List[Dict[str, Any]]) -> str:
        if not accepted_chunks:
            return RAGResponseBuilder.build_fallback()
            
        # Normally this would be fed to an LLM. Since we CANNOT use an LLM,
        # we will deterministically return a concatenation of the top retrieved text.
        
        # We ensure no hallucination by strictly returning the exact chunk text.
        text_responses = []
        for hit in accepted_chunks:
            payload = hit["payload"]
            text_responses.append(payload.get("content", ""))
            
        merged_text = "\\n\\n".join(text_responses)
        return f"Based on the knowledge base:\\n\\n{merged_text}"
        
    @staticmethod
    def build_citations(accepted_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        components = []
        for i, hit in enumerate(accepted_chunks):
            payload = hit["payload"]
            score = round(hit["score"] * 100, 1)
            doc_name = payload.get("doc_name", "Unknown Document")
            
            # Use dynamic UI components for citations
            components.append({
                "type": "card",
                "props": {
                    "title": f"Source {i+1}: {doc_name}",
                    "subtitle": f"Similarity: {score}%",
                    "description": payload.get("content", "")[:100] + "..."
                }
            })
        return components
''')

with open('backend/steps/rag_step.py', 'w') as f:
    f.write('''\
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from services.rag.retriever import RetrieverEngine
from services.rag.vector_store.qdrant_store import QdrantVectorStore
from services.rag.embeddings.mock_embedding import MockEmbeddingProvider
from services.rag.response_builder import RAGResponseBuilder
import time

class RAGStep(PipelineStep):
    def __init__(self):
        self.vector_store = QdrantVectorStore()
        self.embedding_provider = MockEmbeddingProvider()
        self.retriever = RetrieverEngine(self.vector_store, self.embedding_provider)

    def process(self, context: PipelineContext) -> PipelineResult:
        query = context.normalized_message
        
        # Configuration
        top_k = context.metadata.get("rag_top_k", 5)
        threshold = context.metadata.get("rag_threshold", 0.70) # Lowered for mock embeddings
        
        start_time = time.time()
        retrieval_result = self.retriever.retrieve(query, top_k=top_k, threshold=threshold)
        latency = (time.time() - start_time) * 1000
        
        accepted = retrieval_result["accepted"]
        
        # Append RAG metrics to trace
        context.metadata["rag_metrics"] = {
            "top_k": top_k,
            "latency_ms": round(latency, 2),
            "retrieved_count": len(accepted) + len(retrieval_result["rejected"]),
            "accepted_count": len(accepted),
            "rejected_count": len(retrieval_result["rejected"]),
        }
        
        if not accepted:
            # Deterministic fallback, immediately return
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent="RAG_Fallback",
                response=RAGResponseBuilder.build_fallback()
            )
            
        # Build strict response and citations
        response_text = RAGResponseBuilder.build_response(accepted)
        citation_components = RAGResponseBuilder.build_citations(accepted)
        
        return PipelineResult(
            continue_pipeline=False,
            stop=True,
            intent="RAG_Answer",
            response=response_text,
            components=citation_components
        )
''')
