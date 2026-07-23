# Enterprise RAG Chatbot

An enterprise-grade, production-ready Retrieval-Augmented Generation (RAG) chatbot and knowledge management system. Built with a modern tech stack to ensure high performance, persistent conversation memory, and scalable semantic search capabilities.

## Tech Stack

- **Frontend:** Next.js (React), Tailwind CSS, Lucide Icons
- **Backend:** Python, FastAPI, SQLAlchemy
- **Vector Database:** Qdrant Cloud (for scalable vector storage and search)
- **Relational Database:** PostgreSQL via Neon (for persistent conversational memory, user sessions, and metadata)
- **Embeddings:** Local embedding generation using `sentence-transformers/all-MiniLM-L6-v2`
- **LLM Provider:** Google Gemini API

## Key Features

- **Knowledge Base Management:** Upload PDF documents through an intuitive admin panel. Documents are automatically parsed, chunked, embedded, and stored in the vector database.
- **Dynamic Chunking Engine:** Configure chunk sizes, overlap parameters, and semantic search thresholds directly from the UI.
- **Persistent Conversational Memory:** Uses PostgreSQL to reliably remember conversational history, user preferences, and context facts across sessions.
- **Developer Preview & Trace Mode:** Built-in debugging tools that visualize intent matching, retrieval scores, and step-by-step pipeline execution times.
- **Server-Driven UI:** Capable of rendering dynamic components directly inside the chat interface (e.g., carousels, tables, quick replies).

## Prerequisites

- Node.js (v18+ recommended)
- Python (v3.10+ recommended)
- A Qdrant Cloud account (or local Qdrant instance)
- A Neon PostgreSQL database (or local PostgreSQL instance)
- A Google Gemini API Key

## Getting Started

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the `backend` directory based on your database and API credentials:
   ```env
   # Example .env configuration
   POSTGRES_URL=postgresql://user:password@hostname/dbname?sslmode=require
   GeminiApi=your_gemini_api_key_here
   
   QDRANT_URL=https://your-qdrant-cluster.cloud.qdrant.io:6333
   QDRANT_API_KEY=your_qdrant_api_key_here
   VECTOR_PROVIDER=qdrant
   VECTOR_COLLECTION=knowledge_base
   EMBEDDING_MODEL=all-MiniLM-L6-v2
   ```
4. Start the FastAPI backend server:
   ```bash
   python app.py
   ```
   *The backend will automatically initialize the database schema and create the necessary Qdrant collections on startup.*

### 2. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install the Node dependencies:
   ```bash
   npm install
   ```
3. Create a `.env.local` file in the `frontend` directory:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
4. Start the Next.js development server:
   ```bash
   npm run dev
   ```

### 3. Usage

- Open your browser and navigate to `http://localhost:3000` to interact with the Chatbot.
- Access the Admin Dashboard at `http://localhost:3000/admin` to upload documents, tune chunking settings, and manage knowledge bases.

## Running on Local Network

To access the Chatbot from another device on the same Wi-Fi:

### 1. Find Local IP
Run the following command in your terminal to find your Local IPv4 Address:
```bash
ipconfig
```
*(The backend will also automatically detect and print this on startup!)*

### 2. Start Services
Make sure your `.env` files are correctly configured with your Local IP (e.g., `192.168.1.xxx`).
- **Start Backend:** `python app.py`
- **Start Frontend:** `npm run dev`

### 3. Open Browser
On your phone or another PC, navigate to:
`http://192.168.1.xxx:3000`

### Troubleshooting
- **Firewall:** Windows Defender Firewall might block incoming connections to ports 3000, 8001, and 8002. Allow TCP traffic for these ports.
- **Antivirus:** Ensure third-party antivirus software isn't blocking LAN traffic.
- **Same Wi-Fi:** Make sure both devices are on the exact same Wi-Fi network and that the network profile is set to Private (not Public).
- **VPN:** Ensure your VPN is disabled, as it might isolate your device from the local network.
