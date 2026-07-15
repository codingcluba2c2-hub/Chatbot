# Complete Migration from Qdrant to pgvector

## Overview
The architecture has been fully simplified by migrating all RAG vector operations from the cloud-based Qdrant vector database into the native Neon PostgreSQL database using the `pgvector` extension. The application now uses only one database for both structured data and vector embeddings, dramatically simplifying deployment and maintenance.

## Architecture Change

**Old Architecture:**
```
PDF -> Chunking -> Embedding -> Qdrant (Cloud) -> Retriever -> Gemini
```

**New Architecture:**
```
PDF -> Chunking -> Embedding -> PostgreSQL pgvector (Local/Neon) -> Retriever -> Gemini
```

## Schema Updates
The `document_chunks` table has been updated to include vectors natively.

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_chunks (
    id VARCHAR PRIMARY KEY,
    document_id VARCHAR,
    chunk_number INTEGER,
    title VARCHAR,
    content VARCHAR,
    embedding VECTOR(384),
    metadata JSONB,
    token_count INTEGER,
    created_at FLOAT,
    updated_at FLOAT
);
```
*Note: The dimension size is fixed at `384` to match the `all-MiniLM-L6-v2` embedding model.*

## Modified & Removed Files
- **Removed**: `backend/services/rag/vector_store/qdrant_store.py`
- **Removed**: `qdrant-client` dependency from `requirements.txt`.
- **Created**: `backend/services/rag/vector_store/pgvector_store.py` (New `PgVectorProvider`)
- **Updated**: `backend/core/database.py` (Added pgvector extension initialization)
- **Updated**: `backend/models/knowledge.py` (Added `Vector` column)
- **Updated**: `backend/core/config.py` & `.env` (Removed QDRANT variables, set default to `pgvector`)
- **Updated**: `backend/services/rag/vector_store/__init__.py` (Replaced initialization logic)
- **Updated**: `backend/api/routes/dashboard.py` (Replaced Qdrant health checks)
- **Updated**: `backend/api/routes/knowledge.py` (Added `/chunks/{chunk_id}/embedding` debugging endpoint)
- **Updated**: `frontend/src/components/admin/knowledge/KnowledgeBaseModule.tsx` (Added "View Embedding" modal for debugging)

## Retrieval Flow
The pgvector search utilizes optimized SQL cosine distance searching:
```sql
ORDER BY embedding <=> query_embedding LIMIT 5
```
This is fully encapsulated inside the `PgVectorProvider.search()` method using SQLAlchemy models.

## Performance Improvements
By utilizing `pgvector`, we eliminated network hops between the backend and Qdrant. The chunks and vectors are retrieved simultaneously in the same query. Future optimizations can easily be applied by adding an HNSW index on the `embedding` column directly in PostgreSQL.

## Migration Summary
No legacy Qdrant code remains in the project. The codebase compiles without warnings, and the entire ingestion and retrieval pipeline operates securely and efficiently on a single PostgreSQL connection.
