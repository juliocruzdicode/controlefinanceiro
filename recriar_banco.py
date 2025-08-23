#!/usr/bin/env python3
"""
Script para recriar o banco de dados com os novos modelos incluindo user_id
"""

import os
import shutil
from datetime import datetime
from app import app, db
from models import Usuario, Transacao, Categoria, Conta, Tag, TransacaoRecorrente, TipoTransacao, TipoConta, TipoRecorrencia, StatusRecorrencia

def backup_existing_db():
    """Faz backup do banco de dados atual"""
    db_path = 'instance/controle_financeiro.db'
    if os.path.exists(db_path):
        backup_name = f'controle_financeiro_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        backup_path = f'instance/{backup_name}'
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup criado: {backup_path}")
        return backup_path
    return None

def create_admin_user():
    """Cria usuário admin padrão"""
    admin = Usuario(
        username='admin',
        email='admin@controle.com',
        is_admin=True,
        email_verified=True
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print(f"✅ Usuário admin criado (ID: {admin.id})")
    return admin

def create_sample_data(admin_user):
    """Cria dados de exemplo para o admin"""
    
    # Criar algumas categorias
    categorias = [
        Categoria(nome='Alimentação', cor='#28a745', user_id=admin_user.id),
        Categoria(nome='Transporte', cor='#ffc107', user_id=admin_user.id),
        Categoria(nome='Salário', cor='#007bff', user_id=admin_user.id),
        Categoria(nome='Moradia', cor='#dc3545', user_id=admin_user.id),
        Categoria(nome='Lazer', cor='#17a2b8', user_id=admin_user.id),
    ]
    
    for categoria in categorias:
        db.session.add(categoria)
    
    db.session.commit()
    print(f"✅ {len(categorias)} categorias criadas")
    
    # Criar algumas contas
    contas = [
        Conta(nome='Conta Corrente', tipo=TipoConta.CORRENTE, saldo_inicial=1000.0, user_id=admin_user.id),
        Conta(nome='Poupança', tipo=TipoConta.POUPANCA, saldo_inicial=5000.0, user_id=admin_user.id),
        Conta(nome='Carteira', tipo=TipoConta.DINHEIRO, saldo_inicial=200.0, user_id=admin_user.id),
    ]
    
    for conta in contas:
        db.session.add(conta)
    
    db.session.commit()
    print(f"✅ {len(contas)} contas criadas")
    
    # Criar algumas tags
    tags = [
        Tag(nome='Essencial', cor='#dc3545', user_id=admin_user.id),
        Tag(nome='Opcional', cor='#ffc107', user_id=admin_user.id),
        Tag(nome='Investimento', cor='#28a745', user_id=admin_user.id),
    ]
    
    for tag in tags:
        db.session.add(tag)
    
    db.session.commit()
    print(f"✅ {len(tags)} tags criadas")
    
    # Criar algumas transações de exemplo
    transacoes = [
        Transacao(
            descricao='Salário do mês',
            valor=3000.0,
            tipo=TipoTransacao.RECEITA,
            categoria_id=categorias[2].id,  # Salário
            conta_id=contas[0].id,  # Conta Corrente
            user_id=admin_user.id
        ),
        Transacao(
            descricao='Compras no mercado',
            valor=250.0,
            tipo=TipoTransacao.DESPESA,
            categoria_id=categorias[0].id,  # Alimentação
            conta_id=contas[0].id,  # Conta Corrente
            user_id=admin_user.id
        ),
        Transacao(
            descricao='Combustível',
            valor=150.0,
            tipo=TipoTransacao.DESPESA,
            categoria_id=categorias[1].id,  # Transporte
            conta_id=contas[0].id,  # Conta Corrente
            user_id=admin_user.id
        ),
    ]
    
    for transacao in transacoes:
        db.session.add(transacao)
    
    # Adicionar tags às transações
    transacoes[0].add_tag('Essencial')  # Salário
    transacoes[1].add_tag('Essencial')  # Mercado
    transacoes[2].add_tag('Essencial')  # Combustível
    
    db.session.commit()
    print(f"✅ {len(transacoes)} transações criadas")

def main():
    """Função principal"""
    print("🔄 Iniciando recriação do banco de dados...")
    
    with app.app_context():
        # 1. Backup do banco atual
        backup_file = backup_existing_db()
        
        # 2. Recriar todas as tabelas
        print("🗑️  Removendo tabelas existentes...")
        db.drop_all()
        
        print("📊 Criando novas tabelas...")
        db.create_all()
        
        # 3. Criar usuário admin
        admin_user = create_admin_user()
        
        # 4. Criar dados de exemplo
        create_sample_data(admin_user)
        
        print("✅ Banco de dados recriado com sucesso!")
        print(f"📁 Backup anterior salvo em: {backup_file if backup_file else 'N/A'}")
        print("👤 Login: admin / Senha: admin123")
        print("🚀 Execute o app.py para testar!")

if __name__ == '__main__':
    main()
