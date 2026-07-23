"""
Purpose: Admin API routes.
Responsibilities: Dashboard and configuration.
Flow: Admin entrypoint.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import re

from core.database import greeting_repo, faq_repo, log_audit
from core.schemas import Greeting, FAQ
from chatbot.in_memory_engine import engine


router = APIRouter(prefix="/api/admin", tags=["Admin Studio"])

def create_crud_routes(router: APIRouter, repo, model: type[BaseModel], path_name: str, pre_save_hook=None):
    
    @router.get(f"/{path_name}")
    def get_all(skip: int = 0, limit: int = 100, sort_by: str = "created_at", descending: bool = True, query: str = None):
        items = repo.get_all(skip, limit, sort_by, descending, query)
        total = repo.count()
        return {"data": [item.model_dump() for item in items], "total": total, "skip": skip, "limit": limit}
        
    @router.post(f"/{path_name}")
    def create_item(item: dict):
        try:
            if pre_save_hook:
                item = pre_save_hook(item)
            created = repo.create(model(**item))
            log_audit("CREATE", path_name, created.id, new_value=created.model_dump())
            engine.load_all()
            return created.model_dump()
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
            
    @router.put(f"/{path_name}/{{item_id}}")
    def update_item(item_id: str, item: dict):
        old_item = repo.get_by_id(item_id)
        if not old_item:
            raise HTTPException(status_code=404, detail="Item not found")
            
        old_val = old_item.model_dump()
        try:
            if pre_save_hook:
                item = pre_save_hook(item)
            updated = repo.update(item_id, model(**item))
            if updated:
                log_audit("UPDATE", path_name, item_id, old_value=old_val, new_value=updated.model_dump())
                engine.load_all()
                return updated.model_dump()
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=400, detail="Update failed")
        
    @router.delete(f"/{path_name}/{{item_id}}")
    def delete_item(item_id: str):
        old_item = repo.get_by_id(item_id)
        if not old_item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        old_val = old_item.model_dump()
        if repo.delete(item_id):
            log_audit("DELETE", path_name, item_id, old_value=old_val)
            engine.load_all()
            return {"status": "deleted"}
        raise HTTPException(status_code=400, detail="Delete failed")
        
    @router.post(f"/{path_name}/import")
    def import_items(items: List[dict]):
        created_items = []
        for item in items:
            created = repo.create(model(**item))
            created_items.append(created.model_dump())
        log_audit("IMPORT", path_name, "bulk", new_value={"count": len(created_items)})
        engine.load_all()
        return {"imported": len(created_items)}


# Greeting regex auto-generation hook
def generate_greeting_regex(item: dict):
    import itertools
    alias_list = item.get("alias", [])
    regex_val = item.get("regex", "")
    if alias_list and not regex_val:
        patterns = []
        for alias in alias_list:
            alias = alias.strip()
            if not alias: continue
            compressed = ''.join(c for c, _ in itertools.groupby(alias))
            char_patterns = []
            for c in compressed:
                if c.isspace():
                    char_patterns.append(r"\s+")
                else:
                    char_patterns.append(re.escape(c) + "+")
            patterns.append("".join(char_patterns))
        if patterns:
            item["regex"] = rf"(?i)\b({'|'.join(patterns)})\b"
    return item

create_crud_routes(router, greeting_repo, Greeting, "greetings", pre_save_hook=generate_greeting_regex)
create_crud_routes(router, faq_repo, FAQ, "faqs")


# Special endpoint: get all FAQs as parent options (title + id only)
@router.get("/faqs/parent-options")
def get_faq_parent_options():
    """Returns title+id pairs for all top-level FAQs (parent_id is None), used for parent dropdowns."""
    items = faq_repo.get_all(limit=2000)
    options = [
        {"id": item.id, "title": getattr(item, "title", "")}
        for item in items
        if getattr(item, "parent_id", None) is None and getattr(item, "status", "active") == "active"
    ]
    return {"data": options}


@router.get("/dashboard/overview")
def dashboard_overview():
    faq_count = faq_repo.count()
    return {
        "pipeline": {
            "status": "Online",
            "backend": "Running",
            "database": "Connected",
            "qdrant": "Connected",
            "gemini": "Active",
            "current_cache_status": "Enabled",
            "knowledge_documents": 12,
            "indexed_chunks": 45,
            "avg_response_time": "42ms",
            "avg_retrieval_time": "15ms"
        },
        "knowledge": {
            "embedding_model": "all-MiniLM-L6-v2"
        },
        "kpis": {
            "todays_requests": 150,
            "greeting_requests": 45,
            "knowledge_requests": 35,
            "rag_responses": 30,
            "cache_hits": 60,
            "memory_hits": 10,
            "retriever_hits": 25,
            "gemini_calls": 50,
            "fallback_responses": 2,
            "faq_count": faq_count
        }
    }
