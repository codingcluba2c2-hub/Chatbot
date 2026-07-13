import os

code = """
# --- Tools Endpoints ---
@router.get("/tools", response_model=List[ToolModel])
def get_tools(skip: int = 0, limit: int = 100):
    return tool_repo.get_all(skip=skip, limit=limit)

@router.get("/tools/{id}", response_model=ToolModel)
def get_tool(id: str):
    item = tool_repo.get(id)
    if not item:
        raise HTTPException(status_code=404, detail="Tool not found")
    return item

@router.post("/tools", response_model=ToolModel)
def create_tool(item: ToolBase):
    db_item = ToolModel(**item.model_dump())
    created = tool_repo.create(db_item)
    log_audit("create", "Tool", created.id, new_value=created.model_dump())
    return created

@router.put("/tools/{id}", response_model=ToolModel)
def update_tool(id: str, item: ToolBase):
    existing = tool_repo.get(id)
    if not existing:
        raise HTTPException(status_code=404, detail="Tool not found")
        
    db_item = ToolModel(**item.model_dump(), id=id, created_at=existing.created_at)
    updated = tool_repo.update(id, db_item)
    
    if updated:
        log_audit("update", "Tool", id, old_value=existing.model_dump(), new_value=updated.model_dump())
        return updated
    raise HTTPException(status_code=404, detail="Tool not found")

@router.delete("/tools/{id}")
def delete_tool(id: str):
    existing = tool_repo.get(id)
    if existing:
        tool_repo.delete(id)
        log_audit("delete", "Tool", id, old_value=existing.model_dump())
        return {"ok": True}
    raise HTTPException(status_code=404, detail="Tool not found")
"""

with open('backend/api/routes/admin.py', 'r') as f:
    content = f.read()

# Add ToolModel and tool_repo to imports
content = content.replace("IntentModel,", "IntentModel, ToolBase, ToolModel,")
content = content.replace("intent_repo,", "intent_repo, tool_repo,")

content += code

with open('backend/api/routes/admin.py', 'w') as f:
    f.write(content)

print("Added Tool endpoints to admin.py")
