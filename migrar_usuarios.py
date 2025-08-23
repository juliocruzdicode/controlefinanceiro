#!/usr/bin/env python3
"""
Script de migração para adicionar suporte a autenticação com MFA
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Usuario

def migrar_usuarios():
    """Cria tabela de usuários e adiciona usuário admin padrão"""
    with app.app_context():
        print("🔐 Iniciando migração de autenticação...")
        
        try:
            # Criar tabela de usuários
            db.create_all()
            print("✅ Tabela 'usuario' criada com sucesso")
            
            # Verificar se já existe usuário admin
            admin_user = Usuario.query.filter_by(username='admin').first()
            if admin_user:
                print("ℹ️  Usuário admin já existe")
            else:
                # Criar usuário admin padrão
                admin = Usuario(
                    username='admin',
                    email='admin@controle-financeiro.local',
                    is_admin=True
                )
                admin.set_password('admin123')  # Senha padrão - ALTERE IMEDIATAMENTE!
                
                db.session.add(admin)
                db.session.commit()
                
                print("✅ Usuário admin criado:")
                print("   👤 Usuário: admin")
                print("   🔑 Senha: admin123")
                print("   ⚠️  ALTERE A SENHA IMEDIATAMENTE!")
            
            print("\n🎉 Migração de autenticação concluída com sucesso!")
            print("\nPróximos passos:")
            print("1. Acesse /login para fazer login")
            print("2. Configure MFA em /setup-mfa")
            print("3. Altere a senha padrão")
            
        except Exception as e:
            print(f"❌ Erro na migração: {e}")
            return False
        
        return True

if __name__ == '__main__':
    migrar_usuarios()
