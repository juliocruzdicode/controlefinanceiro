"""
Script de migração para o sistema de usuários
"""
from app import app, db
from app.models.user import Usuario
from werkzeug.security import generate_password_hash
import os

def migrar_usuarios():
    """
    Cria tabela de usuários e adiciona usuário admin padrão
    
    Returns:
        bool: True se a migração foi bem-sucedida, False caso contrário
    """
    with app.app_context():
        print("🔐 Iniciando migração do sistema de usuários...")
        
        try:
            # Verificar se já existem usuários
            total_usuarios = Usuario.query.count()
            if total_usuarios > 0:
                print("ℹ️ Usuários já existem no banco. Pulando migração.")
                return True
            
            # Criar usuário admin padrão
            print("👤 Criando usuário admin padrão...")
            
            # Gerar senha segura para o admin
            senha_admin = os.environ.get('ADMIN_PASSWORD', 'admin123')
            hash_senha = generate_password_hash(senha_admin)
            
            admin = Usuario(
                nome="admin",
                nome_completo="Administrador",
                email="admin@example.com",
                senha_hash=hash_senha,
                is_admin=True,
                email_verificado=True
            )
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Usuário admin criado com sucesso!")
            print(f"📧 Email: admin@example.com")
            print(f"🔑 Senha: {senha_admin}")
            print("🚨 Lembre-se de alterar essa senha após o primeiro login!")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro durante a migração: {str(e)}")
            db.session.rollback()
            return False
