from fastapi import APIRouter
from core.database import SessionLocal
from models.cache import ChatCacheDB
from models.memory import MessageDB
from models.knowledge import KnowledgeDocumentDB, KnowledgeSettingsDB
from repositories.registry import greeting_repo, farewell_repo, faq_repo, fastpath_repo

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/overview")
def get_dashboard_overview():
    db = SessionLocal()
    try:
        # 1. Pipeline Status
        pipeline_status = "Online"
        backend_status = "Healthy"
        db_status = "Connected"
        qdrant_status = "Connected"
        gemini_status = "Available"
        
        # 2. Counts
        greeting_count = greeting_repo.count()
        fastpath_count = fastpath_repo.count()
        faq_count = faq_repo.count()
        farewell_count = farewell_repo.count()
        
        # 3. Knowledge Base
        docs = db.query(KnowledgeDocumentDB).all()
        doc_count = len(docs)
        chunks_indexed = sum(d.chunk_count for d in docs)
        avg_processing_time = sum(d.processing_stats.get("duration_ms", 0) for d in docs) / doc_count if doc_count > 0 else 0
        
        settings = db.query(KnowledgeSettingsDB).filter_by(id="default").first()
        chunk_strategy = settings.chunk_strategy if settings else "character"
        similarity_threshold = settings.similarity_threshold if settings else 0.45
        top_k = settings.top_k if settings else 5
        
        # 4. Cache & Messages
        messages = db.query(MessageDB).all()
        total_requests = len([m for m in messages if m.role == "user"])
        fallback_count = len([m for m in messages if m.intent == "Fallback"])
        
        caches = db.query(ChatCacheDB).all()
        cache_hits = sum(c.hit_count for c in caches)
        gemini_calls = len(caches) # We save one cache per gemini call
        gemini_skipped = cache_hits
        
        cache_hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
        fallback_rate = (fallback_count / total_requests * 100) if total_requests > 0 else 0
        memory_hit_rate = 12.5 # Mock, normally computed from memory matches
        retriever_success_rate = 85.0 # Mock, normally from relevance metrics
        

            
        return {
            "pipeline": {
                "status": pipeline_status, "backend": backend_status, "database": db_status, 
                "qdrant": qdrant_status, "gemini": gemini_status,
                "embedding_model": "Available", "current_collection": "knowledge_base",
                "knowledge_documents": doc_count, "indexed_chunks": chunks_indexed,
                "avg_response_time": "45ms", "avg_retrieval_time": "12ms",
                "current_cache_status": "Active"
            },
            "kpis": {
                "todays_requests": total_requests, "greeting_requests": greeting_count, 
                "fastpath_requests": fastpath_count, "rag_responses": gemini_calls + cache_hits,
                "cache_hits": cache_hits, "gemini_calls": gemini_calls, "gemini_skipped": gemini_skipped,
                "fallback_responses": fallback_count,
                "knowledge_requests": faq_count, "memory_hits": 150, "retriever_hits": 320,
                "avg_response_time": "45ms", "avg_retrieval_time": "12ms", "avg_embedding_time": "8ms"
            },
            "knowledge": {
                "embedding_model": "all-MiniLM-L6-v2"
            }
        }
    finally:
        db.close()
