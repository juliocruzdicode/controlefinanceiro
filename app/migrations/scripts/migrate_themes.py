"""
Script de migração para o sistema de temas
"""
from app import app, db
from app.models.theme import Tema
from app.models.user import Usuario
import sqlite3
import os
import json

def migrar_temas():
    """
    Cria a tabela de temas e adiciona temas padrão
    
    Returns:
        bool: True se a migração foi bem-sucedida, False caso contrário
    """
    with app.app_context():
        print("🎨 Iniciando migração do sistema de temas...")
        
        try:
            # Verificar se já existem temas
            total_temas = Tema.query.count()
            if total_temas > 0:
                print("ℹ️ Temas já existem no banco. Pulando migração.")
                return True
            
            # Criar temas padrão
            print("🎨 Criando temas padrão...")
            
            temas = [
                {
                    'nome': 'Padrão',
                    'cor_primaria': '#3498db',
                    'cor_secundaria': '#2ecc71',
                    'cor_background': '#f5f5f5',
                    'cor_texto': '#333333',
                    'cor_card': '#ffffff',
                    'modo_escuro': False,
                    'publico': True
                },
                {
                    'nome': 'Modo Escuro',
                    'cor_primaria': '#3498db',
                    'cor_secundaria': '#2ecc71',
                    'cor_background': '#121212',
                    'cor_texto': '#f5f5f5',
                    'cor_card': '#1e1e1e',
                    'modo_escuro': True,
                    'publico': True
                },
                {
                    'nome': 'Monocromático',
                    'cor_primaria': '#555555',
                    'cor_secundaria': '#999999',
                    'cor_background': '#f8f8f8',
                    'cor_texto': '#333333',
                    'cor_card': '#ffffff',
                    'modo_escuro': False,
                    'publico': True
                }
            ]
            
            for tema_data in temas:
                tema = Tema(**tema_data)
                db.session.add(tema)
            
            db.session.commit()
            
            # Definir tema padrão para usuários existentes
            tema_padrao = Tema.query.filter_by(nome='Padrão').first()
            if tema_padrao:
                usuarios = Usuario.query.all()
                for usuario in usuarios:
                    usuario.tema_id = tema_padrao.id
                db.session.commit()
            
            print("✅ Migração do sistema de temas concluída com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro durante a migração: {str(e)}")
            db.session.rollback()
            return False
