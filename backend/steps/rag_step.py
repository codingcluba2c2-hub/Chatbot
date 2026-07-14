# backend/steps/rag_step.py
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from repositories.registry import settings_repo
from services.rag.vector_store import get_vector_store
from services.rag.embeddings import get_embedding_provider
from services.rag.retriever import RetrieverEngine
from services.rag.reranker import RerankerEngine
from services.rag.response_builder import RAGResponseBuilder
import time

class RAGStep(PipelineStep):
    def __init__(self):
        super().__init__()
        self.vector_store = get_vector_store()
        self.embedding_provider = get_embedding_provider()
        self.retriever_engine = RetrieverEngine(self.vector_store, self.embedding_provider)
        # In a real app we'd inject this via DI, but for now singleton is fine
        self.reranker = RerankerEngine.get_instance()

    def process(self, context: PipelineContext) -> PipelineResult:
        settings = settings_repo.get_by_id("default")
        # We retrieve more chunks now (e.g. 15-20) for the Cross-Encoder to evaluate
        top_k = settings.top_k * 3 if settings else 15
        final_k = settings.top_k if settings else 5
        # Adaptive threshold: 0.0 means we just trust the cross-encoder's top K if positive
        threshold = 0.0

        t0 = time.time()
        
        # Use expanded query if available, fallback to normalized message
        search_query = context.metadata.get("expanded_query", context.normalized_message)
        
        # 1. Retrieve (Hybrid: Dense + BM25 + RRF)
        retrieval_result = self.retriever_engine.retrieve(search_query, top_k=top_k)
        retrieved_chunks = retrieval_result["accepted"]
        
        # 2. Rerank (Cross-Encoder)
        reranked_chunks = self.reranker.rerank(search_query, retrieved_chunks, top_k=final_k, threshold=threshold)
        
        t1 = time.time()
        duration_ms = int((t1 - t0) * 1000)
        
        cross_encoder_scores = [round(c.get("cross_encoder_score", 0), 4) for c in reranked_chunks]
        
        trace_metadata = {
            "query": context.normalized_message,
            "expanded_query": search_query,
            "vector_provider": self.vector_store.__class__.__name__,
            "embedding_model": getattr(self.embedding_provider, 'model_name', 'MockModel'),
            "embedding_dimension": self.embedding_provider.dimension,
            "vector_collection": "knowledge_base",
            "top_k_retrieved": top_k,
            "top_k_reranked": final_k,
            "threshold": threshold,
            "chunks_retrieved_hybrid": len(retrieved_chunks),
            "chunks_passed_reranker": len(reranked_chunks),
            "search_duration_ms": duration_ms,
            "reranked_scores": cross_encoder_scores,
            "highest_ce_score": max(cross_encoder_scores) if cross_encoder_scores else 0,
            "lowest_ce_score": min(cross_encoder_scores) if cross_encoder_scores else 0
        }
        
        if not reranked_chunks:
            # Fallback to the next step
            return PipelineResult(
                continue_pipeline=True,
                metadata=trace_metadata
            )
            
        # Context Builder: Structure the final prompt
        context_text = RAGResponseBuilder.build_context(reranked_chunks)
        
        # We don't bypass LLM. We pass the context to the LLM step!
        context.metadata["rag_context"] = context_text
        context.current_intent = "knowledge_base"
        
        # We let the LLM step handle natural language summarization!
        return PipelineResult(
            continue_pipeline=True,
            intent="knowledge_base",
            metadata=trace_metadata
        )
