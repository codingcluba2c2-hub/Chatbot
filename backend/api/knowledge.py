from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from typing import List
from core.database import document_repo, chunk_repo, SessionLocal
from core.models import DocumentChunkDB, KnowledgeDocumentDB

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge Base"])

@router.get("/documents")
def get_documents():
    docs = document_repo.get_all(limit=1000)
    return [d.model_dump() for d in docs]

@router.get("/documents/{doc_id}")
def get_document(doc_id: str):
    doc = document_repo.get_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc.model_dump()

@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    if document_repo.delete(doc_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Document not found")

@router.post("/upload")
async def upload_document(file: UploadFile = File(...), category: str = Form("general"), language: str = Form("en")):
    # Stub for document upload. Actual extraction and processing would run as a background task.
    return {"status": "processing"}

@router.post("/documents/{doc_id}/reprocess")
def reprocess_document(doc_id: str):
    # Stub for document reprocessing.
    return {"status": "processing"}

@router.get("/documents/{doc_id}/chunks")
def get_document_chunks(doc_id: str):
    with SessionLocal() as db:
        chunks = db.query(DocumentChunkDB).filter(DocumentChunkDB.document_id == doc_id).order_by(DocumentChunkDB.created_at.asc()).all()
        result = []
        for c in chunks:
            result.append({
                "id": c.id,
                "document_id": c.document_id,
                "content": c.content,
                "metadata": c.metadata_col,
                "created_at": c.created_at
            })
        return result

@router.get("/documents/{doc_id}/embeddings")
def get_document_embeddings(doc_id: str):
    with SessionLocal() as db:
        chunks = db.query(DocumentChunkDB).filter(DocumentChunkDB.document_id == doc_id).order_by(DocumentChunkDB.chunk_number.asc()).all()
        
        embeddings_list = []
        for c in chunks:
            vector = c.embedding
            if vector is None:
                vector = []
            elif hasattr(vector, "tolist"):
                vector = vector.tolist()
            elif isinstance(vector, str):
                import json
                try:
                    vector = json.loads(vector)
                except:
                    vector = []
                    
            embeddings_list.append({
                "chunk_id": c.id,
                "chunk_number": c.chunk_number,
                "vector": vector,
                "vector_dimension": len(vector) if vector else 0,
                "content": c.content
            })
            
        return {
            "embedding_model": "all-MiniLM-L6-v2",
            "dimension": 384,
            "distance": "cosine",
            "collection": "knowledge_documents",
            "total_chunks": len(embeddings_list),
            "embeddings": embeddings_list
        }

@router.get("/documents/{doc_id}/retrieve")
def test_retrieval(doc_id: str, q: str = ""):
    # Stub for testing retrieval.
    return {"results": []}

@router.get("/chunks/{chunk_id}/embedding")
def get_chunk_embedding(chunk_id: str):
    # Stub for viewing chunk embedding details.
    with SessionLocal() as db:
        chunk = db.query(DocumentChunkDB).filter(DocumentChunkDB.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")
        return {
            "chunk_id": chunk.id,
            "content": chunk.content,
            "metadata": chunk.metadata_col,
            "vector_dimension": 0,
            "vector": []
        }
