import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

DEVELOPER_MODE = os.getenv("DEVELOPER_MODE", "false").lower() == "true"
POSTGRES_URL = os.getenv("POSTGRES_URL", "sqlite:///./app.db")

# RAG Configuration
VECTOR_PROVIDER = os.getenv("VECTOR_PROVIDER", "pgvector")
VECTOR_COLLECTION = os.getenv("VECTOR_COLLECTION", "knowledge_base")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
USE_LLM_FOR_RAG = os.getenv("USE_LLM_FOR_RAG", "true").lower() == "true"

# Order of pipeline steps to execute
PIPELINE_STEPS: List[str] = [
    "Normalize",
    "ResponseCacheStep",
    "SpellCorrection",
    "Greeting",
    "FollowUpResolver",
    "ConversationContextResolver",
    "FAQ",
    "MeaningfulValidator",
    "Gibberish",
    "AbuseDetection",
    "Memory",
    "KnowledgeSearch",
    "ResponseGenerator"
]
