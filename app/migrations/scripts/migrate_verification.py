"""
Script de migração para sistema de verificação de email
"""
from app import app, db
from app.models.user import Usuario
import sqlite3
import os

def migrar_verificacao_email():
    """
    Adiciona campo de verificação de email na tabela de usuários
    
    Returns:
        bool: True se a migração foi bem-sucedida, False caso contrário
    """
    with app.app_context():
        print("📧 Iniciando migração para verificação de email...")
        
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
                
                if 'email_verificado' not in colunas:
                    print("📝 Adicionando coluna de verificação de email...")
                    cursor.execute('''
                    ALTER TABLE usuario 
                    ADD COLUMN email_verificado BOOLEAN DEFAULT 0
                    ''')
                    
                if 'token_verificacao_email' not in colunas:
                    print("📝 Adicionando coluna de token de verificação...")
                    cursor.execute('''
                    ALTER TABLE usuario 
                    ADD COLUMN token_verificacao_email TEXT DEFAULT NULL
                    ''')
                
                # Definir usuários existentes como verificados
                cursor.execute('''
                UPDATE usuario 
                SET email_verificado = 1
                WHERE email_verificado IS NULL OR email_verificado = 0
                ''')
                
                conn.commit()
                conn.close()
            else:
                # Para outros bancos, usar SQLAlchemy
                print("📝 Atualizando esquema via SQLAlchemy...")
                db.create_all()
                
                # Definir usuários existentes como verificados
                usuarios = Usuario.query.filter_by(email_verificado=False).all()
                for usuario in usuarios:
                    usuario.email_verificado = True
                db.session.commit()
            
            print("✅ Migração para verificação de email concluída com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro durante a migração: {str(e)}")
            return False
