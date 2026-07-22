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
from core.config import USE_LLM_FOR_RAG
from typing import List, Dict, Any
import time

def get_fallback_result(context: PipelineContext) -> PipelineResult:
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
        
    fallback_component = {
        "type": "fallback",
        "prefix": "I couldn't find any information related to",
        "query": context.normalized_message,
        "suffix": "in the current enterprise knowledge base.",
        "suggestions": suggestions
    }
    
    return PipelineResult(
        continue_pipeline=False,
        stop=True,
        intent="Fallback",
        response="",
        components=[fallback_component],
        metadata=context.metadata
    )


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
        
        # Check if ContextResolver provided context
        if "ConversationContextResolver" in context.metadata:
            last_chunks = context.metadata.get("previous_retrieved_chunks", [])
            node_id = context.metadata.get("previous_knowledge_node")
            
            if not last_chunks and node_id:
                from core.database import knowledge_node_repo
                node = knowledge_node_repo.get_by_id(node_id)
                if node:
                    last_chunks = [{"text": getattr(node, "response_markdown", "") or getattr(node, "description", ""), "score": 1.0}]
                    
            if last_chunks:
                logger.info(f"KnowledgeSearch bypassed: Reusing {len(last_chunks)} chunks from previous context.")
                context_text = ""
                for i, chunk in enumerate(last_chunks):
                    text = chunk.get("text", "").strip()
                    context_text += f"Document {i+1}:\n{text}\n\n"
                    
                context.metadata["rag_context"] = context_text
                context.metadata["rag_chunks"] = last_chunks
                context.metadata["knowledge_search_decision"] = "REUSED_CONTEXT"
                context.metadata["retrieval_latency_ms"] = int((time.time() - t0) * 1000)
                context.current_intent = "Knowledge (Context Reuse)"
                return PipelineResult(continue_pipeline=True)
        
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
            return get_fallback_result(context)
            
        context.metadata["knowledge_search_decision"] = "EXECUTED"
        
        # Remove duplicates
        seen_texts = set()
        unique_chunks = []
        for c in valid_chunks:
            text = c.get("text", "").strip()
            if text not in seen_texts:
                seen_texts.add(text)
                unique_chunks.append(c)
                
        # Lexical Reranking: promote chunks that have high keyword overlap with the query
        query_words = set(search_query.lower().split())
        for c in unique_chunks:
            text_lower = c.get("text", "").lower()
            lexical_matches = sum(1 for w in query_words if w in text_lower)
            # Combine vector score with lexical density (simple hybrid)
            c["rerank_score"] = c.get("score", 0) + (lexical_matches * 0.05)
            
        unique_chunks.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        
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
        
        # Register the primary entity for the ConversationStateManager
        best_title = final_chunks[0].get("metadata", {}).get("title") if final_chunks and "metadata" in final_chunks[0] else None
        
        entity = best_title or search_query
        heading = ""
        
        if entity:
            lower_entity = entity.lower()
            
            # If the entity is literally just the heading, fallback to search query
            if lower_entity == "overview" or lower_entity == "details":
                heading = entity
                entity = search_query
            else:
                if " overview" in lower_entity:
                    heading = "Overview"
                    entity = entity.replace(" Overview", "").replace(" overview", "").strip()
                elif " details" in lower_entity:
                    heading = "Details"
                    entity = entity.replace(" Details", "").replace(" details", "").strip()
                
        context.entities["current_entity"] = entity
        context.entities["current_heading"] = heading
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
            context.metadata["llm_used"] = False
            
            context.current_intent = "Fallback"
            
            context.metadata["response_source"] = "Fallback"
                
            return get_fallback_result(context)
            
        # We have chunks, let's use the context built in KnowledgeSearchStep
        filtered_context = context.metadata.get("rag_context", "")
        
        if not USE_LLM_FOR_RAG:
            final_response = filtered_context.replace("Document 1:\n", "").strip() # Minimal formatting for raw
            # Remove "Document X:\n" prefixes if multiple chunks to keep it clean
            import re
            final_response = re.sub(r"Document \d+:\n", "", final_response).strip()
            
            t1 = time.perf_counter()
            context.metadata["llm_latency_ms"] = 0
            context.metadata["llm_used"] = False
            context.metadata["fallback_used"] = False
            context.current_intent = "Knowledge"
            
            greeting_prefix = context.metadata.get("greeting_prefix", "")
            if greeting_prefix:
                final_response = f"{greeting_prefix}\n\n{final_response}"
                
            return PipelineResult(
                continue_pipeline=False,
                stop=True,
                intent="Knowledge",
                response=final_response
            )
            
        provider = get_llm_provider()
        llm_success = False
        final_response = ""
        final_intent = ""
        
        if provider:
            system_prompt = (
                "You are an enterprise knowledge assistant.\n"
                "Answer ONLY using the provided context. Your goal is to make the answer readable, professional and conversational.\n"
                "Generate rich, structured responses using Markdown formatting. Use headings (#, ##), bold (**), bullet lists (•), numbered lists, and short paragraphs.\n"
                "Do not expose metadata, chunk IDs, similarity scores, or payload fields.\n"
                "Convert the retrieved information into a well-formatted markdown response. Preserve headings, lists, and hierarchy when available in the context.\n"
                "Do NOT invent headings or create fake sections. If the chunk contains a single paragraph, return a single paragraph.\n"
                "Never merge everything into one paragraph. Keep paragraph separation.\n"
                "Never invent information. Do not hallucinate. Do not use external knowledge.\n"
                "Do not remove important information or aggressively summarize. Preserve useful details.\n"
                "Choose response length dynamically: small question -> short answer (2-4 lines), broad question -> comprehensive response (150-300 words).\n"
                "If the user asks about a specific topic (e.g., 'What is salary?'), return ONLY that information. Do not include unrelated info.\n"
                "If the user asks a broad topic (e.g., 'Tell me about Product Designer'), return a full overview (Overview, Skills, Experience, Education, Salary) if present.\n"
                "The context may contain noisy text from PDFs. Ignore noise and extract ONLY what matches the query.\n"
                "Only say you couldn't find the information if the query is TRULY not mentioned anywhere."
            )
            
            try:
                prompt = f"User Query: {context.normalized_message}\n\nContext:\n{filtered_context}\n\nPlease provide a helpful, richly formatted markdown response based ONLY on the context."
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
                llm_success = True
                
                context.metadata["llm_used"] = True
                context.metadata["fallback_used"] = False
                
            except Exception as e:
                logger.error(f"LLM generation failed: {e}. Switching to fallback.")
                llm_success = False
                
        # If LLM failed (e.g. 429 quota, timeout), use local fallback
        if not llm_success:
            logger.warning("LLM generation failed, returning fallback message.")
            context.metadata["llm_used"] = False
            context.metadata["fallback_used"] = True
            
            return get_fallback_result(context)
            
        t1 = time.perf_counter()
        context.metadata["llm_latency_ms"] = int((t1 - t0) * 1000)
        context.current_intent = final_intent
        
        # If the LLM explicitly states it couldn't find the answer in the chunks
        if "couldn't find" in final_response.lower() or "do not know" in final_response.lower():
            context.metadata["fallback_used"] = True
            context.metadata["response_source"] = "LLM Rejected (Fallback Triggered)"
            
            return get_fallback_result(context)
        
        # Prepend greeting if present
        greeting_prefix = context.metadata.get("greeting_prefix", "")
        if greeting_prefix:
            final_response = f"{greeting_prefix}\n\n{final_response}"
            
        return PipelineResult(
            continue_pipeline=False,
            stop=True,
            intent=final_intent,
            response=final_response,
            metadata={"llm_used": context.metadata.get("llm_used", False)}
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




