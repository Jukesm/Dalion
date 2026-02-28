from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
import os
from config import DATABASE_URL

# Configuração de Pool Robusta (Escalabilidade)
# QueuePool é o padrão para Postgres. 
# Pre-ping resolve "connection closed" silenciosamente.
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Ativa WAL Mode no SQLite (Melhora concorrência significativamente)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)

import time
import random

def increment_with_lock(session, model, obj_id, field_name):
    """Implementa lock otimista com retry e backoff exponencial."""
    max_retries = 5
    for attempt in range(max_retries):
        obj = session.query(model).filter(model.id == obj_id).first()
        if not obj:
            return False
        
        current_version = getattr(obj, 'version', 0)
        current_val = getattr(obj, field_name, 0)
        
        # Tentativa de update atômico com verificação de versão
        result = session.query(model).filter(
            model.id == obj_id,
            model.version == current_version
        ).update({
            field_name: current_val + 1,
            'version': current_version + 1
        })
        
        if result > 0:
            session.commit()
            return True
            
        # Conflito detectado: Wait & Retry
        wait_time = (0.05 * (2 ** attempt)) + (random.random() * 0.01)
        time.sleep(wait_time)
        session.rollback()
        
    return False
