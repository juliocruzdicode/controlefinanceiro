#!/usr/bin/env python3
"""
Script para adicionar uma transação de teste e verificar se os botões aparecem
"""

import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Transacao, Categoria, TipoTransacao
from datetime import date, datetime

def criar_transacao_teste():
    """Cria uma transação de teste simples"""
    with app.app_context():
        try:
            # Verificar se já existe alguma categoria
            categoria = Categoria.query.first()
            if not categoria:
                # Criar uma categoria de teste
                categoria = Categoria(nome="Alimentação", tipo=TipoTransacao.DESPESA)
                db.session.add(categoria)
                db.session.commit()
                print("✅ Categoria de teste criada")
            
            # Criar uma transação de teste (não recorrente)
            transacao = Transacao(
                descricao="Teste - Almoço",
                valor=25.50,
                data=date.today(),
                tipo=TipoTransacao.DESPESA,
                categoria_id=categoria.id,
                recorrencia_id=None  # Não recorrente
            )
            
            db.session.add(transacao)
            db.session.commit()
            
            print(f"✅ Transação de teste criada: ID {transacao.id}")
            print(f"   Descrição: {transacao.descricao}")
            print(f"   Valor: R$ {transacao.valor}")
            print(f"   É recorrente: {transacao.is_recorrente}")
            
            return transacao.id
            
        except Exception as e:
            print(f"❌ Erro ao criar transação de teste: {e}")
            db.session.rollback()
            return None

def listar_transacoes():
    """Lista todas as transações no banco"""
    with app.app_context():
        try:
            transacoes = Transacao.query.all()
            print(f"\n📊 Total de transações no banco: {len(transacoes)}")
            
            for t in transacoes:
                print(f"   ID {t.id}: {t.descricao} - R$ {t.valor} - Recorrente: {t.is_recorrente}")
                
        except Exception as e:
            print(f"❌ Erro ao listar transações: {e}")

if __name__ == "__main__":
    print("🧪 Criando transação de teste...")
    print("=" * 40)
    
    # Listar transações existentes
    listar_transacoes()
    
    # Criar uma transação de teste
    transacao_id = criar_transacao_teste()
    
    if transacao_id:
        print(f"\n🎯 Agora você pode testar os botões com a transação ID {transacao_id}")
        print("   Acesse: http://127.0.0.1:5001/transacoes")
    
    # Listar transações após criação
    print("\n" + "=" * 40)
    listar_transacoes()
