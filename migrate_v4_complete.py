import sqlite3
from logger import logger

def migrate_v4():
    conn = sqlite3.connect('ceo_ia.db')
    cursor = conn.cursor()
    
    # Colunas para User
    user_cols = [
        ('is_admin', 'BOOLEAN DEFAULT 0'),
        ('is_active', 'BOOLEAN DEFAULT 1'),
        ('last_run_at', 'TEXT'),
        ('created_at', 'FLOAT')
    ]
    
    # Colunas para Idea
    idea_cols = [
        ('views', 'INTEGER DEFAULT 0'),
        ('clicks', 'INTEGER DEFAULT 0'),
        ('conversions', 'INTEGER DEFAULT 0'),
        ('version', 'INTEGER DEFAULT 1'),
        ('created_at', 'FLOAT')
    ]
    
    def add_cols(table, cols):
        for col_name, col_def in cols:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")
                print(f"Colunm {col_name} added to {table}.")
            except sqlite3.OperationalError as e:
                print(f"Skipping {col_name} in {table}: {e}")

    add_cols('users', user_cols)
    add_cols('ideas', idea_cols)
    
    conn.commit()
    conn.close()
    print("Migration Scale 4.0 complete.")

if __name__ == "__main__":
    migrate_v4()
