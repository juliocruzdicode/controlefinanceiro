"""
Script de migração para o sistema de transações recorrentes
"""
from app import app, db
from app.models.recurring_transaction import TransacaoRecorrente
from app.models.enums import StatusRecorrencia
import sqlite3
import os
from datetime import datetime

def migrar_recorrentes():
    """
    Migra o banco de dados para incluir o sistema de transações recorrentes
    
    Returns:
        bool: True se a migração foi bem-sucedida, False caso contrário
    """
    with app.app_context():
        print("🔄 Iniciando migração do sistema de transações recorrentes...")
        
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
                
                # Verificar se a tabela já existe
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transacao_recorrente'")
                if cursor.fetchone():
                    print("ℹ️ Tabela de transações recorrentes já existe. Pulando migração.")
                    conn.close()
                    return True
                
                # Criar tabela de transações recorrentes
                print("📝 Criando tabela de transações recorrentes...")
                cursor.execute('''
                CREATE TABLE transacao_recorrente (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL,
                    tipo TEXT NOT NULL,
                    data_inicial DATETIME NOT NULL,
                    periodicidade TEXT NOT NULL,
                    dia_cobranca INTEGER,
                    dia_semana INTEGER,
                    parcelas_total INTEGER,
                    parcelas_geradas INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'ATIVA',
                    data_criacao DATETIME NOT NULL,
                    data_modificacao DATETIME NOT NULL,
                    tags_lista TEXT,
                    categoria_id INTEGER NOT NULL,
                    conta_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY (categoria_id) REFERENCES categoria (id),
                    FOREIGN KEY (conta_id) REFERENCES conta (id),
                    FOREIGN KEY (user_id) REFERENCES usuario (id)
                )
                ''')
                
                # Adicionar campo de recorrência à tabela de transações
                cursor.execute("PRAGMA table_info(transacao)")
                colunas = [col[1] for col in cursor.fetchall()]
                
                if 'recorrencia_id' not in colunas:
                    print("📝 Adicionando campo de recorrência à tabela de transações...")
                    cursor.execute('''
                    ALTER TABLE transacao 
                    ADD COLUMN recorrencia_id INTEGER DEFAULT NULL
                    REFERENCES transacao_recorrente (id)
                    ''')
                
                conn.commit()
                conn.close()
            else:
                # Para outros bancos, usar SQLAlchemy
                print("📝 Criando tabelas via SQLAlchemy...")
                db.create_all()
            
            print("✅ Migração do sistema de transações recorrentes concluída com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro durante a migração: {str(e)}")
            return False
