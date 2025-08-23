"""
Script para adicionar coluna password_reset_token à tabela usuario
"""
from app import app, db
from models import Usuario
import sys
import sqlite3
import os

def adicionar_coluna_reset_token():
    """Adiciona a coluna password_reset_token à tabela usuario"""
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
        
        print(f"Adicionando coluna password_reset_token à tabela usuario no banco: {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar se a coluna já existe
            cursor.execute("PRAGMA table_info(usuario)")
            colunas = cursor.fetchall()
            colunas_nomes = [coluna[1] for coluna in colunas]
            
            if 'password_reset_token' in colunas_nomes:
                print("Coluna password_reset_token já existe. Nada a fazer.")
                return
            
            # Adicionar a nova coluna
            cursor.execute("ALTER TABLE usuario ADD COLUMN password_reset_token TEXT")
            conn.commit()
            print("Coluna password_reset_token adicionada com sucesso!")
            
            conn.close()
            
        except Exception as e:
            print(f"Erro ao adicionar coluna: {e}")

if __name__ == "__main__":
    adicionar_coluna_reset_token()
