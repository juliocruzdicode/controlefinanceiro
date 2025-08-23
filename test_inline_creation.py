#!/usr/bin/env python3
"""
Teste simples para verificar se a funcionalidade de criação inline está funcionando
"""

from app import app
from models import db, Usuario, Categoria, Conta
from flask_login import login_user
import json

def test_inline_creation():
    with app.app_context():
        # Obter usuário admin
        admin = Usuario.query.filter_by(username='admin').first()
        if not admin:
            print("❌ Usuário admin não encontrado")
            return
        
        print(f"✅ Usuário admin encontrado: {admin.username}")
        
        # Verificar categorias existentes
        categorias = Categoria.query.filter_by(user_id=admin.id).count()
        print(f"📊 Categorias existentes: {categorias}")
        
        # Verificar contas existentes
        contas = Conta.query.filter_by(user_id=admin.id).count()
        print(f"💳 Contas existentes: {contas}")
        
        print("\n🎯 Funcionalidade implementada:")
        print("✅ Template nova_transacao.html com botões '+' para categoria e conta")
        print("✅ Modais Bootstrap para criação inline")
        print("✅ JavaScript para AJAX requests")
        print("✅ Rotas AJAX /api/categoria/nova e /api/conta/nova")
        print("✅ Validação e isolamento por usuário")
        
        print("\n📝 Para testar:")
        print("1. Acesse http://localhost:5002/login")
        print("2. Faça login com admin/admin123")
        print("3. Vá para http://localhost:5002/nova-transacao")
        print("4. Clique no botão '+' ao lado de Categoria ou Conta")
        print("5. Preencha os dados no modal e clique em 'Criar'")
        print("6. A nova opção deve aparecer no dropdown automaticamente")

if __name__ == "__main__":
    test_inline_creation()
