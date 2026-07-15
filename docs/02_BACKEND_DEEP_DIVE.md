# 02. Backend Deep Dive

This document breaks down every single folder and critical file in the `backend/` directory of the Chatbot project. It is designed to help new developers understand exactly where business logic lives and how the Python backend operates.

---

## Folder Tree Overview

```text
backend/
├── api/             # REST Endpoints
├── core/            # Configuration and System Setup
├── models/          # Data Models (Cache, DB schemas)
├── pipeline/        # The Pipeline Engine
├── repositories/    # Database Access Layer
├── schemas/         # Pydantic Validation Schemas
├── services/        # Heavy Business Logic (RAG, Chunking)
├── steps/           # Individual Pipeline Steps
├── uploads/         # Temporary Document Storage
└── utils/           # Helper Utilities
```

---

## 1. `backend/api/`
**Purpose**: Contains the FastAPI REST router definitions. These files are the entry points for all HTTP requests from the frontend.
**Responsibility**: Receive requests, validate input via Pydantic schemas, call the appropriate Services or Pipeline, and return JSON responses.
**Dependencies**: Depends on `schemas`, `services`, and `pipeline`.

### Key Files:
- `routes/chat.py`
  - **Purpose**: Handles the main chat interface.
  - **Flow**: Receives a message → Creates a `PipelineContext` → Passes it to `PipelineRunner` → Returns the execution trace and final response.
- `routes/knowledge.py`
  - **Purpose**: Handles document uploads, deletion, and settings for the Knowledge Base.
  - **Flow**: Receives PDF → Triggers `process_document_bg` in a background task → Responds with success immediately. Also contains the `/embeddings` route for the Admin UI.
- `routes/admin.py`, `routes/dashboard.py`, `routes/health.py`, `routes/session.py`
  - **Purpose**: Handle various administrative panels, analytics generation, server health checks, and session clearing.

---

## 2. `backend/core/`
**Purpose**: Centralized configuration and system initialization.
**Responsibility**: Loads `.env` variables, configures loggers, sets up database URLs, and defines the global `PIPELINE_STEPS` order.

### Key Files:
- `config.py`
  - **Purpose**: Uses `dotenv` to load environment variables. Defines `QDRANT_URL`, `EMBEDDING_MODEL`, and the exact order of execution for the `PIPELINE_STEPS`.
- `logger.py`
  - **Purpose**: Configures standard Python logging to output clean, formatted console logs for debugging.
- `circuit_breaker.py`
  - **Purpose**: A safety mechanism. If Gemini fails 5 times in a row, the circuit breaker "trips" and stops sending requests for a few minutes to prevent API rate limiting or massive bills.

---

## 3. `backend/pipeline/`
**Purpose**: The core engine that powers the chatbot's decision-making process.
**Responsibility**: Execute a predefined list of steps sequentially.

### Key Files:
- `pipeline_context.py`
  - **Purpose**: A data container holding the original message, normalized message, metadata, and final response. It is passed from step to step.
- `pipeline_result.py`
  - **Purpose**: A simple class returned by every step. Contains `continue_pipeline` (boolean). If False, the pipeline halts immediately.
- `pipeline_runner.py`
  - **Purpose**: Iterates through `PIPELINE_STEPS` (defined in `config.py`).
  - **Pseudo Code**:
    ```python
    for step in PIPELINE_STEPS:
        result = step.process(context)
        if result.stop:
            return context.response
    ```

---

## 4. `backend/steps/`
**Purpose**: Contains the individual conversational logic blocks.
**Responsibility**: Perform one specific task (e.g., check for gibberish, search the DB) and decide whether to stop or continue the pipeline.

### Key Files & Explanations:

#### `normalize_step.py`
- **Purpose**: Cleans up user typos before they hit the LLM.
- **Logic**: Uses regex to convert slang ("hiii", "gm") into standard English ("hello", "good morning").

#### `conversation_intelligence_step.py`
- **Purpose**: Handles identity and memory.
- **Logic**: If the user says "Call yourself Sara" or "My name is John", this step intercepts it using Regex, updates the `LocalStorage` memory payload, and stops the pipeline instantly (bypassing the slow LLM).

#### `conversation_opener_step.py`
- **Purpose**: Handles standard greetings.
- **Logic**: If the normalized text is exactly "hello" or "hi", it returns a hardcoded friendly greeting and stops.

#### `fastpath_router_step.py`
- **Purpose**: Instant answers for known corporate queries.
- **Logic**: Checks the message against a dictionary of keywords (e.g., "CEO", "Contact"). If matched, returns the exact corporate answer.

#### `faq_step.py`
- **Purpose**: Handles frequently asked questions.
- **Logic**: Similar to FastPath, but intended for user-defined FAQs loaded from the database.

#### `gibberish_step.py`
- **Purpose**: Prevents the bot from wasting LLM tokens on random keyboard smashes.
- **Logic**: Uses a heuristic algorithm (checking vowel/consonant ratios) to detect strings like "asdfghjkl". If detected, returns "Please type a clear question."

#### `knowledge_search_step.py`
- **Purpose**: The "R" in RAG (Retrieval).
- **Logic**: Takes the user's query → Generates a 384D embedding → Queries Qdrant for the top 3 similar document chunks → Attaches those chunks to the `PipelineContext` metadata.

#### `response_formatter_step.py`
- **Purpose**: A local fallback for summarization.
- **Logic**: If the LLM is unavailable, this step uses extractive summarization to pick the top 5 sentences containing the user's keywords and returns them.

#### `llm_step.py`
- **Purpose**: The "G" in RAG (Generation).
- **Logic**: Takes the retrieved chunks from `knowledge_search_step` and sends them to Google Gemini along with a strict prompt: "Answer the user's question using ONLY the provided context."

---

## 5. `backend/services/`
**Purpose**: Heavy data processing and external system interaction.

### Key Files:
- `knowledge/extraction_engine.py`
  - **Purpose**: Reads PDF or TXT files and converts them into raw strings.
- `knowledge/chunking_engine.py`
  - **Purpose**: Splits massive strings into smaller chunks (e.g., 1000 characters) while preserving sentence boundaries and adding overlap.
- `rag/embeddings.py`
  - **Purpose**: A Singleton wrapper around `SentenceTransformer`. Generates vectors.
- `rag/vector_store/qdrant_store.py`
  - **Purpose**: Connects to the Qdrant database. Contains methods for `upsert`, `search`, and `get_document_embeddings`.

---

## 6. `backend/repositories/`
**Purpose**: Abstraction layer for data storage.
**Responsibility**: Implements CRUD (Create, Read, Update, Delete) operations. The rest of the app calls `repo.get_all()` without knowing if the underlying storage is SQLite, PostgreSQL, or JSON.

### Key Files:
- `base_repository.py`: Defines the interface and standard methods.
- `registry.py`: Instantiates the repositories (e.g., `document_repo`, `chunk_repo`) so they can be imported globally.

---

## 7. `backend/schemas/`
**Purpose**: Pydantic models for data validation.
**Responsibility**: Ensure that incoming API requests and outgoing JSON responses match the exact expected format. If a frontend sends a string instead of an integer, Pydantic throws a clean error automatically.

---

## Interview Questions & Best Answers

**Q: Explain the Dependency Flow in the backend.**
> **A:** "The flow goes exactly one way: API Routes call Services and the Pipeline. The Pipeline calls Steps. Steps call Services and Repositories. Services call external APIs (like Gemini or Qdrant). A Repository never calls a Service, and a Step never calls a Route. This unidirectional flow ensures there are no circular dependency errors and makes unit testing incredibly easy."

**Q: How does the backend prevent massive cloud bills if a user spams the system?**
> **A:** "We have multiple layers of defense. First, the `gibberish_step` filters out keyboard smashes locally. Second, the `fastpath` and `faq` steps intercept common queries instantly without calling the LLM. Finally, if the LLM does get called, we have a `circuit_breaker` that stops further requests if the API starts failing or rate-limiting us."

**Q: Why use the Repository Pattern?**
> **A:** "It decouples our business logic from our database framework. Right now, we might be using a simple local storage or tiny database. If we scale to millions of users and need to migrate to PostgreSQL, we don't have to rewrite the `api/` or `steps/` folders. We only rewrite the files inside the `repositories/` folder."
