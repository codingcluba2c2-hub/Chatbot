from steps.base_step import PipelineStep
from pipeline.pipeline_context import PipelineContext
from pipeline.pipeline_result import PipelineResult
from services.rag.embeddings import get_embedding_provider
from core.database import SessionLocal
from models.cache import ChatCacheDB
import hashlib
import numpy as np
import time

def cosine_similarity(vec1, vec2):
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot / (norm1 * norm2))

class SemanticCacheStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineResult:
        query = context.normalized_message
        
        # 1. Hash the query for exact match (L1/L2 equivalent)
        q_hash = hashlib.sha256(query.encode('utf-8')).hexdigest()
        
        db = SessionLocal()
        cutoff_time = time.time() - (30 * 60) # 30 mins TTL
        
        try:
            # 1. Check exact hash first
            exact_match = db.query(ChatCacheDB).filter(
                ChatCacheDB.question_hash == q_hash,
                ChatCacheDB.created_at > cutoff_time
            ).first()
            if exact_match:
                exact_match.hit_count += 1
                db.commit()
                context.metadata["cache_hit"] = True
                context.metadata["cache_type"] = "exact"
                context.metadata["cache_similarity"] = 1.0
                return PipelineResult(
                    stop=True,
                    intent=context.entities.get("intent", "Knowledge"),
                    response=exact_match.answer,
                    metadata={"cache": "exact_hit", "similarity": 1.0}
                )
            
            # 2. Semantic Search Cache (L3 equivalent)
            embedding_provider = get_embedding_provider()
            query_embedding = embedding_provider.embed_query(query)
            context.metadata["query_embedding"] = query_embedding # Save for retriever later!
            
            recent_caches = db.query(ChatCacheDB).filter(
                ChatCacheDB.created_at > cutoff_time
            ).order_by(ChatCacheDB.created_at.desc()).limit(100).all()
            
            best_score = 0.0
            best_match = None
            
            for cache_entry in recent_caches:
                if cache_entry.embedding:
                    score = cosine_similarity(query_embedding, cache_entry.embedding)
                    if score > best_score:
                        best_score = score
                        best_match = cache_entry
            
            if best_match and best_score > 0.95:
                best_match.hit_count += 1
                db.commit()
                context.metadata["cache_hit"] = True
                context.metadata["cache_type"] = "semantic"
                context.metadata["cache_similarity"] = best_score
                return PipelineResult(
                    stop=True,
                    intent=context.entities.get("intent", "Knowledge"),
                    response=best_match.answer,
                    metadata={"cache": "semantic_hit", "similarity": best_score}
                )
                
            context.metadata["cache_hit"] = False
            context.metadata["question_hash"] = q_hash
            return PipelineResult(continue_pipeline=True)
            
        finally:
            db.close()
