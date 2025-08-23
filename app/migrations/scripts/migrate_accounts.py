"""
Script de migração para o sistema de contas
"""
from app import app, db
from app.models.account import Conta, TipoConta
from app.models.transaction import Transacao
import sqlite3
import os

def migrar_contas():
    """
    Migra o banco de dados para incluir o sistema de contas
    e associa transações existentes a uma conta padrão
    
    Returns:
        bool: True se a migração foi bem-sucedida, False caso contrário
    """
    with app.app_context():
        print("🔄 Iniciando migração do sistema de contas...")
        
        try:
            # Verificar se já existem contas
            total_contas = Conta.query.count()
            if total_contas > 0:
                print("ℹ️ Contas já existem no banco. Pulando migração.")
                return True
            
            # Criar conta padrão
            print("📝 Criando conta padrão...")
            conta_padrao = Conta(
                nome="Conta Principal",
                tipo=TipoConta.CONTA_CORRENTE,
                saldo=0,
                saldo_inicial=0,
                cor="#3498db",
                user_id=1  # Assumindo que o primeiro usuário é o admin
            )
            db.session.add(conta_padrao)
            db.session.commit()
            
            # Associar transações existentes à conta padrão
            print("🔄 Atualizando transações existentes...")
            transacoes = Transacao.query.all()
            
            if transacoes:
                for transacao in transacoes:
                    transacao.conta_id = conta_padrao.id
                
                # Recalcular saldo da conta
                receitas = sum(t.valor for t in transacoes if t.tipo == 'RECEITA')
                despesas = sum(t.valor for t in transacoes if t.tipo == 'DESPESA')
                conta_padrao.saldo = conta_padrao.saldo_inicial + receitas - despesas
                
                db.session.commit()
                print(f"✅ {len(transacoes)} transações associadas à conta padrão.")
            
            print("✅ Migração do sistema de contas concluída com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro durante a migração: {str(e)}")
            db.session.rollback()
            return False
