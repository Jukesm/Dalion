import os
from sqlalchemy import create_engine, text
from config import DATABASE_URL

def migrate_v4():
    print(f"Iniciando Migração em: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    
    # Comandos de alteração (Sintaxe compatível com PG e SQLite)
    commands = [
        # Users
        "ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE",
        "ALTER TABLE users ADD COLUMN last_run_at TEXT",
        "ALTER TABLE users ADD COLUMN created_at FLOAT",
        # Ideas
        "ALTER TABLE ideas ADD COLUMN views INTEGER DEFAULT 0",
        "ALTER TABLE ideas ADD COLUMN clicks INTEGER DEFAULT 0",
        "ALTER TABLE ideas ADD COLUMN conversions INTEGER DEFAULT 0",
        "ALTER TABLE ideas ADD COLUMN version INTEGER DEFAULT 1",
        "ALTER TABLE ideas ADD COLUMN created_at FLOAT"
    ]
    
    with engine.connect() as conn:
        for cmd in commands:
            try:
                conn.execute(text(cmd))
                conn.commit()
                print(f"Executado: {cmd}")
            except Exception as e:
                # Silencia erros de "coluna já existe"
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    continue
                print(f"Aviso: {e}")

    print("Migration Scale 4.0 complete.")

if __name__ == "__main__":
    migrate_v4()
