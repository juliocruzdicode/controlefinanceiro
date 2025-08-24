"""
Serviço para agendamento de tarefas automatizadas
"""
from flask_apscheduler import APScheduler
from flask import current_app
from sqlalchemy import and_
from app import db
from app.models.recorrente import TransacaoRecorrente, StatusRecorrencia
import logging

# Criar instância do scheduler
scheduler = APScheduler()

def init_scheduler(app):
    """Inicializa o agendador de tarefas"""
    # Configuração do scheduler
    app.config['SCHEDULER_API_ENABLED'] = True
    
    # Inicializar o scheduler
    scheduler.init_app(app)
    scheduler.start()
    
    # Registrar tarefas agendadas
    with app.app_context():
        # Executar diariamente às 00:01
        scheduler.add_job(
            id='gerar_transacoes_recorrentes',
            func=gerar_todas_transacoes_recorrentes,
            trigger='cron',
            hour=0,
            minute=1,
            replace_existing=True
        )
        
        app.logger.info("✅ Agendador de tarefas inicializado")
        app.logger.info("✅ Tarefa de geração de transações recorrentes agendada para execução diária às 00:01")

def gerar_todas_transacoes_recorrentes():
    """Gera todas as transações pendentes de todas as recorrências ativas"""
    app = current_app._get_current_object()
    
    with app.app_context():
        try:
            app.logger.info("🔄 Iniciando geração automática de transações recorrentes")
            
            # Buscar todas as recorrências ativas
            recorrentes_ativas = TransacaoRecorrente.query.filter_by(
                status=StatusRecorrencia.ATIVA
            ).all()
            
            total_recorrentes = len(recorrentes_ativas)
            total_transacoes_geradas = 0
            
            app.logger.info(f"📊 Processando {total_recorrentes} transações recorrentes ativas")
            
            # Processar cada recorrência
            for recorrente in recorrentes_ativas:
                try:
                    transacoes_geradas = recorrente.gerar_transacoes_pendentes()
                    total_transacoes_geradas += len(transacoes_geradas)
                    
                    if len(transacoes_geradas) > 0:
                        app.logger.info(f"✅ Recorrência #{recorrente.id} ({recorrente.descricao}): {len(transacoes_geradas)} transação(ões) gerada(s)")
                except Exception as e:
                    app.logger.error(f"❌ Erro ao processar recorrência #{recorrente.id}: {str(e)}")
            
            app.logger.info(f"✅ Geração automática concluída: {total_transacoes_geradas} transação(ões) gerada(s) no total")
            
            return {
                'recorrentes_processadas': total_recorrentes,
                'transacoes_geradas': total_transacoes_geradas
            }
            
        except Exception as e:
            app.logger.error(f"❌ Erro na geração automática de transações recorrentes: {str(e)}")
            return {'error': str(e)}
