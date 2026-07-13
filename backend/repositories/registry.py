# backend/repositories/registry.py
from repositories.base_repository import BaseRepository
from repositories.memory_repository import ConversationRepository, MessageRepository, FactRepository
from schemas.admin import (
    Greeting, Farewell, FAQ, FastPath, AuditLog
)
from schemas.knowledge import KnowledgeDocument, DocumentChunk, KnowledgeSettings

from models.admin import (
    GreetingDB, FarewellDB, FAQDB, FastPathDB, AuditLogDB
)
from models.knowledge import KnowledgeDocumentDB, DocumentChunkDB, KnowledgeSettingsDB
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

# Global singletons
audit_repo = AuditLogRepository(AuditLog, AuditLogDB)
greeting_repo = GreetingRepository(Greeting, GreetingDB)
farewell_repo = FarewellRepository(Farewell, FarewellDB)
faq_repo = FAQRepository(FAQ, FAQDB)
fastpath_repo = FastPathRepository(FastPath, FastPathDB)
document_repo = DocumentRepository(KnowledgeDocument, KnowledgeDocumentDB)
chunk_repo = ChunkRepository(DocumentChunk, DocumentChunkDB)
settings_repo = KnowledgeSettingsRepository(KnowledgeSettings, KnowledgeSettingsDB)

conversation_repo = ConversationRepository()
message_repo = MessageRepository()
fact_repo = FactRepository()

# Function to record audit logs
def log_audit(action: str, entity_type: str, entity_id: str, old_value=None, new_value=None, user: str = "system"):
    audit_repo.create(AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        user=user
    ))
