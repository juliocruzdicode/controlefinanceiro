#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para criar 40 transações de teste para o usuário admin
"""

from app import app
from models import db, Transacao, Categoria, Conta, Usuario, TipoTransacao
from datetime import datetime, timedelta
import random

# Dados de exemplo para as transações
TRANSACOES_EXEMPLO = [
    # Receitas
    {"descricao": "Salário", "valor": 5000.00, "tipo": "RECEITA", "categoria": "Salário"},
    {"descricao": "Freelance Design", "valor": 800.00, "tipo": "RECEITA", "categoria": "Trabalho Extra"},
    {"descricao": "Venda de produto", "valor": 350.00, "tipo": "RECEITA", "categoria": "Vendas"},
    {"descricao": "Dividendos", "valor": 120.00, "tipo": "RECEITA", "categoria": "Investimentos"},
    {"descricao": "Cashback", "valor": 45.00, "tipo": "RECEITA", "categoria": "Outros"},
    
    # Despesas - Alimentação
    {"descricao": "Supermercado", "valor": -280.50, "tipo": "DESPESA", "categoria": "Alimentação"},
    {"descricao": "Restaurante", "valor": -85.00, "tipo": "DESPESA", "categoria": "Alimentação"},
    {"descricao": "Lanchonete", "valor": -25.90, "tipo": "DESPESA", "categoria": "Alimentação"},
    {"descricao": "Padaria", "valor": -18.50, "tipo": "DESPESA", "categoria": "Alimentação"},
    {"descricao": "Delivery", "valor": -42.00, "tipo": "DESPESA", "categoria": "Alimentação"},
    
    # Despesas - Transporte
    {"descricao": "Combustível", "valor": -150.00, "tipo": "DESPESA", "categoria": "Transporte"},
    {"descricao": "Uber", "valor": -32.50, "tipo": "DESPESA", "categoria": "Transporte"},
    {"descricao": "Estacionamento", "valor": -15.00, "tipo": "DESPESA", "categoria": "Transporte"},
    {"descricao": "Pedágio", "valor": -8.70, "tipo": "DESPESA", "categoria": "Transporte"},
    
    # Despesas - Moradia
    {"descricao": "Aluguel", "valor": -1200.00, "tipo": "DESPESA", "categoria": "Moradia"},
    {"descricao": "Conta de Luz", "valor": -180.45, "tipo": "DESPESA", "categoria": "Moradia"},
    {"descricao": "Conta de Água", "valor": -95.30, "tipo": "DESPESA", "categoria": "Moradia"},
    {"descricao": "Internet", "valor": -89.90, "tipo": "DESPESA", "categoria": "Moradia"},
    {"descricao": "Condomínio", "valor": -350.00, "tipo": "DESPESA", "categoria": "Moradia"},
    
    # Despesas - Saúde
    {"descricao": "Farmácia", "valor": -45.80, "tipo": "DESPESA", "categoria": "Saúde"},
    {"descricao": "Consulta Médica", "valor": -200.00, "tipo": "DESPESA", "categoria": "Saúde"},
    {"descricao": "Academia", "valor": -89.90, "tipo": "DESPESA", "categoria": "Saúde"},
    
    # Despesas - Lazer
    {"descricao": "Cinema", "valor": -35.00, "tipo": "DESPESA", "categoria": "Lazer"},
    {"descricao": "Netflix", "valor": -32.90, "tipo": "DESPESA", "categoria": "Lazer"},
    {"descricao": "Spotify", "valor": -19.90, "tipo": "DESPESA", "categoria": "Lazer"},
    {"descricao": "Livros", "valor": -68.00, "tipo": "DESPESA", "categoria": "Lazer"},
    
    # Despesas - Vestuário
    {"descricao": "Roupas", "valor": -125.00, "tipo": "DESPESA", "categoria": "Vestuário"},
    {"descricao": "Sapatos", "valor": -89.90, "tipo": "DESPESA", "categoria": "Vestuário"},
    
    # Despesas - Educação
    {"descricao": "Curso Online", "valor": -150.00, "tipo": "DESPESA", "categoria": "Educação"},
    {"descricao": "Material Escolar", "valor": -78.50, "tipo": "DESPESA", "categoria": "Educação"},
    
    # Despesas - Outros
    {"descricao": "Presente", "valor": -95.00, "tipo": "DESPESA", "categoria": "Outros"},
    {"descricao": "Doação", "valor": -50.00, "tipo": "DESPESA", "categoria": "Outros"},
    {"descricao": "Taxa Bancária", "valor": -12.90, "tipo": "DESPESA", "categoria": "Outros"},
    {"descricao": "Manutenção Carro", "valor": -280.00, "tipo": "DESPESA", "categoria": "Transporte"},
    {"descricao": "Seguro", "valor": -185.00, "tipo": "DESPESA", "categoria": "Outros"},
    {"descricao": "Celular", "valor": -79.90, "tipo": "DESPESA", "categoria": "Outros"},
    {"descricao": "Cabelereiro", "valor": -45.00, "tipo": "DESPESA", "categoria": "Outros"},
    {"descricao": "Pet Shop", "valor": -85.00, "tipo": "DESPESA", "categoria": "Outros"},
    {"descricao": "Investimento", "valor": -500.00, "tipo": "DESPESA", "categoria": "Investimentos"},
    {"descricao": "Emergência Médica", "valor": -320.00, "tipo": "DESPESA", "categoria": "Saúde"}
]

def criar_categorias_padrao(user_id):
    """Criar categorias padrão se não existirem"""
    categorias_padrao = [
        "Salário", "Trabalho Extra", "Vendas", "Investimentos", "Outros",
        "Alimentação", "Transporte", "Moradia", "Saúde", "Lazer", 
        "Vestuário", "Educação"
    ]
    
    categorias_existentes = {cat.nome for cat in Categoria.query.filter_by(user_id=user_id).all()}
    
    for nome_categoria in categorias_padrao:
        if nome_categoria not in categorias_existentes:
            categoria = Categoria(
                nome=nome_categoria,
                user_id=user_id
            )
            db.session.add(categoria)
    
    db.session.commit()

def criar_conta_padrao(user_id):
    """Criar conta padrão se não existir"""
    conta_existente = Conta.query.filter_by(user_id=user_id).first()
    if not conta_existente:
        conta = Conta(
            nome="Conta Principal",
            saldo_inicial=1000.00,
            user_id=user_id
        )
        db.session.add(conta)
        db.session.commit()
        return conta
    return conta_existente

def criar_transacoes_admin():
    """Criar 40 transações para o usuário admin"""
    try:
        # Buscar o usuário admin
        admin = Usuario.query.filter_by(username='admin').first()
        if not admin:
            print("❌ Usuário admin não encontrado!")
            return False
        
        print(f"✅ Usuário admin encontrado - ID: {admin.id}")
        
        # Criar categorias padrão
        print("📁 Criando categorias padrão...")
        criar_categorias_padrao(admin.id)
        
        # Criar conta padrão
        print("🏦 Criando conta padrão...")
        conta = criar_conta_padrao(admin.id)
        
        # Buscar categorias do admin
        categorias = {cat.nome: cat.id for cat in Categoria.query.filter_by(user_id=admin.id).all()}
        print(f"📂 Categorias disponíveis: {list(categorias.keys())}")
        
        # Data inicial (60 dias atrás)
        data_inicial = datetime.now() - timedelta(days=60)
        
        print(f"💰 Criando 40 transações para o período de {data_inicial.strftime('%d/%m/%Y')} até hoje...")
        
        transacoes_criadas = 0
        
        # Criar as transações
        for i in range(40):
            transacao_template = TRANSACOES_EXEMPLO[i % len(TRANSACOES_EXEMPLO)]
            
            # Data aleatória nos últimos 60 dias
            dias_aleatorio = random.randint(0, 60)
            data_transacao = data_inicial + timedelta(days=dias_aleatorio)
            
            # Verificar se a categoria existe
            categoria_nome = transacao_template["categoria"]
            categoria_id = categorias.get(categoria_nome)
            
            if not categoria_id:
                print(f"⚠️  Categoria '{categoria_nome}' não encontrada, usando 'Outros'")
                categoria_id = categorias.get("Outros")
            
            # Adicionar variação no valor (±20%)
            valor_base = abs(transacao_template["valor"])
            variacao = random.uniform(0.8, 1.2)
            valor_final = round(valor_base * variacao, 2)
            
            # Manter o sinal correto
            if transacao_template["valor"] < 0:
                valor_final = -valor_final
            
            transacao = Transacao(
                descricao=f"{transacao_template['descricao']} #{i+1}",
                valor=valor_final,
                data_transacao=data_transacao,
                tipo=TipoTransacao.RECEITA if transacao_template["tipo"] == "RECEITA" else TipoTransacao.DESPESA,
                categoria_id=categoria_id,
                conta_id=conta.id,
                user_id=admin.id
            )
            
            db.session.add(transacao)
            transacoes_criadas += 1
            
            if (i + 1) % 10 == 0:
                print(f"✅ {i + 1} transações criadas...")
        
        # Salvar no banco
        db.session.commit()
        
        print(f"🎉 Sucesso! {transacoes_criadas} transações criadas para o usuário admin")
        
        # Calcular totais
        total_receitas = sum(t["valor"] for t in TRANSACOES_EXEMPLO[:40] if t["valor"] > 0) * variacao
        total_despesas = sum(abs(t["valor"]) for t in TRANSACOES_EXEMPLO[:40] if t["valor"] < 0) * variacao
        
        print(f"📊 Resumo:")
        print(f"   💚 Total de receitas: R$ {total_receitas:,.2f}")
        print(f"   💸 Total de despesas: R$ {total_despesas:,.2f}")
        print(f"   📈 Saldo: R$ {(total_receitas - total_despesas):,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar transações: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    with app.app_context():
        print("🚀 Iniciando criação de transações para o usuário admin...")
        print("=" * 60)
        sucesso = criar_transacoes_admin()
        print("=" * 60)
        if sucesso:
            print("✅ Processo concluído com sucesso!")
        else:
            print("❌ Processo falhou!")
