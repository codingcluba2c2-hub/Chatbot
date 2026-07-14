import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

DEVELOPER_MODE = os.getenv("DEVELOPER_MODE", "false").lower() == "true"
POSTGRES_URL = os.getenv("POSTGRES_URL", "sqlite:///./app.db")

# RAG Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
VECTOR_PROVIDER = os.getenv("VECTOR_PROVIDER", "qdrant")
VECTOR_COLLECTION = os.getenv("VECTOR_COLLECTION", "knowledge_base")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Order of pipeline steps to execute
PIPELINE_STEPS: List[str] = [
    "Normalize",
    "SpellCorrection",
    "ConversationOpener",
    "AssistantPreference",
    "SessionMemory",
    "FastPathRouter",
    "FAQ",
    "MeaningfulValidator",
    "KnowledgeSearch",
    "ResponseFormatter",
    "LLM",
    "Fallback",
    "Gibberish"
]
