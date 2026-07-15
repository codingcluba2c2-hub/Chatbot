from core.database import engine
from sqlalchemy import text

def migrate():
    with engine.begin() as conn:
        print("Adding chunk_number...")
        conn.execute(text("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS chunk_number INTEGER DEFAULT 0"))
        
        print("Adding title...")
        conn.execute(text("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS title VARCHAR"))
        
        print("Adding embedding...")
        conn.execute(text("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS embedding vector(384)"))
        
        print("Adding token_count...")
        conn.execute(text("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS token_count INTEGER DEFAULT 0"))
        
        print("Adding updated_at...")
        conn.execute(text("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS updated_at FLOAT"))
        
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
