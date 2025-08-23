"""
Script de migração para adição de token de redefinição de senha
"""
from app import app, db
from app.models.user import Usuario
import sqlite3
import os

def migrar_token_redefinicao():
    """
    Adiciona campo de token de redefinição de senha na tabela de usuários
    
    Returns:
        bool: True se a migração foi bem-sucedida, False caso contrário
    """
    with app.app_context():
        print("🔑 Iniciando migração para token de redefinição de senha...")
        
        try:
            # Verificar se é SQLite
            if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
                # Determinar caminho do banco de dados
                if 'instance/' in app.config['SQLALCHEMY_DATABASE_URI']:
                    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
                else:
                    db_path = os.path.join('instance', app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
                
                # Conectar ao banco SQLite diretamente
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Verificar se a coluna já existe
                cursor.execute("PRAGMA table_info(usuario)")
                colunas = [col[1] for col in cursor.fetchall()]
                
                if 'token_redefinicao_senha' not in colunas:
                    print("📝 Adicionando coluna de token de redefinição de senha...")
                    cursor.execute('''
                    ALTER TABLE usuario 
                    ADD COLUMN token_redefinicao_senha TEXT DEFAULT NULL
                    ''')
                    
                if 'token_expiracao' not in colunas:
                    print("📝 Adicionando coluna de expiração de token...")
                    cursor.execute('''
                    ALTER TABLE usuario 
                    ADD COLUMN token_expiracao DATETIME DEFAULT NULL
                    ''')
                
                conn.commit()
                conn.close()
            else:
                # Para outros bancos, usar SQLAlchemy
                print("📝 Atualizando esquema via SQLAlchemy...")
                db.create_all()
            
            print("✅ Migração para token de redefinição de senha concluída com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro durante a migração: {str(e)}")
            return False
