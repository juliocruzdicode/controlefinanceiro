#!/usr/bin/env python3
"""
Teste específico para verificar se a geração de transações recorrentes está funcionando
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar a aplicação Flask e os modelos
from app import app
from models import db, TransacaoRecorrente, TipoRecorrencia, StatusRecorrencia, TipoTransacao, Transacao, Usuario, Categoria, Conta
from datetime import datetime, timedelta
from models import TransacaoRecorrente, TipoRecorrencia, StatusRecorrencia, TipoTransacao, Transacao, Usuario, Categoria, Conta

def testar_geracao_recorrentes():
    """Testa a geração de transações recorrentes"""
    with app.app_context():
        try:
            print("🧪 Iniciando teste de geração de transações recorrentes...")
            
            # Primeiro, limpar transações recorrentes existentes para o teste
            usuario = Usuario.query.filter_by(email='teste@teste.com').first()
            
            if not usuario:
                print("⚠️ Criando usuário de teste...")
                usuario = Usuario(
                    nome='Usuário Teste',
                    email='teste@teste.com',
                    senha_hash='123456'  # Não é seguro, apenas para teste
                )
                db.session.add(usuario)
                db.session.commit()
            
            # Verificar se existem categorias e contas para o teste
            categoria = Categoria.query.filter_by(user_id=usuario.id).first()
            if not categoria:
                print("⚠️ Criando categoria de teste...")
                categoria = Categoria(
                    nome='Categoria Teste',
                    user_id=usuario.id
                )
                db.session.add(categoria)
                db.session.commit()
            
            conta = Conta.query.filter_by(user_id=usuario.id).first()
            if not conta:
                print("⚠️ Criando conta de teste...")
                conta = Conta(
                    nome='Conta Teste',
                    saldo_inicial=1000,
                    user_id=usuario.id
                )
                db.session.add(conta)
                db.session.commit()
            
            # Limpar transações recorrentes existentes do usuário de teste
            TransacaoRecorrente.query.filter_by(user_id=usuario.id).delete()
            db.session.commit()
            
            # Criar uma nova transação recorrente para teste
            hoje = datetime.utcnow()
            data_inicio = hoje - timedelta(days=30)  # 30 dias atrás
            
            recorrente = TransacaoRecorrente(
                descricao='Transação Teste Recorrente',
                valor=100.00,
                tipo=TipoTransacao.DESPESA,
                data_inicio=data_inicio,
                tipo_recorrencia=TipoRecorrencia.MENSAL,
                status=StatusRecorrencia.ATIVA,
                is_parcelada=False,
                categoria_id=categoria.id,
                conta_id=conta.id,
                user_id=usuario.id
            )
            
            db.session.add(recorrente)
            db.session.commit()
            
            print(f"✅ Transação recorrente criada com ID: {recorrente.id}")
            
            # Gerar transações pendentes
            transacoes_geradas = recorrente.gerar_transacoes_pendentes()
            
            print(f"✅ {len(transacoes_geradas)} transações geradas com sucesso")
            
            # Verificar se as transações foram criadas corretamente
            for idx, transacao in enumerate(transacoes_geradas):
                print(f"  📝 Transação #{idx+1}: ID={transacao.id}, Descrição={transacao.descricao}, user_id={transacao.user_id}")
                if transacao.user_id is None:
                    print("❌ ERRO: user_id é None! O problema persiste.")
                    return False
            
            print("✅ Todas as transações têm user_id definido corretamente")
            return True
            
        except Exception as e:
            print(f"❌ Erro durante o teste: {str(e)}")
            return False

if __name__ == '__main__':
    # Configurar o ambiente de teste
    os.environ['FLASK_ENV'] = 'development'
    
    # Executar o teste
    resultado = testar_geracao_recorrentes()
    
    if resultado:
        print("✅ Teste concluído com sucesso! O problema foi resolvido.")
    else:
        print("❌ Teste falhou! O problema pode persistir.")
