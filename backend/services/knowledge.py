"""
Purpose: Document management.
Responsibilities: Parse and chunk files.
Flow: Used by admin APIs.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import List, Dict, Optional, Any
from typing import List, Optional
import os
import shutil
import time
from core.database import document_repo, log_audit
from core.schemas import *
from core.models import *
from services.extraction import ExtractionEngine
from services.chunking import ChunkingEngine
from services.embeddings import get_embedding_provider
from services.vectorstore import get_vector_store


router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

UPLOAD_DIR = "uploads"


def update_doc_status(doc_id: str, status: str, stats: dict = None, error: str = None, chunk_count: int = None):
    doc = document_repo.get_by_id(doc_id)
    if doc:
        doc.status = status
        doc.updated_at = time.time()
        if chunk_count is not None:
            doc.chunk_count = chunk_count
        if stats:
            if not getattr(doc, 'processing_stats', None):
                doc.processing_stats = {}
            doc.processing_stats.update(stats)
        if error:
            doc.error_message = error
        document_repo.update(doc_id, doc)
        return doc
    return None

def process_document_bg(doc_id: str, file_path: str, file_type: str):
    start_time = time.time()
    stats = {"logs": []}
    
    def log_step(msg: str):
        stats["logs"].append(f"[{time.strftime('%H:%M:%S')}] {msg}")
        update_doc_status(doc_id, doc.status, stats)
        
    doc = update_doc_status(doc_id, "validating")
    if not doc:
        return
        
    try:
        # Phase 1: Extraction & Cleaning
        log_step("Starting text extraction & cleaning...")
        doc = update_doc_status(doc_id, "extracting")
        t0 = time.time()
        raw_text, text, extraction_stats = ExtractionEngine.extract_text(file_path, file_type)
        stats.update(extraction_stats)
        
        # Save raw text for debugging
        doc.raw_text = raw_text
        document_repo.update(doc_id, doc)
        
        log_step(f"Extraction complete in {time.time() - t0:.2f}s")
        
        # Get dynamic settings
        from core.database import settings_repo
        settings = settings_repo.get_by_id("default")
        if not settings:
            from core.schemas import KnowledgeSettings
            settings = KnowledgeSettings()
            settings_repo.create(settings)

        # Phase 2: Chunking
        log_step(f"Starting chunk generation ({settings.chunk_strategy} strategy, size: {settings.chunk_size})...")
        doc = update_doc_status(doc_id, "chunking", stats)
        t0 = time.time()
        chunks_data = ChunkingEngine.chunk_text(
            raw_text, 
            document_id=doc_id
        )
        
        if not chunks_data:
            raise ValueError("Chunking engine returned 0 chunks.")
            
        stats["chunks_created"] = len(chunks_data)
        log_step(f"Created {len(chunks_data)} chunks in {time.time() - t0:.2f}s")
        
        # Phase 3: Embedding
        doc = update_doc_status(doc_id, "embedding", stats)
        log_step("Generating embeddings...")
        t0 = time.time()
        
        ids = []
        payloads = []
        texts_to_embed = []
        
        import uuid
        for c_data in chunks_data:
            chunk_id = str(uuid.uuid4())
            ids.append(chunk_id)
            texts_to_embed.append(c_data["content"])
            
            meta = c_data.get("metadata", {}).copy()
            meta.update({
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "doc_name": doc.name,
                "content": c_data["content"],
                "status": "published"
            })
            payloads.append(meta)
            
        embeddings = get_embedding_provider().embed_documents(texts_to_embed)
        stats["embeddings_generated"] = len(embeddings)
        log_step(f"Generated {len(embeddings)} embeddings in {time.time() - t0:.2f}s")
        
        # Phase 4: Indexing
        doc = update_doc_status(doc_id, "indexing", stats)
        log_step("Storing in vector database...")
        t0 = time.time()
        
        get_vector_store().upsert(ids, embeddings, payloads)
        stats["vectors_stored"] = len(ids)
        log_step(f"Indexed {len(ids)} vectors in {time.time() - t0:.2f}s")
        
        # Finalization
        stats["total_processing_time"] = round(time.time() - start_time, 2)
        update_doc_status(doc_id, "published", stats, chunk_count=len(chunks_data))
        log_audit("process", "KnowledgeDocument", doc_id, new_value={"status": "published", "chunks": len(chunks_data)})
        
    except Exception as e:
        stats["total_processing_time"] = round(time.time() - start_time, 2)
        log_step(f"ERROR: {str(e)}")
        update_doc_status(doc_id, "failed", stats, str(e))
        log_audit("process_failed", "KnowledgeDocument", doc_id, new_value={"error": str(e)})

@router.post("/upload", response_model=KnowledgeDocument)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: str = Form("general"),
    tags: str = Form(""),
    language: str = Form("en")
):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else 'txt'
    safe_filename = f"{time.time()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    file_size = os.path.getsize(file_path)
    
    # Calculate SHA-256 for deduplication
    import hashlib
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    file_hash = sha256_hash.hexdigest()
    
    # Check if duplicate exists
    all_docs = document_repo.get_all()
    for existing_doc in all_docs:
        if existing_doc.file_hash == file_hash:
            os.remove(file_path)
            raise HTTPException(409, f"Duplicate Document: This file was already uploaded as '{existing_doc.name}'")
            
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    
    doc = KnowledgeDocument(
        name=file.filename,
        category=category,
        language=language,
        tags=tag_list,
        file_path=file_path,
        file_type=file_ext,
        file_size=file_size,
        file_hash=file_hash,
        status="processing"
    )
    
    created = document_repo.create(doc)
    log_audit("create", "KnowledgeDocument", created.id, new_value=created.model_dump())
    
    # Process in background
    background_tasks.add_task(process_document_bg, created.id, file_path, file_ext)
    
    return created

@router.get("/documents", response_model=List[KnowledgeDocument])
def list_documents(skip: int = 0, limit: int = 100):
    docs = document_repo.get_all(skip=skip, limit=limit)
    # Strip raw_text to prevent massive JSON payloads during polling
    for doc in docs:
        doc.raw_text = None
    return docs

@router.get("/documents/{doc_id}", response_model=KnowledgeDocument)
def get_document(doc_id: str):
    doc = document_repo.get_by_id(doc_id)
    if not doc:
        raise HTTPException(404, "Not found")
    return doc

@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    doc = document_repo.get_by_id(doc_id)
    if doc:
        from core.database import SessionLocal
        from core.models import DocumentChunkDB
        from sqlalchemy import delete
        
        db = SessionLocal()
        try:
            # Delete chunks directly
            stmt = delete(DocumentChunkDB).where(DocumentChunkDB.document_id == doc_id)
            db.execute(stmt)
            db.commit()
        finally:
            db.close()
            
        # Delete file
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)
            
        document_repo.delete(doc_id)
        log_audit("delete", "KnowledgeDocument", doc_id)
        return {"ok": True}
    raise HTTPException(404, "Not found")

@router.get("/documents/{doc_id}/chunks", response_model=List[DocumentChunk])
def get_document_chunks(doc_id: str):
    from core.database import SessionLocal
    from core.models import DocumentChunkDB
    from sqlalchemy.orm import defer
    db = SessionLocal()
    try:
        # Defer embedding to make this query blazing fast
        db_chunks = db.query(DocumentChunkDB).filter(DocumentChunkDB.document_id == doc_id).options(defer(DocumentChunkDB.embedding)).all()
        return [
            DocumentChunk(
                id=c.id,
                document_id=c.document_id,
                content=c.content,
                metadata=c.metadata_col,
                created_at=c.created_at
            ) for c in db_chunks
        ]
    finally:
        db.close()

@router.get("/documents/{doc_id}/retrieve")
def retrieve_from_document(doc_id: str, q: str, top_k: int = 3):
    if not q:
        raise HTTPException(400, "Query parameter 'q' is required")
        
    from chatbot.rag import get_retriever
    
    # Use full hybrid retrieval pipeline instead of just raw dense vector search
    retriever = get_retriever()
    results = retriever.retrieve(q, top_k=top_k, filter_dict={"document_id": doc_id})
    
    # results["accepted"] contains the actual matched chunks
    return {"query": q, "results": results.get("accepted", [])}

@router.get("/documents/{doc_id}/embeddings")
def get_document_embeddings(doc_id: str):
    doc = document_repo.get_by_id(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
        
    vector_store = get_vector_store()
    if not hasattr(vector_store, 'get_document_embeddings'):
        raise HTTPException(501, "Vector store does not support fetching raw embeddings")
        
    raw_embeddings = vector_store.get_document_embeddings(doc_id)
    
    formatted_embeddings = []
    for i, emb in enumerate(raw_embeddings):
        payload = emb.get("payload", {})
        formatted_embeddings.append({
            "chunk_number": i + 1,
            "chunk_id": payload.get("chunk_id", emb.get("id")),
            "content": payload.get("content", ""),
            "vector_dimension": len(emb.get("vector", [])),
            "vector": emb.get("vector", [])
        })
        
    from core.config import EMBEDDING_MODEL, VECTOR_COLLECTION
    return {
        "document_id": doc_id,
        "embedding_model": EMBEDDING_MODEL,
        "dimension": 384,
        "collection": VECTOR_COLLECTION,
        "distance": "COSINE",
        "total_chunks": len(formatted_embeddings),
        "embeddings": formatted_embeddings
    }

@router.get("/chunks/{chunk_id}/embedding")
def get_chunk_embedding(chunk_id: str):
    from core.database import SessionLocal
    from core.models import DocumentChunkDB
    db = SessionLocal()
    try:
        chunk = db.query(DocumentChunkDB).filter(DocumentChunkDB.id == chunk_id).first()
        if not chunk:
            raise HTTPException(404, "Chunk not found")
            
        # Handle numpy arrays or lists from vector column
        vector_data = chunk.embedding.tolist() if hasattr(chunk.embedding, "tolist") else chunk.embedding
            
        return {
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "content": chunk.content,
            "vector_dimension": len(vector_data) if vector_data else 0,
            "vector": vector_data,
            "metadata": chunk.metadata_col
        }
    finally:
        db.close()

@router.get("/settings")
def get_settings():
    from core.database import settings_repo
    from core.schemas import KnowledgeSettings
    settings = settings_repo.get_by_id("default")
    if not settings:
        settings = KnowledgeSettings()
        settings_repo.create(settings)
    return settings

@router.put("/settings")
def update_settings(settings_update: dict):
    from core.database import settings_repo
    from core.schemas import KnowledgeSettings
    settings = settings_repo.get_by_id("default")
    if not settings:
        settings = KnowledgeSettings()
        
    for k, v in settings_update.items():
        if hasattr(settings, k):
            setattr(settings, k, v)
            
    settings.updated_at = time.time()
    updated = settings_repo.update("default", settings)
    if not updated:
        updated = settings_repo.create(settings)
    return updated

@router.post("/documents/{doc_id}/reprocess")
def reprocess_document(doc_id: str, background_tasks: BackgroundTasks):
    doc = document_repo.get_by_id(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    
    from core.database import SessionLocal
    from core.models import DocumentChunkDB
    from sqlalchemy import delete
    
    db = SessionLocal()
    try:
        stmt = delete(DocumentChunkDB).where(DocumentChunkDB.document_id == doc_id)
        db.execute(stmt)
        db.commit()
    finally:
        db.close()
        
    # Reset stats
    doc.processing_stats = {}
    doc.chunk_count = 0
    doc.status = "processing"
    document_repo.update(doc_id, doc)
    
    # Process in background
    background_tasks.add_task(process_document_bg, doc.id, doc.file_path, doc.file_type)
    return {"message": f"Successfully deleted {len(deleted_ids)} documents from {len(chunks)} chunks"}

from chatbot.pipeline import PipelineStep, PipelineContext, PipelineStepResult
class KnowledgeTreeStep(PipelineStep):
    def process(self, context: PipelineContext) -> PipelineStepResult:
        result = KnowledgeTreeService.search(context.normalized_message)
        if result:
            markdown = result.get("markdown", "")
            title = result.get("title", "")
            children = result.get("children", [])
            breadcrumbs = result.get("breadcrumbs", [])
            
            # Enterprise Entity Extraction:
            # We must lock onto the root topic (e.g. 'Product Designer') using breadcrumbs.
            root_entity = breadcrumbs[0].get("title") if breadcrumbs else title
            
            # The heading is the actual matched node (e.g. 'Overview')
            heading = title if title != root_entity else ""
            
            context.entities["current_entity"] = root_entity
            context.entities["current_heading"] = heading
            
            response = markdown if markdown else f"Found information for {title}."
            
            if breadcrumbs and len(breadcrumbs) > 0:
                crumb_text = " > ".join([b.get("title") for b in breadcrumbs])
                response = f"📍 **{crumb_text}**\n\n{response}"
                
            components = []
            
            if children:
                components.append({
                    "type": "quickReplies",
                    "items": [child.get("title") for child in children]
                })
                
            return PipelineStepResult(
                stop=True, 
                intent="KnowledgeTree", 
                response=response,
                components=components,
                metadata={"knowledge_node": result}
            )
        return PipelineStepResult(stop=False)
class KnowledgeTreeService:
    @staticmethod
    def _format_node(node: Any, children: List[Any] = None) -> Dict[str, Any]:
        if not node:
            return None
        return {
            "id": getattr(node, "id", ""),
            "title": getattr(node, "title", ""),
            "description": getattr(node, "description", ""),
            "markdown": getattr(node, "response_markdown", ""),
            "parentId": getattr(node, "parent_id", None),
            "aliases": getattr(node, "aliases", []),
            "status": getattr(node, "status", "active"),
            "children": children or []
        }

    @staticmethod
    def getChildren(node_id: str) -> List[Dict[str, Any]]:
        nodes = knowledge_node_repo.get_all(limit=1000)
        parent_node = next((n for n in nodes if getattr(n, "id", "") == node_id), None)
        parent_title = getattr(parent_node, "title", "") if parent_node else ""
        
        children = [
            n for n in nodes 
            if (getattr(n, "parent_id", "") == node_id or (parent_title and getattr(n, "parent_id", "") == parent_title))
            and getattr(n, "status", "active") == "active"
        ]
        children.sort(key=lambda x: getattr(x, "sort_order", 1))
        
        return [KnowledgeTreeService._format_node(c) for c in children]

    @staticmethod
    def getBreadcrumbs(node_id: str) -> List[Dict[str, str]]:
        breadcrumbs = []
        current_id = node_id
        nodes = knowledge_node_repo.get_all(limit=1000)
        
        # Traverse up to 10 levels to prevent infinite loops
        for _ in range(10):
            if not current_id:
                break
            
            # Find node by ID or Title (since parent_id could be a title)
            node = next((n for n in nodes if getattr(n, "id", "") == current_id or getattr(n, "title", "") == current_id), None)
            
            if not node:
                break
            # Insert at beginning to build root->child order
            breadcrumbs.insert(0, {"id": getattr(node, "id", ""), "title": getattr(node, "title", "")})
            current_id = getattr(node, "parent_id", None)
            
        return breadcrumbs

    @staticmethod
    def findById(node_id: str) -> Optional[Dict[str, Any]]:
        node = knowledge_node_repo.get_by_id(node_id)
        if not node or getattr(node, "status", "active") != "active":
            return None
        children = KnowledgeTreeService.getChildren(node_id)
        result = KnowledgeTreeService._format_node(node, children)
        result["breadcrumbs"] = KnowledgeTreeService.getBreadcrumbs(node_id)
        return result

    @staticmethod
    def getNode(node_id: str) -> Optional[Dict[str, Any]]:
        return KnowledgeTreeService.findById(node_id)

    @staticmethod
    def findByAlias(query: str) -> Optional[Dict[str, Any]]:
        is_match, matched_title, conf, node_data = detect_knowledge_node(query)
        if is_match and node_data:
            node_id = getattr(node_data, "id", "")
            children = KnowledgeTreeService.getChildren(node_id)
            result = KnowledgeTreeService._format_node(node_data, children)
            result["breadcrumbs"] = KnowledgeTreeService.getBreadcrumbs(node_id)
            return result
        return None

    @staticmethod
    def findRoot() -> List[Dict[str, Any]]:
        nodes = knowledge_node_repo.get_all(limit=1000)
        roots = [
            n for n in nodes 
            if not getattr(n, "parent_id", None) and getattr(n, "status", "active") == "active"
        ]
        roots.sort(key=lambda x: getattr(x, "sort_order", 1))
        return [KnowledgeTreeService._format_node(r) for r in roots]

    @staticmethod
    def search(query: str) -> Optional[Dict[str, Any]]:
        return KnowledgeTreeService.findByAlias(query)


from typing import List, Dict, Optional, Any
from core.database import knowledge_node_repo
from chatbot.detector import detect_knowledge_node

class KnowledgeTreeService:
    @staticmethod
    def _format_node(node: Any, children: List[Any] = None) -> Dict[str, Any]:
        if not node:
            return None
        return {
            "id": getattr(node, "id", ""),
            "title": getattr(node, "title", ""),
            "description": getattr(node, "description", ""),
            "markdown": getattr(node, "response_markdown", ""),
            "parentId": getattr(node, "parent_id", None),
            "aliases": getattr(node, "aliases", []),
            "status": getattr(node, "status", "active"),
            "children": children or []
        }

    @staticmethod
    def getChildren(node_id: str) -> List[Dict[str, Any]]:
        nodes = knowledge_node_repo.get_all(limit=1000)
        parent_node = next((n for n in nodes if getattr(n, "id", "") == node_id), None)
        parent_title = getattr(parent_node, "title", "") if parent_node else ""
        
        children = [
            n for n in nodes 
            if (getattr(n, "parent_id", "") == node_id or (parent_title and getattr(n, "parent_id", "") == parent_title))
            and getattr(n, "status", "active") == "active"
        ]
        children.sort(key=lambda x: getattr(x, "sort_order", 1))
        
        return [KnowledgeTreeService._format_node(c) for c in children]

    @staticmethod
    def getBreadcrumbs(node_id: str) -> List[Dict[str, str]]:
        breadcrumbs = []
        current_id = node_id
        nodes = knowledge_node_repo.get_all(limit=1000)
        
        # Traverse up to 10 levels to prevent infinite loops
        for _ in range(10):
            if not current_id:
                break
            
            # Find node by ID or Title (since parent_id could be a title)
            node = next((n for n in nodes if getattr(n, "id", "") == current_id or getattr(n, "title", "") == current_id), None)
            
            if not node:
                break
            # Insert at beginning to build root->child order
            breadcrumbs.insert(0, {"id": getattr(node, "id", ""), "title": getattr(node, "title", "")})
            current_id = getattr(node, "parent_id", None)
            
        return breadcrumbs

    @staticmethod
    def findById(node_id: str) -> Optional[Dict[str, Any]]:
        node = knowledge_node_repo.get_by_id(node_id)
        if not node or getattr(node, "status", "active") != "active":
            return None
        children = KnowledgeTreeService.getChildren(node_id)
        result = KnowledgeTreeService._format_node(node, children)
        result["breadcrumbs"] = KnowledgeTreeService.getBreadcrumbs(node_id)
        return result

    @staticmethod
    def getNode(node_id: str) -> Optional[Dict[str, Any]]:
        return KnowledgeTreeService.findById(node_id)

    @staticmethod
    def findByAlias(query: str) -> Optional[Dict[str, Any]]:
        is_match, matched_title, conf, node_data = detect_knowledge_node(query)
        if is_match and node_data:
            node_id = getattr(node_data, "id", "")
            children = KnowledgeTreeService.getChildren(node_id)
            result = KnowledgeTreeService._format_node(node_data, children)
            result["breadcrumbs"] = KnowledgeTreeService.getBreadcrumbs(node_id)
            return result
        return None

    @staticmethod
    def findRoot() -> List[Dict[str, Any]]:
        nodes = knowledge_node_repo.get_all(limit=1000)
        roots = [
            n for n in nodes 
            if not getattr(n, "parent_id", None) and getattr(n, "status", "active") == "active"
        ]
        roots.sort(key=lambda x: getattr(x, "sort_order", 1))
        return [KnowledgeTreeService._format_node(r) for r in roots]

    @staticmethod
    def search(query: str) -> Optional[Dict[str, Any]]:
        return KnowledgeTreeService.findByAlias(query)


