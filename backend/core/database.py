from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from core.config import POSTGRES_URL

engine = create_engine(POSTGRES_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auto-migrate columns and tables if missing
from sqlalchemy import text
from models.knowledge import Base
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE knowledge_documents ADD COLUMN processing_stats JSON DEFAULT '{}'::json;"))
        conn.commit()
except Exception:
    pass

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE knowledge_documents ADD COLUMN file_hash VARCHAR;"))
        conn.commit()
except Exception:
    pass

try:
    Base.metadata.create_all(bind=engine)
except Exception:
    pass
