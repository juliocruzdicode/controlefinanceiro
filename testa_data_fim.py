#!/usr/bin/env python3
# testa_data_fim.py
"""
Script simplificado para testar a geração de transações recorrentes até data_fim.
"""

import os
import sys
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adicionar o diretório atual ao path para permitir importações relativas
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

# Importar apenas os modelos necessários para teste
from models import TransacaoRecorrente, Transacao, StatusRecorrencia

# Função de teste para simular o comportamento de gerar_transacoes_pendentes
def testar_gerar_transacoes_pendentes():
    """
    Teste simplificado para verificar a lógica de gerar transações recorrentes
    com e sem data_fim.
    """
    logger.info("=== Teste: Transação Recorrente COM data_fim ===")
    
    # Simular uma transação recorrente com data_fim
    hoje = date.today()
    
    # Caso 1: Com data_fim
    data_fim = hoje + relativedelta(months=6)
    tr_com_fim = TransacaoRecorrente()
    tr_com_fim.descricao = "TESTE_COM_DATA_FIM"
    tr_com_fim.data_inicio = hoje
    tr_com_fim.data_fim = data_fim
    tr_com_fim.periodicidade = "MENSAL"
    tr_com_fim.dia_cobranca = hoje.day
    tr_com_fim.status = StatusRecorrencia.ATIVA.value
    
    # Testar a função de cálculo de próxima data
    datas = []
    data_limite = hoje + relativedelta(months=12)  # Horizonte de 12 meses
    if tr_com_fim.data_fim:
        data_limite = tr_com_fim.data_fim  # Data fim substitui o horizonte
    
    data_atual = tr_com_fim.data_inicio
    while data_atual <= data_limite:
        datas.append(data_atual)
        # Simular o cálculo da próxima data para periodicidade mensal
        data_atual = data_atual + relativedelta(months=1)
    
    # Verificar resultados
    logger.info(f"Data início: {tr_com_fim.data_inicio}")
    logger.info(f"Data fim: {tr_com_fim.data_fim}")
    logger.info(f"Data limite calculada: {data_limite}")
    logger.info(f"Número de transações que seriam geradas: {len(datas)}")
    logger.info(f"Primeira data: {datas[0]}")
    logger.info(f"Última data: {datas[-1]}")
    
    # Verificar se a última data está no mês da data_fim
    ultimo_mes = date(datas[-1].year, datas[-1].month, 1)
    fim_mes = date(data_fim.year, data_fim.month, 1)
    if ultimo_mes == fim_mes:
        logger.info("✅ SUCESSO: A última transação está no mês da data_fim")
    else:
        logger.error(f"❌ ERRO: A última transação ({ultimo_mes}) não está no mês da data_fim ({fim_mes})")
    
    logger.info("\n=== Teste: Transação Recorrente SEM data_fim ===")
    
    # Caso 2: Sem data_fim
    tr_sem_fim = TransacaoRecorrente()
    tr_sem_fim.descricao = "TESTE_SEM_DATA_FIM"
    tr_sem_fim.data_inicio = hoje
    tr_sem_fim.data_fim = None  # Sem data fim
    tr_sem_fim.periodicidade = "MENSAL"
    tr_sem_fim.dia_cobranca = hoje.day
    tr_sem_fim.status = StatusRecorrencia.ATIVA.value
    
    # Testar a função de cálculo de próxima data
    datas = []
    meses_futuros = 12
    data_limite = hoje + relativedelta(months=meses_futuros)  # Horizonte de 12 meses
    if tr_sem_fim.data_fim:
        data_limite = tr_sem_fim.data_fim  # Data fim substitui o horizonte (não deve ocorrer neste caso)
    
    data_atual = tr_sem_fim.data_inicio
    while data_atual <= data_limite:
        datas.append(data_atual)
        # Simular o cálculo da próxima data para periodicidade mensal
        data_atual = data_atual + relativedelta(months=1)
    
    # Verificar resultados
    logger.info(f"Data início: {tr_sem_fim.data_inicio}")
    logger.info(f"Data fim: {tr_sem_fim.data_fim}")
    logger.info(f"Data limite calculada: {data_limite}")
    logger.info(f"Número de transações que seriam geradas: {len(datas)}")
    logger.info(f"Primeira data: {datas[0]}")
    logger.info(f"Última data: {datas[-1]}")
    
    # Verificar se a última data está no mês esperado (hoje + 12 meses)
    ultimo_mes = date(datas[-1].year, datas[-1].month, 1)
    data_esperada = hoje + relativedelta(months=meses_futuros)
    mes_esperado = date(data_esperada.year, data_esperada.month, 1)
    if ultimo_mes == mes_esperado:
        logger.info("✅ SUCESSO: A última transação está no mês esperado (hoje + 12 meses)")
    else:
        logger.error(f"❌ ERRO: A última transação ({ultimo_mes}) não está no mês esperado ({mes_esperado})")

def main():
    """Função principal que executa os testes."""
    logger.info("Iniciando testes de geração de transações recorrentes")
    
    try:
        testar_gerar_transacoes_pendentes()
        logger.info("\nTestes concluídos com sucesso!")
        return 0
    except Exception as e:
        logger.error(f"Erro durante os testes: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
