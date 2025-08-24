"""
Serviço para agendamento de tarefas automatizadas
"""
from flask_apscheduler import APScheduler
from flask import current_app
import logging

# Criar instância do scheduler
scheduler = APScheduler()

def init_scheduler(app):
    """Inicializa o agendador de tarefas"""
    try:
        # Importar os modelos dentro do contexto da aplicação
        from models import TransacaoRecorrente, StatusRecorrencia
        
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
                func=lambda: gerar_todas_transacoes_recorrentes(app),
                trigger='cron',
                hour=0,
                minute=1,
                replace_existing=True
            )
            
            # Também adicionar um job para executar a cada inicialização da aplicação
            scheduler.add_job(
                id='gerar_transacoes_inicializacao',
                func=lambda: gerar_todas_transacoes_recorrentes(app),
                trigger='date',
                run_date=scheduler.app.datetime.datetime.now() + scheduler.app.datetime.timedelta(seconds=30),
                replace_existing=True
            )
            
            app.logger.info("✅ Agendador de tarefas inicializado")
            app.logger.info("✅ Tarefa de geração de transações recorrentes agendada para execução diária às 00:01")
            app.logger.info("✅ Tarefa de geração de transações recorrentes agendada para execução 30 segundos após a inicialização")
    except Exception as e:
        app.logger.error(f"❌ Erro ao inicializar o agendador de tarefas: {str(e)}")

def gerar_todas_transacoes_recorrentes(app):
    """Gera todas as transações pendentes de todas as recorrências ativas"""
    with app.app_context():
        try:
            from models import TransacaoRecorrente, StatusRecorrencia, db
            
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
