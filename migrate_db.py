import sqlite3

def migrate():
    try:
        conn = sqlite3.connect('ceo_ia.db')
        cursor = conn.cursor()
        
        # Lista de colunas para adicionar
        columns = [
            ('mp_access_token', 'VARCHAR'),
            ('mp_refresh_token', 'VARCHAR'),
            ('mp_user_id', 'VARCHAR')
        ]
        
        for col_name, col_type in columns:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                print(f"Coluna {col_name} adicionada com sucesso.")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"Coluna {col_name} já existe.")
                else:
                    print(f"Erro ao adicionar {col_name}: {e}")
        
        conn.commit()
        conn.close()
        print("Migração concluída.")
    except Exception as e:
        print(f"Erro na migração: {e}")

if __name__ == "__main__":
    migrate()
