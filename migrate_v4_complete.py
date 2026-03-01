import os
from sqlalchemy import create_engine, text
from config import DATABASE_URL

def migrate_v4():
    print(f"Iniciando Migração em: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    
    # Comandos para adicionar colunas individualmente
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
        with engine.begin() as conn: # Inicia uma transação por comando
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                print(f"Sucesso: {table}.{col} adicionada.")
            except Exception as e:
                # Ignora se a coluna já existir
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"Info: {table}.{col} já existe.")
                else:
                    print(f"Erro em {table}.{col}: {e}")

    print("Migration Scale 4.0 complete.")

if __name__ == "__main__":
    migrate_v4()
