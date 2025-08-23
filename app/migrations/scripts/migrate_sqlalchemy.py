"""
Script de migração para SQLAlchemy
"""
from app import app, db
from datetime import datetime
import json
import os

def migrar_database():
    """
    Migra o banco de dados para a versão mais recente do esquema
    usando SQLAlchemy ORM
    
    Returns:
        bool: True se a migração foi bem-sucedida, False caso contrário
    """
    with app.app_context():
        print("🔄 Iniciando migração do banco de dados...")
        
        try:
            # Criar todas as tabelas definidas nos modelos
            print("📝 Criando tabelas...")
            db.create_all()
            
            # Inserir dados iniciais, se necessário
            # Isso pode incluir configurações padrão, usuário admin, etc.
            
            print("✅ Migração do banco de dados concluída com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro durante a migração: {str(e)}")
            return False
