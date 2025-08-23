"""
Módulo de enumerações para o sistema
"""
from enum import Enum

class TipoTransacao(Enum):
    RECEITA = "receita"
    DESPESA = "despesa"

class TipoConta(Enum):
    CORRENTE = "corrente"
    POUPANCA = "poupanca"
    CARTAO_CREDITO = "cartao_credito"
    CARTAO_DEBITO = "cartao_debito"
    DINHEIRO = "dinheiro"
    INVESTIMENTO = "investimento"
    OUTROS = "outros"

class TipoRecorrencia(Enum):
    UNICA = "unica"           # Transação única (padrão)
    SEMANAL = "semanal"       # A cada 7 dias
    QUINZENAL = "quinzenal"   # A cada 15 dias
    MENSAL = "mensal"         # Mensalmente
    TRIMESTRAL = "trimestral" # A cada 3 meses
    SEMESTRAL = "semestral"   # A cada 6 meses
    ANUAL = "anual"           # Anualmente

class StatusRecorrencia(Enum):
    ATIVA = "ativa"           # Gerando transações
    PAUSADA = "pausada"       # Temporariamente pausada
    FINALIZADA = "finalizada" # Concluída ou cancelada
