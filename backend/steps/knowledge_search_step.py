from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from services.rag.retriever import get_retriever
import time

class KnowledgeSearchStep(PipelineStep):
    def __init__(self):
        pass
        
    def process(self, context: PipelineContext) -> PipelineResult:
        if context.current_intent in ["greeting", "farewell", "gibberish", "fastpath"]:
            return PipelineResult(continue_pipeline=True)
            
        if not context.metadata.get("is_meaningful", True):
            context.metadata["knowledge_search_decision"] = "SKIPPED (Gibberish)"
            return PipelineResult(continue_pipeline=True)
            
        search_query = context.normalized_message
        
        t0 = time.time()
        retriever = get_retriever()
        if not retriever:
            raise RuntimeError("Knowledge Search failed because Retriever could not be initialized.")
            
        retrieval_result = retriever.retrieve(search_query, top_k=5)
        t1 = time.time()
        
        retrieved_chunks = retrieval_result.get("accepted", [])
        
        if not retrieved_chunks:
            context.metadata["knowledge_search_decision"] = "REJECTED (Low Similarity)"
            return PipelineResult(continue_pipeline=True)
            
        context.metadata["knowledge_search_decision"] = "EXECUTED"
        context.metadata["top_score"] = retrieved_chunks[0]["score"]
        
        # Build prompt context
        context_text = ""
        for i, chunk in enumerate(retrieved_chunks):
            source = chunk.get("metadata", {}).get("source", "Unknown")
            text = chunk.get("text", "").strip()
            context_text += f"[Document {i+1} | Source: {source}]\n{text}\n\n"
            
        context.metadata["rag_context"] = context_text
        context.metadata["rag_chunks"] = retrieved_chunks
        context.metadata["retrieval_latency_ms"] = int((t1 - t0) * 1000)
        context.current_intent = "Knowledge"
        
        # If the query is short (like a job title), register it as the active entity for follow-ups
        if len(search_query.split()) <= 4:
            context.entities["knowledge_search_topic"] = search_query
        
        return PipelineResult(continue_pipeline=True)
