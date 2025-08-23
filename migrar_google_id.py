import sqlite3
import os

def migrar_google_id():
    """Adiciona a coluna google_id à tabela usuario"""
    print("Iniciando migração para adicionar coluna google_id à tabela usuario...")
    
    # Caminho do banco de dados SQLite
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'controle_financeiro.db')
    
    if not os.path.exists(db_path):
        print(f"Banco de dados não encontrado em {db_path}")
        return
    
    # Conectar ao banco de dados
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(usuario)")
        colunas = cursor.fetchall()
        colunas_nomes = [coluna[1] for coluna in colunas]
        
        if 'google_id' in colunas_nomes:
            print("A coluna google_id já existe na tabela usuario.")
            return
        
        # SQLite não permite adicionar restrições UNIQUE em ALTER TABLE
        # Vamos adicionar a coluna sem UNIQUE primeiro
        cursor.execute("ALTER TABLE usuario ADD COLUMN google_id TEXT")
        
        # Commit das alterações
        conn.commit()
        print("Coluna google_id adicionada com sucesso à tabela usuario!")
        
    except Exception as e:
        print(f"Erro ao adicionar coluna google_id: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrar_google_id()
