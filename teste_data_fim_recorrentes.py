#!/usr/bin/env python3
# teste_data_fim_recorrentes.py
"""
Script para testar a geração de transações recorrentes com e sem data_fim.

Este script testa os seguintes cenários:
1. Transação recorrente com data_fim: deve gerar todas as transações até a data fim
2. Transação recorrente sem data_fim: deve gerar transações para os próximos X meses
"""

import os
import sys
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Garantir que estamos no diretório correto
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Importar as dependências da aplicação
# Usando o ambiente normal, mas desativando o modo debug para evitar problemas
import config
config.DEBUG = False
from app import app, db
from models import Usuario, TransacaoRecorrente, Transacao, Categoria, Conta, Status

def limpar_dados_teste():
    """Limpa os dados de teste do banco de dados."""
    with app.app_context():
        # Remover todas as transações e transações recorrentes de teste
        Transacao.query.filter(Transacao.descricao.like('TESTE_%')).delete()
        TransacaoRecorrente.query.filter(TransacaoRecorrente.descricao.like('TESTE_%')).delete()
        db.session.commit()
        logger.info("Dados de teste limpos com sucesso")

def criar_usuario_teste():
    """Cria ou obtém um usuário de teste."""
    with app.app_context():
        usuario = Usuario.query.filter_by(email='teste@teste.com').first()
        if not usuario:
            usuario = Usuario(
                nome='Usuário Teste', 
                email='teste@teste.com',
                senha='senha_teste',
                data_criacao=datetime.now()
            )
            db.session.add(usuario)
            db.session.commit()
            logger.info(f"Usuário de teste criado: {usuario.id}")
        else:
            logger.info(f"Usuário de teste existente: {usuario.id}")
        return usuario

def criar_categoria_teste(usuario_id):
    """Cria ou obtém uma categoria de teste."""
    with app.app_context():
        categoria = Categoria.query.filter_by(nome='TESTE_CATEGORIA', usuario_id=usuario_id).first()
        if not categoria:
            categoria = Categoria(
                nome='TESTE_CATEGORIA',
                usuario_id=usuario_id
            )
            db.session.add(categoria)
            db.session.commit()
            logger.info(f"Categoria de teste criada: {categoria.id}")
        else:
            logger.info(f"Categoria de teste existente: {categoria.id}")
        return categoria

def criar_conta_teste(usuario_id):
    """Cria ou obtém uma conta de teste."""
    with app.app_context():
        conta = Conta.query.filter_by(nome='TESTE_CONTA', usuario_id=usuario_id).first()
        if not conta:
            conta = Conta(
                nome='TESTE_CONTA',
                saldo_inicial=1000,
                usuario_id=usuario_id
            )
            db.session.add(conta)
            db.session.commit()
            logger.info(f"Conta de teste criada: {conta.id}")
        else:
            logger.info(f"Conta de teste existente: {conta.id}")
        return conta

def criar_transacao_recorrente_com_data_fim(usuario_id, categoria_id, conta_id):
    """Cria uma transação recorrente com data_fim."""
    with app.app_context():
        hoje = date.today()
        data_inicio = hoje
        # Definir uma data_fim 6 meses no futuro
        data_fim = hoje + relativedelta(months=6)
        
        transacao_recorrente = TransacaoRecorrente(
            descricao='TESTE_COM_DATA_FIM',
            valor=-100.00,  # Despesa
            data_inicio=data_inicio,
            data_fim=data_fim,
            periodicidade='MENSAL',
            dia_cobranca=data_inicio.day,
            categoria_id=categoria_id,
            conta_id=conta_id,
            usuario_id=usuario_id,
            status=Status.ATIVO.value
        )
        
        db.session.add(transacao_recorrente)
        db.session.commit()
        logger.info(f"Transação recorrente com data_fim criada: {transacao_recorrente.id}")
        logger.info(f"Data início: {data_inicio}, Data fim: {data_fim}")
        
        return transacao_recorrente

def criar_transacao_recorrente_sem_data_fim(usuario_id, categoria_id, conta_id):
    """Cria uma transação recorrente sem data_fim."""
    with app.app_context():
        hoje = date.today()
        data_inicio = hoje
        
        transacao_recorrente = TransacaoRecorrente(
            descricao='TESTE_SEM_DATA_FIM',
            valor=-50.00,  # Despesa
            data_inicio=data_inicio,
            data_fim=None,  # Sem data fim
            periodicidade='MENSAL',
            dia_cobranca=data_inicio.day,
            categoria_id=categoria_id,
            conta_id=conta_id,
            usuario_id=usuario_id,
            status=Status.ATIVO.value
        )
        
        db.session.add(transacao_recorrente)
        db.session.commit()
        logger.info(f"Transação recorrente sem data_fim criada: {transacao_recorrente.id}")
        logger.info(f"Data início: {data_inicio}, Data fim: Nenhuma")
        
        return transacao_recorrente

def gerar_transacoes_e_verificar(transacao_recorrente_id, com_data_fim=True):
    """Gera transações para uma transação recorrente e verifica os resultados."""
    with app.app_context():
        tr = TransacaoRecorrente.query.get(transacao_recorrente_id)
        if not tr:
            logger.error(f"Transação recorrente não encontrada: {transacao_recorrente_id}")
            return
        
        # Contar transações antes da geração
        antes = Transacao.query.filter_by(
            transacao_recorrente_id=transacao_recorrente_id
        ).count()
        
        # Gerar transações pendentes
        if com_data_fim:
            logger.info(f"Gerando transações até data_fim: {tr.data_fim}")
            mensagem = tr.gerar_transacoes_pendentes()
        else:
            # Testando com um período específico para transações sem data_fim
            meses_futuros = 12
            logger.info(f"Gerando transações para os próximos {meses_futuros} meses")
            mensagem = tr.gerar_transacoes_pendentes(meses_futuros=meses_futuros)
        
        # Contar transações depois da geração
        depois = Transacao.query.filter_by(
            transacao_recorrente_id=transacao_recorrente_id
        ).count()
        
        # Obter o status atual da transação recorrente
        status_atual = tr.status
        
        # Obter as datas das transações geradas
        transacoes = Transacao.query.filter_by(
            transacao_recorrente_id=transacao_recorrente_id
        ).order_by(Transacao.data.asc()).all()
        
        data_primeira = transacoes[0].data if transacoes else None
        data_ultima = transacoes[-1].data if transacoes else None
        
        # Mostrar resultados
        logger.info(f"Mensagem de retorno: {mensagem}")
        logger.info(f"Transações antes: {antes}, depois: {depois}, diferença: {depois - antes}")
        logger.info(f"Status atual da transação recorrente: {status_atual}")
        logger.info(f"Data da primeira transação: {data_primeira}")
        logger.info(f"Data da última transação: {data_ultima}")
        
        # Verificações adicionais para transações com data_fim
        if com_data_fim:
            if data_ultima and tr.data_fim:
                # A última transação deve ser no mês da data_fim
                ultimo_mes = date(data_ultima.year, data_ultima.month, 1)
                fim_mes = date(tr.data_fim.year, tr.data_fim.month, 1)
                
                if ultimo_mes == fim_mes:
                    logger.info("✅ SUCESSO: A última transação está no mês da data_fim")
                else:
                    logger.error(f"❌ ERRO: A última transação ({ultimo_mes}) não está no mês da data_fim ({fim_mes})")
                
                # O status deve ser FINALIZADO
                if status_atual == Status.FINALIZADO.value:
                    logger.info("✅ SUCESSO: Status corretamente definido como FINALIZADO")
                else:
                    logger.error(f"❌ ERRO: Status deveria ser FINALIZADO, mas está {status_atual}")
            else:
                logger.error("❌ ERRO: Não foi possível verificar a data_fim")
        else:
            # Para transações sem data_fim, verifique se foram geradas para o período correto
            if data_ultima:
                hoje = date.today()
                data_esperada = hoje + relativedelta(months=12)
                # Use o primeiro dia do mês para comparação
                ultimo_mes = date(data_ultima.year, data_ultima.month, 1)
                mes_esperado = date(data_esperada.year, data_esperada.month, 1)
                
                # A última transação deve estar no mês esperado (hoje + 12 meses)
                if ultimo_mes == mes_esperado:
                    logger.info("✅ SUCESSO: A última transação está no mês esperado (hoje + 12 meses)")
                else:
                    logger.error(f"❌ ERRO: A última transação ({ultimo_mes}) não está no mês esperado ({mes_esperado})")
                
                # O status deve continuar ATIVO
                if status_atual == Status.ATIVO.value:
                    logger.info("✅ SUCESSO: Status corretamente mantido como ATIVO")
                else:
                    logger.error(f"❌ ERRO: Status deveria ser ATIVO, mas está {status_atual}")
            else:
                logger.error("❌ ERRO: Não foram geradas transações")

def main():
    """Função principal que executa os testes."""
    logger.info("Iniciando testes de geração de transações recorrentes")
    
    try:
        # Limpar dados de testes anteriores
        limpar_dados_teste()
        
        # Criar dados de teste
        usuario = criar_usuario_teste()
        categoria = criar_categoria_teste(usuario.id)
        conta = criar_conta_teste(usuario.id)
        
        # Testar transação com data_fim
        logger.info("\n=== TESTE 1: Transação Recorrente COM data_fim ===")
        tr_com_data_fim = criar_transacao_recorrente_com_data_fim(usuario.id, categoria.id, conta.id)
        gerar_transacoes_e_verificar(tr_com_data_fim.id, com_data_fim=True)
        
        # Testar transação sem data_fim
        logger.info("\n=== TESTE 2: Transação Recorrente SEM data_fim ===")
        tr_sem_data_fim = criar_transacao_recorrente_sem_data_fim(usuario.id, categoria.id, conta.id)
        gerar_transacoes_e_verificar(tr_sem_data_fim.id, com_data_fim=False)
        
        logger.info("\nTestes concluídos com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro durante os testes: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
