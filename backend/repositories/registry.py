# backend/repositories/registry.py
from repositories.base_repository import BaseRepository
from repositories.memory_repository import ConversationRepository, MessageRepository, FactRepository
from schemas.admin import (
    Greeting, Farewell, FAQ, FastPath, AuditLog
)
from schemas.knowledge import KnowledgeDocument, DocumentChunk, KnowledgeSettings, KnowledgeNode

from models.admin import (
    GreetingDB, FarewellDB, FAQDB, FastPathDB, AuditLogDB
)
from models.knowledge import KnowledgeDocumentDB, DocumentChunkDB, KnowledgeSettingsDB, KnowledgeNodeDB
from models.memory import ConversationDB, MessageDB, MemoryFactDB

class AuditLogRepository(BaseRepository[AuditLog, AuditLogDB]):
    pass

class GreetingRepository(BaseRepository[Greeting, GreetingDB]):
    pass

class FarewellRepository(BaseRepository[Farewell, FarewellDB]):
    pass

class FAQRepository(BaseRepository[FAQ, FAQDB]):
    pass

class FastPathRepository(BaseRepository[FastPath, FastPathDB]):
    pass

class DocumentRepository(BaseRepository[KnowledgeDocument, KnowledgeDocumentDB]):
    pass

class ChunkRepository(BaseRepository[DocumentChunk, DocumentChunkDB]):
    pass

class KnowledgeSettingsRepository(BaseRepository[KnowledgeSettings, KnowledgeSettingsDB]):
    pass

class KnowledgeNodeRepository(BaseRepository[KnowledgeNode, KnowledgeNodeDB]):
    pass

_instances = {}

def _get_repo(name: str):
    if name not in _instances:
        if name == "audit_repo":
            _instances[name] = AuditLogRepository(AuditLog, AuditLogDB)
        elif name == "greeting_repo":
            _instances[name] = GreetingRepository(Greeting, GreetingDB)
        elif name == "farewell_repo":
            _instances[name] = FarewellRepository(Farewell, FarewellDB)
        elif name == "faq_repo":
            _instances[name] = FAQRepository(FAQ, FAQDB)
        elif name == "fastpath_repo":
            _instances[name] = FastPathRepository(FastPath, FastPathDB)
        elif name == "document_repo":
            _instances[name] = DocumentRepository(KnowledgeDocument, KnowledgeDocumentDB)
        elif name == "chunk_repo":
            _instances[name] = ChunkRepository(DocumentChunk, DocumentChunkDB)
        elif name == "settings_repo":
            _instances[name] = KnowledgeSettingsRepository(KnowledgeSettings, KnowledgeSettingsDB)
        elif name == "conversation_repo":
            _instances[name] = ConversationRepository()
        elif name == "message_repo":
            _instances[name] = MessageRepository()
        elif name == "fact_repo":
            _instances[name] = FactRepository()
        elif name == "knowledge_node_repo":
            _instances[name] = KnowledgeNodeRepository(KnowledgeNode, KnowledgeNodeDB)
        else:
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return _instances[name]

def __getattr__(name):
    if name in ["audit_repo", "greeting_repo", "farewell_repo", "faq_repo", 
                "fastpath_repo", "document_repo", "chunk_repo", "settings_repo", 
                "conversation_repo", "message_repo", "fact_repo", "knowledge_node_repo"]:
        return _get_repo(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Function to record audit logs
def log_audit(action: str, entity_type: str, entity_id: str, old_value=None, new_value=None, user: str = "system"):
    _get_repo("audit_repo").create(AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        user=user
    ))
