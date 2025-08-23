"""
Script para adicionar a tabela de temas e o campo de tema no usuário
"""
from app import app, db
from models import Tema, Usuario
import sqlite3
import os
import json

def criar_tabela_tema():
    """Cria a tabela de temas e adiciona os campos de tema ao usuário"""
    with app.app_context():
        # Verificar se estamos usando SQLite
        if 'sqlite' not in app.config['SQLALCHEMY_DATABASE_URI']:
            print("Este script é apenas para SQLite. Use migração SQLAlchemy para PostgreSQL.")
            return
        
        # Ajustar o caminho para usar o diretório instance
        if 'instance/' not in app.config['SQLALCHEMY_DATABASE_URI']:
            db_path = os.path.join('instance', app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
        else:
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            
        if not os.path.exists(db_path):
            print(f"Banco de dados não encontrado: {db_path}")
            return
        
        print(f"Adicionando tabela de temas e campos de tema ao usuário no banco: {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 1. Verificar se a tabela tema já existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tema'")
            if not cursor.fetchone():
                # Criar a tabela tema
                cursor.execute('''
                CREATE TABLE tema (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome VARCHAR(50) NOT NULL UNIQUE,
                    descricao VARCHAR(200),
                    is_default BOOLEAN DEFAULT 0,
                    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cor_primaria VARCHAR(7) DEFAULT '#007bff',
                    cor_secundaria VARCHAR(7) DEFAULT '#6c757d',
                    cor_sucesso VARCHAR(7) DEFAULT '#28a745',
                    cor_perigo VARCHAR(7) DEFAULT '#dc3545',
                    cor_alerta VARCHAR(7) DEFAULT '#ffc107',
                    cor_info VARCHAR(7) DEFAULT '#17a2b8',
                    cor_fundo VARCHAR(7) DEFAULT '#ffffff',
                    cor_texto VARCHAR(7) DEFAULT '#212529',
                    cor_primaria_dark VARCHAR(7) DEFAULT '#375a7f',
                    cor_secundaria_dark VARCHAR(7) DEFAULT '#444444',
                    cor_sucesso_dark VARCHAR(7) DEFAULT '#00bc8c',
                    cor_perigo_dark VARCHAR(7) DEFAULT '#e74c3c',
                    cor_alerta_dark VARCHAR(7) DEFAULT '#f39c12',
                    cor_info_dark VARCHAR(7) DEFAULT '#3498db',
                    cor_fundo_dark VARCHAR(7) DEFAULT '#222222',
                    cor_texto_dark VARCHAR(7) DEFAULT '#ffffff'
                )
                ''')
                print("Tabela tema criada com sucesso")
                
                # Criar tema padrão
                cursor.execute('''
                INSERT INTO tema (nome, descricao, is_default)
                VALUES ('Padrão', 'Tema padrão do sistema', 1)
                ''')
                print("Tema padrão criado com sucesso")
            else:
                print("Tabela tema já existe")
            
            # 2. Verificar se os campos de tema já existem na tabela usuario
            cursor.execute("PRAGMA table_info(usuario)")
            colunas = cursor.fetchall()
            colunas_nomes = [coluna[1] for coluna in colunas]
            
            if 'tema_id' not in colunas_nomes:
                cursor.execute("ALTER TABLE usuario ADD COLUMN tema_id INTEGER REFERENCES tema(id)")
                print("Coluna tema_id adicionada à tabela usuario")
            else:
                print("Coluna tema_id já existe na tabela usuario")
                
            if 'dark_mode' not in colunas_nomes:
                cursor.execute("ALTER TABLE usuario ADD COLUMN dark_mode BOOLEAN DEFAULT 0")
                print("Coluna dark_mode adicionada à tabela usuario")
            else:
                print("Coluna dark_mode já existe na tabela usuario")
            
            # Definir tema padrão para todos os usuários que não têm tema
            tema_id = cursor.execute("SELECT id FROM tema WHERE is_default = 1").fetchone()[0]
            cursor.execute("UPDATE usuario SET tema_id = ? WHERE tema_id IS NULL", (tema_id,))
            print(f"Tema padrão (ID: {tema_id}) definido para todos os usuários")
            
            conn.commit()
            conn.close()
            print("Migração concluída com sucesso!")
            
        except Exception as e:
            print(f"Erro durante a migração: {e}")
            try:
                conn.rollback()
                conn.close()
            except:
                pass

if __name__ == "__main__":
    criar_tabela_tema()
