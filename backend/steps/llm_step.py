import logging
from typing import Dict, Any
from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from services.llm import get_llm_provider
from core.database import SessionLocal
from models.cache import ChatCacheDB
from core.circuit_breaker import llm_circuit_breaker
from services.rag.local_response_generator import LocalResponseGenerator
import time

logger = logging.getLogger(__name__)

class LLMStep(PipelineStep):
    """
    Generates a natural language response using an LLM, 
    grounded in the retrieved context if available.
    """
    def __init__(self):
        pass
        
    def process(self, context: PipelineContext) -> PipelineResult:
        rag_context = context.metadata.get("rag_context")
        
        if not context.metadata.get("is_meaningful", True):
            return PipelineResult(continue_pipeline=True)
            
        chunks = context.metadata.get("rag_chunks", [])
        if not chunks:
            return PipelineResult(continue_pipeline=True)
            
        # Circuit Breaker Check - if OPEN, completely skip Gemini
        if not llm_circuit_breaker.is_allowed():
            logger.warning("Circuit Breaker is OPEN. Skipping Gemini LLM call.")
            return self._handle_fallback(context, "Circuit Breaker OPEN", 0)
            
        # Adaptive Detail Level
        word_count = len(context.normalized_message.split())
        query_lower = context.normalized_message.lower()
        needs_details = any(w in query_lower for w in ["explain", "describe", "tell me more", "complete details", "elaborate"])
        
        detail_instruction = "Return a concise professional answer in under 100 words unless the user explicitly asks for more details."
        if word_count < 6 and not needs_details:
            detail_instruction = "Return a very short, concise professional answer (1-2 sentences max)."
        elif needs_details:
            detail_instruction = "Provide a detailed, well-structured answer based strictly on the context."

        system_prompt = (
            "You are a strict enterprise AI assistant. "
            "You MUST answer ONLY using the provided context. "
            "Do not add external knowledge. "
            "If the answer is not contained in the context, reply: "
            "'I don't have information about this in the current knowledge base.'\n"
            f"{detail_instruction}\n\n"
        )
        if rag_context:
            system_prompt += f"Context:\n{rag_context}"
        
        t0 = time.time()
        # 1. Initialize Provider
        llm = get_llm_provider()
        if not llm:
            logger.error("LLM Step failed because Gemini Provider could not be initialized.")
            llm_circuit_breaker.record_failure()
            return self._handle_fallback(context, "Provider missing", int((time.time()-t0)*1000))
            
        try:
            response_result = llm.generate(
                prompt=context.normalized_message,
                config={
                    "system_prompt": system_prompt,
                    "max_tokens": 500,
                    "temperature": 0.3
                }
            )
            t1 = time.time()
            llm_circuit_breaker.record_success()
            
            try:
                import json
                parsed = json.loads(response_result.text)
                final_text = parsed.get("response", response_result.text)
                components = parsed.get("components", [])
                actions = parsed.get("actions", [])
            except Exception:
                final_text = response_result.text
                components = []
                actions = []
                
            try:
                db = SessionLocal()
                import hashlib
                q_hash = hashlib.sha256(context.normalized_message.encode()).hexdigest()
                existing = db.query(ChatCacheDB).filter(ChatCacheDB.question_hash == q_hash).first()
                if not existing:
                    new_cache = ChatCacheDB(
                        normalized_question=context.normalized_message,
                        question_hash=q_hash,
                        answer=final_text,
                        provider_used="gemini",
                        session_id=context.session_id
                    )
                    db.add(new_cache)
                    db.commit()
                db.close()
            except Exception as ce:
                logger.error(f"Failed to save to cache: {ce}")
                
            return PipelineResult(
                stop=True,
                intent=context.current_intent or "knowledge_base",
                response=final_text,
                components=components,
                actions=actions,
                metadata={
                    "gemini_status": "SUCCESS",
                    "gemini_used": True, 
                    "fallback_used": False, 
                    "response_source": "Gemini",
                    "circuit_state": llm_circuit_breaker.state,
                    "retry_count": llm_circuit_breaker.consecutive_failures,
                    "llm_latency_ms": int((t1-t0)*1000)
                }
            )
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            t1 = time.time()
            
            retry_after = None
            if "429" in str(e):
                retry_after = 60
                
            llm_circuit_breaker.record_failure(retry_after=retry_after)
            return self._handle_fallback(context, str(e), int((t1-t0)*1000))
            
    def _handle_fallback(self, context: PipelineContext, error_msg: str, latency_ms: int) -> PipelineResult:
        rag_chunks = context.metadata.get("rag_chunks", [])
        
        # Build intelligent fallback response using LocalResponseGenerator
        local_result = LocalResponseGenerator.generate(context.normalized_message, rag_chunks)
        clean_text = local_result["response"]
        local_metadata = local_result["metadata"]
        
        status_match = "FAILED"
        if "429" in error_msg:
            status_match = "FAILED (429)"
        elif "500" in error_msg:
            status_match = "FAILED (500)"
        elif "403" in error_msg or "401" in error_msg:
            status_match = "FAILED (Auth)"
        elif "timeout" in error_msg.lower() or "408" in error_msg:
            status_match = "FAILED (Timeout)"
        elif "connection" in error_msg.lower() or "socket" in error_msg.lower():
            status_match = "FAILED (Network)"
        elif "Circuit Breaker" in error_msg:
            status_match = "SKIPPED (Circuit Breaker)"
            
        try:
            db = SessionLocal()
            import hashlib
            q_hash = hashlib.sha256(context.normalized_message.encode()).hexdigest()
            existing = db.query(ChatCacheDB).filter(ChatCacheDB.question_hash == q_hash).first()
            if not existing:
                new_cache = ChatCacheDB(
                    normalized_question=context.normalized_message,
                    question_hash=q_hash,
                    answer=clean_text,
                    provider_used="knowledge_builder",
                    session_id=context.session_id
                )
                db.add(new_cache)
                db.commit()
            db.close()
        except Exception as ce:
            logger.error(f"Failed to save fallback to cache: {ce}")
            
        return PipelineResult(
            stop=True,
            intent=context.current_intent or "knowledge_base",
            response=clean_text,
            components=[],
            actions=[],
            metadata={
                "gemini_status": status_match,
                "circuit_state": llm_circuit_breaker.state,
                "llm_error": error_msg,
                "llm_latency_ms": latency_ms,
                "retry_count": llm_circuit_breaker.consecutive_failures,
                **local_metadata
            }
        )
