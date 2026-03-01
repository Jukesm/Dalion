import os
from sqlalchemy import create_engine, text
from config import DATABASE_URL
from models import Base
from database import engine

def migrate_v4():
    print(f"🚀 Iniciando Migração em: {DATABASE_URL}")
    
    # 1. Garante que as tabelas básicas existem
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Estrutura básica do banco garantida.")
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")

    # 2. Comandos para adicionar colunas individualmente (para upgrades de versão)
    commands = [
        ("users", "is_admin", "BOOLEAN DEFAULT FALSE"),
        ("users", "is_active", "BOOLEAN DEFAULT TRUE"),
        ("users", "last_run_at", "TEXT"),
        ("users", "created_at", "FLOAT"),
        ("ideas", "views", "INTEGER DEFAULT 0"),
        ("ideas", "clicks", "INTEGER DEFAULT 0"),
        ("ideas", "conversions", "INTEGER DEFAULT 0"),
        ("ideas", "version", "INTEGER DEFAULT 1"),
        ("ideas", "created_at", "FLOAT")
    ]
    
    for table, col, col_type in commands:
        # Usamos uma transação isolada por coluna para evitar abortar o bloco todo
        try:
            with engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                conn.commit()
                print(f"➕ Coluna adicionada: {table}.{col}")
        except Exception as e:
            # Silencia apenas erros de duplicata
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                pass 
            else:
                print(f"⚠️ Aviso em {table}.{col}: {e}")

    print("🏁 Migração Scale 4.0 concluída.")

if __name__ == "__main__":
    migrate_v4()
