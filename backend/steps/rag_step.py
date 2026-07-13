# backend/steps/rag_step.py
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from repositories.registry import settings_repo
from services.rag.vector_store import get_vector_store
from services.rag.embeddings import get_embedding_provider
import time

class RAGStep(PipelineStep):
    def __init__(self):
        super().__init__()
        self.vector_store = get_vector_store()
        self.embedding_provider = get_embedding_provider()

    def process(self, context: PipelineContext) -> PipelineResult:
        settings = settings_repo.get_by_id("default")
        top_k = settings.top_k if settings else 5
        threshold = settings.similarity_threshold if settings else 0.75

        t0 = time.time()
        
        # Generate embedding for the query
        query_embedding = self.embedding_provider.embed_query(context.normalized_message)
        
        # Search the vector store
        results = self.vector_store.search(query_embedding, top_k=top_k)
        
        # Filter by similarity threshold
        valid_chunks = []
        for res in results:
            if res.get("score", 0) >= threshold:
                valid_chunks.append(res)
                
        t1 = time.time()
        duration_ms = int((t1 - t0) * 1000)
        
        raw_scores = [round(c.get("score", 0), 4) for c in results]
        
        trace_metadata = {
            "query": context.normalized_message,
            "vector_provider": self.vector_store.__class__.__name__,
            "embedding_model": getattr(self.embedding_provider, 'model_name', 'MockModel'),
            "embedding_dimension": self.embedding_provider.dimension,
            "vector_collection": "knowledge_base",
            "top_k_requested": top_k,
            "threshold": threshold,
            "chunks_retrieved": len(results),
            "chunks_passed_threshold": len(valid_chunks),
            "search_duration_ms": duration_ms,
            "retrieved_scores": raw_scores,
            "highest_score": max(raw_scores) if raw_scores else 0,
            "lowest_score": min(raw_scores) if raw_scores else 0,
            "average_score": round(sum(raw_scores) / len(raw_scores), 4) if raw_scores else 0
        }
        
        if not valid_chunks:
            # Fallback to the next step
            return PipelineResult(
                continue_pipeline=True,
                metadata=trace_metadata
            )
            
        # Context Builder: Merge chunks into a single response
        context_text = "\n\n".join([chunk.get("payload", {}).get("content", "") for chunk in valid_chunks])
        
        # Set final response to retrieved context, bypassing fallback
        context.intent = "knowledge_base"
        
        return PipelineResult(
            stop=True,
            intent="knowledge_base",
            response=context_text,
            metadata=trace_metadata
        )
