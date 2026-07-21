from chatbot.pipeline import PipelineStep, PipelineStepResult, PipelineContext
from core.logger import get_logger
"""
Purpose: RAG logic.
Responsibilities: Retrieve docs and generate answers.
Flow: Core answer logic.
"""

from services.embeddings import get_embedding_provider
from services.vectorstore import get_vector_store
from chatbot.pipeline import PipelineContext
from chatbot.pipeline import PipelineResult
from chatbot.llm import get_llm_provider
from typing import List, Dict, Any
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
            
        # Top K = 10
        retrieval_result = retriever.retrieve(search_query, top_k=10)
        t1 = time.time()
        
        # Apply similarity threshold (handled largely in retriever, but we enforce it strictly here)
        threshold = 0.55
        raw_chunks = retrieval_result.get("accepted", [])
        valid_chunks = [c for c in raw_chunks if c.get("score", 0) >= threshold]
        
        if not valid_chunks:
            context.metadata["knowledge_search_decision"] = "REJECTED (Low Similarity)"
            return PipelineResult(
                stop=True,
                intent="Fallback",
                response="Sorry, I couldn't find this information in the current knowledge base.",
                metadata=context.metadata
            )
            
        context.metadata["knowledge_search_decision"] = "EXECUTED"
        
        # Remove duplicates
        seen_texts = set()
        unique_chunks = []
        for c in valid_chunks:
            text = c.get("text", "").strip()
            if text not in seen_texts:
                seen_texts.add(text)
                unique_chunks.append(c)
                
        # Rerank (Stub: Sorting by lexical density + score as a secondary metric)
        # Assuming Qdrant already gives good vector similarity, we sort them by score.
        unique_chunks.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # Keep best 3 chunks
        final_chunks = unique_chunks[:3]
        
        context.metadata["top_score"] = final_chunks[0]["score"]
        
        # Build clean context
        context_text = ""
        for i, chunk in enumerate(final_chunks):
            text = chunk.get("text", "").strip()
            context_text += f"Document {i+1}:\n{text}\n\n"
            
        context.metadata["rag_context"] = context_text
        context.metadata["rag_chunks"] = final_chunks
        context.metadata["retrieval_latency_ms"] = int((t1 - t0) * 1000)
        context.current_intent = "Knowledge"
        
        # If the query is short, register it as the active entity for follow-ups
        if len(search_query.split()) <= 4:
            context.entities["knowledge_search_topic"] = search_query
        
        return PipelineResult(continue_pipeline=True)



logger = get_logger(__name__)

class ResponseGeneratorStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        if getattr(self, 'stop', False):
            return PipelineResult(continue_pipeline=False)
            
        t0 = time.perf_counter()
        
        # Determine if we should generate a response
        decision = context.metadata.get("knowledge_search_decision", "SKIPPED")
        if decision.startswith("REJECTED") or decision == "SKIPPED (Gibberish)":
            t1 = time.perf_counter()
            context.metadata["llm_latency_ms"] = int((t1 - t0) * 1000)
            context.metadata["fallback_used"] = True
            context.metadata["gemini_used"] = False
            
            context.current_intent = "Fallback"
            
            # Sub-ms deterministic suggestion engine
            text_lower = context.normalized_message.lower()
            suggestions = []
            
            if "salary" in text_lower or "pay" in text_lower or "hr" in text_lower or "leave" in text_lower:
                suggestions = ["Leave Policy", "Attendance", "HR Contact", "Employee Benefits"]
            elif "tech" in text_lower or "software" in text_lower or "react" in text_lower or "node" in text_lower:
                suggestions = ["AI Services", "React", "Node.js", "Cloud", "Projects"]
            elif "company" in text_lower or "about" in text_lower or "founder" in text_lower:
                suggestions = ["Founder", "Mission", "Vision", "Services", "Contact", "company about"]
            else:
                suggestions = ["Overview", "Office Timings", "Leave Policy", "Contact", "Services", "Career", "Help"]
                
            from components.factory import ComponentBuilder
            fallback_component = ComponentBuilder.fallback(context.normalized_message, suggestions)
            
            # Keep string response empty, let frontend render the component
            final_response = ""
            
            # Developer mode metrics
            context.metadata["fallback_trigger"] = decision
            context.metadata["suggestions_generated"] = len(suggestions)
            context.metadata["response_source"] = "Fallback"
                
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent="Fallback",
                response=final_response,
                components=[fallback_component]
            )
            
        # We have chunks, let's use the context built in KnowledgeSearchStep
        filtered_context = context.metadata.get("rag_context", "")
        
        provider = get_llm_provider()
        gemini_success = False
        final_response = ""
        final_intent = ""
        
        if provider:
            system_prompt = (
                "You are an enterprise AI assistant.\n"
                "Use ONLY the supplied context.\n"
                "Never invent information.\n"
                "Never answer using external knowledge.\n"
                "If the context is insufficient, say you couldn't find the information."
            )
            
            try:
                prompt = f"Question: {context.normalized_message}\n\nContext:\n{filtered_context}"
                config = {
                    "system_prompt": system_prompt,
                    "temperature": 0.2
                }
                
                result = provider.generate(prompt, config)
                
                import json
                try:
                    res_data = json.loads(result.text)
                    final_response = res_data.get("response", result.text)
                except:
                    final_response = result.text
                final_intent = "Knowledge"
                gemini_success = True
                
                context.metadata["gemini_used"] = True
                context.metadata["fallback_used"] = False
                
            except Exception as e:
                logger.error(f"Gemini generation failed: {e}. Switching to Local Response Generator.")
                gemini_success = False
                
        # If Gemini failed (e.g. 429 quota, timeout), use local fallback
        if not gemini_success:
            logger.warning("Gemini generation failed, returning fallback message.")
            final_response = "Sorry, I couldn't find this information in the current knowledge base."
            final_intent = "Knowledge (Fallback)"
            
            context.metadata["gemini_used"] = False
            context.metadata["fallback_used"] = True
            
        t1 = time.perf_counter()
        context.metadata["llm_latency_ms"] = int((t1 - t0) * 1000)
        context.current_intent = final_intent
        
        # If the LLM explicitly states it couldn't find the answer in the chunks
        if "couldn't find" in final_response.lower() or "do not know" in final_response.lower():
            context.metadata["fallback_used"] = True
            context.metadata["response_source"] = "LLM Rejected (Fallback Triggered)"
            
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent="Fallback",
                response="Sorry, I couldn't find this information in the current knowledge base.",
                components=[]
            )
        
        # Prepend greeting if present
        greeting_prefix = context.metadata.get("greeting_prefix", "")
        if greeting_prefix:
            final_response = f"{greeting_prefix}\n\n{final_response}"
            
        return PipelineResult(
            continue_pipeline=False,
            stop=True,
            intent=final_intent,
            response=final_response
        )



logger = get_logger(__name__)


logger = get_logger(__name__)

class Retriever:
    def __init__(self):
        self.vector_store = get_vector_store()
        self.embedding_provider = get_embedding_provider()

    def retrieve(self, query: str, top_k: int = 5, threshold: float = 0.45, filter_dict: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.embedding_provider:
            raise RuntimeError("Embedding provider is not configured.")
        if not self.vector_store:
            raise RuntimeError("Vector store is not configured.")
            
        logger.info(f"Retrieving for query: {query}")
        
        # Embed Query
        query_embedding = self.embedding_provider.embed_query(query)
        
        # Vector Store Hybrid Search (fetches dense + local TF-IDF rerank)
        # We pass query to search so it can perform the keyword hybrid steps
        if hasattr(self.vector_store.__class__, 'search') and 'query' in self.vector_store.__class__.search.__code__.co_varnames:
            rescored_results = self.vector_store.search(
                query=query,
                query_embedding=query_embedding, 
                top_k=top_k * 2,
                filter_dict=filter_dict
            )
        else:
            dense_results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k * 2,
                filter_dict=filter_dict
            )
            
            # Hybrid Keyword Search Fallback
            try:
                from core.database import SessionLocal
                from core.models import DocumentChunkDB
                from sqlalchemy import or_
                db = SessionLocal()
                try:
                    keywords = [w.strip('?"\',.').lower() for w in query.split() if len(w.strip('?"\',.')) > 4]
                    if keywords:
                        conditions = [DocumentChunkDB.content.ilike(f"%{kw}%") for kw in keywords]
                        
                        db_query = db.query(DocumentChunkDB).filter(or_(*conditions))
                        if filter_dict and "document_id" in filter_dict:
                            db_query = db_query.filter(DocumentChunkDB.document_id == filter_dict["document_id"])
                            
                        # Fetch up to 1000 candidate chunks that match at least one keyword
                        candidate_chunks = db_query.limit(1000).all()
                        
                        # Rank them by how many keywords they contain
                        scored_candidates = []
                        for c in candidate_chunks:
                            text_lower = (c.content or "").lower()
                            match_count = sum(1 for kw in keywords if kw in text_lower)
                            scored_candidates.append((match_count, c))
                            
                        # Sort by highest match count first
                        scored_candidates.sort(key=lambda x: x[0], reverse=True)
                        
                        # Take the best matches (up to top_k)
                        for match_count, c in scored_candidates[:top_k]:
                            hybrid_score = 0.85 + (match_count * 0.01)
                            
                            # Check if Qdrant already returned this chunk
                            existing_idx = next((i for i, dr in enumerate(dense_results) if dr.get("id") == c.id), -1)
                            
                            if existing_idx != -1:
                                # Chunk exists in Qdrant, boost its score to whichever is higher
                                dense_results[existing_idx]["score"] = max(dense_results[existing_idx].get("score", 0), hybrid_score)
                            else:
                                # Chunk doesn't exist, append it
                                payload_dict = dict(c.metadata_col) if c.metadata_col else {}
                                payload_dict["content"] = c.content
                                payload_dict["chunk_id"] = c.id
                                
                                dense_results.append({
                                    "id": c.id,
                                    "score": hybrid_score,  
                                    "text": c.content,
                                    "payload": payload_dict
                                })
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Keyword search fallback failed: {e}")
                
            rescored_results = sorted(dense_results, key=lambda x: x.get("score", 0), reverse=True)
        
        # Adaptive Thresholding & Fallback
        HARD_MIN_THRESHOLD = 0.20
        
        valid_chunks = []
        # Merge nearby/duplicate chunks if they belong to same section
        seen_contents = set()
        for c in rescored_results:
            if c.get("score", 0) >= HARD_MIN_THRESHOLD:
                content_hash = hash(c.get("payload", {}).get("content", ""))
                if content_hash not in seen_contents:
                    valid_chunks.append(c)
                    seen_contents.add(content_hash)
                    
        valid_chunks = valid_chunks[:top_k]
        
        rejection_reason = "None"
        if not valid_chunks and rescored_results:
            rejection_reason = f"All chunks fell below strict threshold ({HARD_MIN_THRESHOLD})."
            
        return {
            "accepted": valid_chunks,
            "rejected": [c for c in rescored_results if c not in valid_chunks],
            "threshold": HARD_MIN_THRESHOLD,
            "query": query
        }

_retriever_instance = None

def get_retriever() -> Retriever:
    global _retriever_instance
    if not _retriever_instance:
        _retriever_instance = Retriever()
        print("Retriever Ready")
    return _retriever_instance

_retriever_instance = None

def get_retriever() -> Retriever:
    global _retriever_instance
    if not _retriever_instance:
        _retriever_instance = Retriever()
        print("Retriever Ready")
    return _retriever_instance


