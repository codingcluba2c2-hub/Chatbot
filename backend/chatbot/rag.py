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
        if context.current_intent in ["greeting", "gibberish", "FAQ"]:
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
            
        # Adjust top_k based on intent
        is_overview = context.current_intent == "ENTERPRISE_OVERVIEW"
        target_top_k = 50 if is_overview else 50 # Retrieve top 50 as requested
        
        retrieval_result = retriever.retrieve(search_query, top_k=target_top_k)
        t1 = time.time()
        
        # Apply similarity threshold (handled largely in retriever, but we enforce it strictly here)
        threshold = 0.25 # Lowered threshold because we are doing deep reranking now
        raw_chunks = retrieval_result.get("accepted", [])
        valid_chunks = [c for c in raw_chunks if c.get("raw_score", c.get("score", 0)) >= threshold or c.get("keyword_score", 0) > 0]
        
        if not valid_chunks:
            context.metadata["knowledge_search_decision"] = "REJECTED (Low Similarity)"
            return get_fallback_result(context)
            
        context.metadata["knowledge_search_decision"] = "EXECUTED"
        
        # Remove duplicates based on ID or text
        seen_ids = set()
        seen_texts = set()
        unique_chunks = []
        for c in valid_chunks:
            text = c.get("text", c.get("payload", {}).get("content", "")).strip()
            cid = c.get("id")
            if text not in seen_texts and cid not in seen_ids:
                seen_texts.add(text)
                seen_ids.add(cid)
                unique_chunks.append(c)
                
        # Weighted Fusion Reranking
        query_words = set(search_query.lower().split())
        query_lower = search_query.lower()
        
        for c in unique_chunks:
            payload = c.get("payload", {})
            title = (payload.get("title") or "").lower()
            heading = (payload.get("heading") or payload.get("section") or "").lower()
            metadata_str = str(payload).lower()
            
            # Scores from DB (PgVector provides these)
            vector_score = c.get("raw_score", c.get("score", 0))
            bm25_score = c.get("keyword_score", 0)
            
            # Scale BM25 score (usually ranges 0-5, let's normalize roughly to 0-1)
            norm_bm25 = min(bm25_score / 5.0, 1.0)
            
            # Weighted Fusion: Metadata +4, Heading +3, Title +5, BM25 +2, Vector +2
            fusion_score = (vector_score * 2.0) + (norm_bm25 * 2.0)
            reasons = [f"Vector(x2)={vector_score*2.0:.2f}", f"BM25(x2)={norm_bm25*2.0:.2f}"]
            
            # Title match
            if title and (title == query_lower or any(w in title for w in query_words if len(w)>4)):
                fusion_score += 5.0
                reasons.append("Title(+5)")
                
            # Heading match
            if heading and (heading == query_lower or any(w in heading for w in query_words if len(w)>4)):
                fusion_score += 3.0
                reasons.append("Heading(+3)")
                
            # Metadata match
            metadata_matches = sum(1 for w in query_words if len(w)>4 and w in metadata_str)
            if metadata_matches > 0:
                fusion_score += 4.0
                reasons.append("Metadata(+4)")
                
            c["fusion_score"] = fusion_score
            c["ranking_reason"] = ", ".join(reasons)
            
        unique_chunks.sort(key=lambda x: x.get("fusion_score", 0), reverse=True)
        
        # Cross Encoder Reranking Mock
        # Since running a true CrossEncoder is slow on CPU, we apply an LLM-like strict relevance check heuristic
        # If it has a high fusion score, it passes.
        for c in unique_chunks:
            c["rerank_score"] = c.get("fusion_score", 0) * 1.1 # Mock boost
            
        # Keep best chunks
        if context.current_intent == "ENTERPRISE_OVERVIEW":
            final_chunks = unique_chunks[:50]
        else:
            final_chunks = unique_chunks[:10]
            
        discarded_chunks = [c for c in unique_chunks if c not in final_chunks]
        
        if final_chunks:
            context.metadata["top_score"] = final_chunks[0]["score"]
            context.metadata["reranked_top_score"] = final_chunks[0].get("rerank_score", 0)
        else:
            context.metadata["top_score"] = 0
            
        # Group and Merge Chunks
        grouped = {}
        for c in final_chunks:
            payload = c.get("payload", {})
            doc = payload.get("document_id", "Unknown")
            sec = payload.get("heading", payload.get("section", payload.get("title", "Details")))
            
            group_key = (doc, sec)
            if group_key not in grouped:
                grouped[group_key] = []
            grouped[group_key].append(c)
            
        merged_sections = []
        for (doc, sec), chunks in grouped.items():
            # sort chunks by chunk_number to maintain document order within the section
            chunks.sort(key=lambda x: x.get("payload", {}).get("chunk_number", 0))
            
            seen_paras = set()
            merged_paras = []
            for c in chunks:
                raw_text = c.get("text", "").strip()
                # Extract content
                lines = raw_text.split('\n')
                content_start_idx = 0
                for i, line in enumerate(lines):
                    if line.strip() == "Content":
                        content_start_idx = i + 1
                        break
                        
                clean_lines = lines[content_start_idx:]
                paras = "\n".join(clean_lines).split('\n')
                
                for p in paras:
                    p = p.strip()
                    if not p or p in seen_paras:
                        continue
                        
                    seen_paras.add(p)
                    merged_paras.append(p)
                    
            if merged_paras:
                merged_sections.append({
                    "section_name": sec,
                    "content": "\n\n".join(merged_paras),
                    "document_id": doc
                })
                
        # Semantic Ordering
        preferred_order = ["title", "overview", "location", "department", "experience", "salary", "education", "skills", "responsibilities", "benefits", "application process"]
        
        def get_order_index(sec_name):
            sec_lower = sec_name.lower()
            for i, pref in enumerate(preferred_order):
                if pref in sec_lower:
                    return i
            return 999
            
        merged_sections.sort(key=lambda x: (get_order_index(x["section_name"]), x["section_name"]))
        
        # Build clean context string with strict token limits
        context_text = ""
        context_tokens = 0
        MAX_TOKENS = 8000 if context.current_intent == "ENTERPRISE_OVERVIEW" else 2000
        CHARS_PER_TOKEN = 4
        
        for sec in merged_sections:
            sec_name = sec["section_name"].title() if sec["section_name"].lower() != "details" else "Details"
            block = f"## {sec_name}\n\n{sec['content']}\n\n"
            block_tokens = len(block) // CHARS_PER_TOKEN
            
            if context_tokens + block_tokens > MAX_TOKENS:
                break
                
            context_text += block
            context_tokens += block_tokens
            
        context.metadata["rag_context"] = context_text.strip()
        context.metadata["rag_chunks"] = final_chunks
        
        # Developer Telemetry
        context.metadata["retrieved_chunks_count"] = len(unique_chunks)
        context.metadata["selected_chunks_count"] = len(final_chunks)
        context.metadata["discarded_chunks_count"] = len(discarded_chunks)
        context.metadata["merged_chunks_count"] = len(merged_sections)
        context.metadata["context_tokens"] = context_tokens
        context.metadata["ranking_reasons"] = [{"id": c.get("id"), "reason": c.get("ranking_reason")} for c in final_chunks]
        
        context.metadata["retrieval_latency_ms"] = int((time.time() - t0) * 1000)
        if context.current_intent != "ENTERPRISE_OVERVIEW":
            context.current_intent = "Knowledge"
        
        # Register the primary entity for the ConversationStateManager
        best_title = final_chunks[0].get("payload", {}).get("title") if final_chunks and "payload" in final_chunks[0] else None
        
        entity = best_title or search_query
        heading = ""
        
        if entity:
            lower_entity = entity.lower()
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
            context.metadata["response_source"] = "Fallback"
            context.current_intent = "Fallback"
            return get_fallback_result(context)
            
        # We have chunks, let's use the context built in KnowledgeSearchStep
        filtered_context = context.metadata.get("rag_context", "")
        
        final_response = ""
        final_intent = "ENTERPRISE_OVERVIEW" if context.current_intent == "ENTERPRISE_OVERVIEW" else "Knowledge"
        
        if USE_LLM_FOR_RAG:
            from services.llm_manager import get_llm_manager
            
            if context.current_intent == "ENTERPRISE_OVERVIEW":
                system_prompt = (
                    "You are an enterprise knowledge assistant.\n"
                    "The user wants a comprehensive overview of the entire organization.\n"
                    "Based ONLY on the provided context, generate a complete, interview-ready structured report.\n"
                    "Use headings for every major topic you find in the context. For example:\n"
                    "# Company Overview\n# History\n# Vision\n# Mission\n# Core Values\n# Leadership\n"
                    "# Global Presence\n# Industries Served\n# Products\n# Technologies\n"
                    "# AI\n# Blockchain\n# DevOps\n# Careers\n# Hiring Process\n# HR Policies\n# Employee Benefits\n"
                    "CRITICAL: If a requested section is unavailable, do NOT repeatedly print 'Information not available'.\n"
                    "Instead create ONE section at the very end called '## Information Not Available' and list only the missing topics as bullet points.\n"
                    "Do not expose metadata, chunk IDs, or similarity scores.\n"
                    "Never hallucinate. Do not use external knowledge.\n"
                    "Do not limit the length of your response; provide a thorough, highly structured, and readable report."
                )
            else:
                system_prompt = (
                    "You are an enterprise knowledge assistant.\n"
                    "Answer ONLY using the provided context. Your goal is to make the answer readable, professional and conversational.\n"
                    "Generate rich, structured responses using Markdown formatting. Use headings (#, ##), bold (**), bullet lists (•), tables, code, and short paragraphs.\n"
                    "Do not expose metadata, chunk IDs, similarity scores, or payload fields.\n"
                    "Convert the retrieved information into a well-formatted markdown response. Preserve hierarchy when available.\n"
                    "Never invent information. Do not hallucinate. Do not use external knowledge.\n"
                    "CRITICAL: Answer specifically what the user asks based on the intent.\n"
                    "- If the user asks for 'Salary', return ONLY Salary and Variable Pay details. Nothing else.\n"
                    "- If the user asks for 'Experience', return ONLY experience details.\n"
                    "- If the user asks for 'Responsibilities', return ONLY responsibilities.\n"
                    "- If the user asks for 'Skills', return ONLY skills.\n"
                    "DO NOT dump all retrieved chunks if the user asked a specific question.\n"
                    "MAXIMUM LENGTH: 250 words. Be extremely concise unless the user explicitly asks for details.\n"
                    "If the user asks a broad topic (e.g., 'Tell me about Product Designer'), return a short overview (Role, Experience, Skills, Location, Salary).\n"
                    "Only say you couldn't find the information if the query is TRULY not mentioned anywhere in the context."
                )
            
            prompt = f"User Query: {context.normalized_message or context.original_message}\n\nContext:\n{filtered_context}\n\nPlease provide a helpful, richly formatted markdown response based ONLY on the context."
            
            manager = get_llm_manager()
            result = manager.generate(prompt, system_prompt, context.metadata)
            
            final_response = result.get("response", "")
            trace = result.get("trace", {})
            
            context.metadata.update(trace)
            context.metadata["llm_used"] = trace.get("Response Source") != "Local Markdown Formatter"
            
            if "couldn't find" in final_response.lower() or "do not know" in final_response.lower():
                pass # Already handled by LLM itself
                
        else:
            # Fallback to returning the grouped Markdown sections if LLM is disabled entirely
            final_response = filtered_context
            context.metadata["llm_used"] = False
            context.metadata["response_source"] = "Raw Chunks (LLM Disabled)"
            
        t1 = time.perf_counter()
        
        formatting_time_ms = int((t1 - t0) * 1000)
        context.metadata["formatting_time_ms"] = formatting_time_ms
        context.metadata["llm_latency_ms"] = formatting_time_ms
        context.metadata["response_length"] = len(final_response)
        context.metadata["fallback_used"] = context.metadata.get("Fallback Used", False)
        context.current_intent = final_intent
        
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

def initialize_retriever():
    global _retriever_instance
    if _retriever_instance is not None:
        return
        
    _retriever_instance = Retriever()
    print("Retriever Ready")

def get_retriever() -> Retriever:
    global _retriever_instance
    if _retriever_instance is None:
        raise RuntimeError("Retriever was not initialized at startup. Call initialize_retriever() first.")
    return _retriever_instance




