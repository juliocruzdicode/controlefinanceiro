"""
Script de migração para o sistema de tags
"""
from app import app, db
from app.models.tag import Tag
import sqlite3
import os
from datetime import datetime

def backup_database(db_path):
    """
    Cria um backup do banco de dados antes da migração
    
    Args:
        db_path: Caminho do arquivo de banco de dados
        
    Returns:
        str: Caminho do arquivo de backup
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_tags_{timestamp}"
    
    # Copiar arquivo original para backup
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup criado em: {backup_path}")
    
    return backup_path

def migrar_tags():
    """
    Migra o banco de dados para incluir o sistema de tags
    
    Returns:
        bool: True se a migração foi bem-sucedida, False caso contrário
    """
    with app.app_context():
        print("🔄 Iniciando migração do sistema de tags...")
        
        try:
            # Verificar se é SQLite
            if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
                # Determinar caminho do banco de dados
                if 'instance/' in app.config['SQLALCHEMY_DATABASE_URI']:
                    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
                else:
                    db_path = os.path.join('instance', app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
                
                # Criar backup antes de começar
                backup_database(db_path)
                
                # Conectar ao banco SQLite diretamente
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Verificar se as tabelas já existem
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tag'")
                if cursor.fetchone():
                    print("ℹ️ Tabela de tags já existe. Pulando migração.")
                    conn.close()
                    return True
                
                # Criar tabela de tags
                print("📝 Criando tabela de tags...")
                cursor.execute('''
                CREATE TABLE tag (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    cor TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES usuario (id)
                )
                ''')
                
                # Criar tabela de relacionamento
                print("📝 Criando tabela de relacionamento transacao_tags...")
                cursor.execute('''
                CREATE TABLE transacao_tags (
                    transacao_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    PRIMARY KEY (transacao_id, tag_id),
                    FOREIGN KEY (transacao_id) REFERENCES transacao (id),
                    FOREIGN KEY (tag_id) REFERENCES tag (id)
                )
                ''')
                
                conn.commit()
                conn.close()
            else:
                # Para outros bancos, usar SQLAlchemy
                print("📝 Criando tabelas de tags via SQLAlchemy...")
                db.create_all()
            
            print("✅ Migração do sistema de tags concluída com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro durante a migração: {str(e)}")
            return False
