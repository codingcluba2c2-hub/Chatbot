"""
Purpose: Admin API routes.
Responsibilities: Dashboard and configuration.
Flow: Admin entrypoint.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, TypeVar, Generic
import re

from core.database import greeting_repo, farewell_repo, faq_repo, fastpath_repo, knowledge_node_repo
from core.schemas import Greeting, Farewell, FAQ, FastPath, KnowledgeNode


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
            return {"status": "deleted"}
        raise HTTPException(status_code=400, detail="Delete failed")
        
    @router.post(f"/{path_name}/import")
    def import_items(items: List[dict]):
        created_items = []
        for item in items:
            created = repo.create(model(**item))
            created_items.append(created.model_dump())
        log_audit("IMPORT", path_name, "bulk", new_value={"count": len(created_items)})
        return {"imported": len(created_items)}

# Create routes for all modules

def generate_greeting_regex(item: dict):
    alias_list = item.get("alias", [])
    regex_val = item.get("regex", "")
    
    # Generate regex only if it is empty and alias list has items
    if alias_list and not regex_val:
        import itertools
        patterns = []
        for alias in alias_list:
            alias = alias.strip()
            if not alias: continue
            
            compressed = ''.join(c for c, _ in itertools.groupby(alias))
            char_patterns = []
            for c in compressed:
                if c.isspace():
                    char_patterns.append(r"\s+")
                elif c.isalnum():
                    char_patterns.append(re.escape(c) + "+")
                else:
                    char_patterns.append(re.escape(c) + "+")
            patterns.append("".join(char_patterns))
            
        if patterns:
            item["regex"] = rf"(?i)\b({'|'.join(patterns)})\b"
            
    return item

create_crud_routes(router, greeting_repo, Greeting, "greetings", pre_save_hook=generate_greeting_regex)
create_crud_routes(router, farewell_repo, Farewell, "farewells", pre_save_hook=generate_greeting_regex)
create_crud_routes(router, faq_repo, FAQ, "faqs")
create_crud_routes(router, fastpath_repo, FastPath, "fastpaths")

create_crud_routes(router, knowledge_node_repo, KnowledgeNode, "knowledge_nodes")


