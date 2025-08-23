#!/usr/bin/env python3
"""
Script para testar o sistema de verificação de email
"""

from app import app, db
from models import Usuario

def test_email_verification():
    """Testa o sistema de verificação de email"""
    with app.app_context():
        # Criar usuário de teste
        test_user = Usuario(
            username="teste_email", 
            email="teste@example.com"
        )
        test_user.set_password("MinhaSenh@123")
        test_user.email_verified = False
        
        db.session.add(test_user)
        db.session.commit()
        
        # Gerar token de verificação
        token = test_user.generate_email_verification_token()
        db.session.commit()
        
        print("🧪 Teste de verificação de email")
        print(f"👤 Usuário: {test_user.username}")
        print(f"📧 Email: {test_user.email}")
        print(f"🔑 Token: {token}")
        print(f"🔗 URL de verificação: http://127.0.0.1:5002/confirm-email/{token}")
        print(f"✅ Email verificado: {test_user.email_verified}")
        
        return test_user, token

if __name__ == '__main__':
    user, token = test_email_verification()
    
    print("\n🚀 Para testar:")
    print(f"1. Acesse: http://127.0.0.1:5002/confirm-email/{token}")
    print("2. Ou teste o login com usuário não verificado")
    print("3. Usuário: teste_email | Senha: MinhaSenh@123")
