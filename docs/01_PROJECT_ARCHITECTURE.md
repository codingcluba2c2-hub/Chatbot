# 01. Project Architecture & Overview

## 1. Project Overview

### Purpose
The Mobiloitte AI Assistant is an enterprise-grade Conversational AI chatbot. It is designed to act as an intelligent virtual assistant capable of answering questions, performing basic identity and session management, and retrieving enterprise knowledge using a Retrieval-Augmented Generation (RAG) pipeline.

### Business Problem
In an enterprise setting, employees and customers often struggle to find accurate, up-to-date information scattered across various documents, policies, and manuals. Traditional search engines return links, not answers. This project solves that by ingesting company documents, breaking them down semantically, and using Large Language Models (LLMs) to synthesize direct, accurate answers based *only* on the ingested knowledge.

---

## 2. Architecture

The system utilizes a decoupled client-server architecture:
- **Client (Frontend)**: A responsive, modern web interface for users to chat with the bot, and an Admin portal to manage the Knowledge Base and system settings.
- **Server (Backend)**: A high-performance Python API that processes messages through a sequential Pipeline, interfaces with a Vector Database, and calls an external LLM for generation.

### Technology Stack

**Frontend Stack**
- **NextJS (React)**: The core framework for UI rendering and routing. Chosen for its performance, SEO capabilities, and robust ecosystem.
- **TypeScript**: Ensures type safety, reducing runtime errors and improving developer experience.
- **Tailwind CSS**: A utility-first CSS framework for rapid, responsive UI styling.
- **Lucide React**: Provides clean, modern vector icons.
- **Recharts**: A charting library used to visualize embeddings and system statistics in the Admin panel.
- **LocalStorage**: Used to persist user session data and developer settings locally without requiring a complex authentication system.

**Backend Stack**
- **Python 3.x**: The primary programming language, ideal for AI and data processing.
- **FastAPI**: A modern, fast web framework for building APIs. Chosen for its asynchronous support and automatic documentation (Swagger).
- **Uvicorn**: An ASGI web server implementation for FastAPI.
- **Pydantic**: Used for data validation and settings management using Python type annotations.
- **SQLAlchemy/SQLite** (or In-Memory Repositories): Used to store document metadata, chunks, and system configurations.

**AI Stack**
- **Embedding Model (`all-MiniLM-L6-v2`)**: A lightweight, highly efficient SentenceTransformer model that converts text chunks into 384-dimensional dense vectors.
- **Vector Database (Qdrant)**: A powerful vector search engine. It stores the 384D vectors and performs lightning-fast cosine similarity searches to find relevant information.
- **LLM (Google Gemini)**: The generative AI model used to synthesize the final answer using the context retrieved from Qdrant.

---

## 3. Folder Structure & Justification

```text
Chatbot/
├── backend/                  # The entire Python FastAPI backend
│   ├── api/                  # Contains all REST API route definitions (chat, knowledge, admin)
│   ├── core/                 # Application configuration, environment variables, and core logic
│   ├── models/               # Data structures (Cache, etc.)
│   ├── pipeline/             # The core Execution Pipeline engine that runs the sequence of steps
│   ├── repositories/         # Database abstraction layer (Repository Pattern)
│   ├── schemas/              # Pydantic models for API request/response validation
│   ├── services/             # Business logic (RAG, Chunking, Extraction, Embeddings)
│   ├── steps/                # Individual Pipeline Step implementations (Normalize, FAQ, LLM, etc.)
│   ├── uploads/              # Temporary storage for uploaded PDF/TXT documents
│   └── utils/                # Helper functions (Text normalization, sanitization)
│
├── frontend/                 # The NextJS React frontend
│   ├── public/               # Static assets (images, icons)
│   └── src/
│       ├── app/              # NextJS App Router (pages: /chat, /admin)
│       ├── components/       # Reusable React components (Chat UI, Admin panels)
│       └── lib/              # Frontend utilities and API clients
│
└── docs/                     # Project documentation
```

### Why each folder exists:
- `api/`: Keeps routing logic separate from business logic.
- `services/`: Houses complex logic like chunking text and interfacing with Qdrant, ensuring controllers (routes) remain thin.
- `steps/`: The heart of the application. By separating each conversational step into its own file, the system becomes highly modular and testable.
- `repositories/`: Abstracts the database layer. If we switch from SQLite to PostgreSQL, we only change the repository, not the business logic.

---

## 4. Request Lifecycle & Data Flow

### Browser Request Flow (Chat)

```text
Browser (User types "Hello")
       ↓ [POST /api/chat]
FastAPI (chat.py)
       ↓
PipelineRunner (Initializes Context)
       ↓
Step 1: NormalizeStep (Converts "Hellooo" -> "hello")
       ↓
Step 2: ConversationIntelligenceStep (Detects identity/memory queries)
       ↓
Step 3: ConversationOpenerStep (Detects greetings, returns "Hi there!")
       ↓ (Pipeline Stops early to save time!)
FastAPI returns JSON
       ↓
NextJS updates UI Chat Bubble
```

### Knowledge Base Ingestion Flow

```text
Admin Uploads Document (PDF)
       ↓ [POST /api/knowledge/upload]
FastAPI receives file in uploads/
       ↓
ExtractionEngine (Extracts raw text from PDF)
       ↓
ChunkingEngine (Splits text into 1000-character chunks with overlap)
       ↓
SentenceTransformer (Converts each chunk into a 384D Vector)
       ↓
Qdrant (Stores Vectors + Chunk Content)
       ↓
Status updated to "Published"
```

### Complete RAG Execution Flow (Querying Knowledge)

```text
User asks: "What is the leave policy?"
       ↓
Pipeline normalizes and corrects spelling.
       ↓
KnowledgeSearchStep generates a 384D Vector for the query.
       ↓
Qdrant performs Cosine Similarity search.
       ↓
Top 3 matching chunks are retrieved.
       ↓
LLMStep sends the chunks + user query to Google Gemini.
       ↓
Gemini synthesizes a formatted answer.
       ↓
Pipeline returns the final response to the user.
```

---

## 5. Architectural Design Patterns

### The Pipeline Pattern
The chatbot does not use a single massive `if/else` block. Instead, it uses the **Pipeline Pattern**. 
A request passes through a sequence of `PipelineStep` classes. Each step has a specific job. If a step successfully handles the request (e.g., the FAQ step finds a direct match), it can stop the pipeline early and return the response, saving execution time and API costs.

### The Repository Pattern
Data access is abstracted using Repositories (`document_repo`, `chunk_repo`). The application code never writes SQL or raw database commands directly. It calls `document_repo.get_by_id()`. This makes swapping databases seamless.

### The Singleton Pattern
Expensive resources, like the `SentenceTransformer` embedding model and the `QdrantClient`, are initialized as Singletons. They are loaded into memory once during application startup and reused for every request. This prevents the server from freezing while reloading massive AI models on every API call.

### Lazy Loading
In the frontend, certain heavy components (like the Recharts visualizers in the Embeddings tab) are lazy-loaded. They are only fetched from the server when the user actually clicks the tab. This keeps the initial page load blazing fast.

---

## 6. System Justifications (Why we use what we use)

- **Why Qdrant?**: It is an incredibly fast, open-source vector database built in Rust. It supports local file storage and Docker, making it perfect for both local development and enterprise deployment.
- **Why SentenceTransformer?**: Running embeddings locally (`all-MiniLM-L6-v2`) is free, private, and extremely fast compared to calling OpenAI's embedding API for every single document chunk.
- **Why Gemini?**: Google's Gemini provides state-of-the-art text synthesis with a generous free tier, making it ideal for the generative portion of RAG.
- **Why FastPath / FAQ?**: LLMs are slow and expensive. If a user asks "Who made you?" or "Reset my password", we don't need AI to answer that. FastPath and FAQ intercept these queries using Regex and return hardcoded answers instantly.
- **How Session Works**: The frontend generates a unique UUID for the session and stores it in LocalStorage. It sends this ID with every request. The backend uses this ID to maintain short-term conversation history (Memory), allowing the bot to remember context (e.g., "What was my previous question?").
- **How Developer Mode Works**: When enabled in the frontend, the backend attaches a detailed `trace` object to the JSON response. This trace contains the execution time (in milliseconds) of *every single pipeline step*, allowing engineers to see exactly where the bot spent its time and why it made its decisions.

---

## 7. Interview Questions & Best Answers

**Q: Why did you choose a Pipeline architecture over standard controller logic?**
> **A:** "A Conversational AI needs to handle greetings, spelling errors, FAQs, RAG, and general LLM chat. If we put all that in one controller, it becomes a massive, unmaintainable 'spaghetti' of if/else statements. The Pipeline pattern allows us to decouple each feature into its own isolated Step. We can add, remove, or reorder steps without breaking the rest of the application. It also allows us to implement 'early exits' to save LLM costs."

**Q: How does your application handle vector database costs and latency?**
> **A:** "We run the `all-MiniLM-L6-v2` embedding model locally within the Python process using SentenceTransformers. This means generating embeddings costs $0 and has virtually zero network latency. We store these locally in Qdrant. The only network call we make is the final generation step to Gemini, which significantly reduces our overall cloud footprint."

**Q: Explain how your Knowledge Base ingestion works.**
> **A:** "When a document is uploaded, it runs in a FastAPI Background Task so the UI doesn't freeze. The `ExtractionEngine` pulls the raw text. The `ChunkingEngine` splits it into smaller pieces (e.g., 1000 characters with 100 character overlap to maintain context). The embedding model converts each chunk into a 384-dimensional vector, which is then upserted into Qdrant. The document status is then updated to 'published' so the frontend knows it's ready."
