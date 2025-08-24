"""
API para verificar e gerenciar as tarefas agendadas
"""
from flask import Blueprint, jsonify, current_app, render_template
from flask_login import login_required, current_user
from models import TransacaoRecorrente, StatusRecorrencia, db
from scheduler_service import scheduler

scheduler_bp = Blueprint('scheduler', __name__)

@scheduler_bp.route('/scheduler')
@login_required
def scheduler_page():
    """Página de gerenciamento do agendador"""
    return render_template('scheduler.html')

@scheduler_bp.route('/api/scheduler/status')
@login_required
def scheduler_status():
    """Retorna o status do agendador"""
    try:
        jobs = []
        for job in scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'next_run_time': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else None,
                'func': str(job.func),
                'trigger': str(job.trigger)
            })
        
        return jsonify({
            'status': 'running' if scheduler.running else 'stopped',
            'jobs': jobs
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scheduler_bp.route('/api/scheduler/run-now')
@login_required
def run_jobs_now():
    """Executa a geração de transações recorrentes imediatamente"""
    try:
        app = current_app._get_current_object()
        
        # Buscar todas as recorrências ativas do usuário atual
        recorrentes_ativas = TransacaoRecorrente.query.filter_by(
            status=StatusRecorrencia.ATIVA,
            user_id=current_user.id
        ).all()
        
        total_recorrentes = len(recorrentes_ativas)
        total_transacoes_geradas = 0
        
        # Processar cada recorrência
        for recorrente in recorrentes_ativas:
            try:
                # No caso do scheduler (que gera automaticamente), não projetamos as transações, criamos direto
                transacoes_geradas = recorrente.gerar_transacoes_pendentes(apenas_projetar=False)
                total_transacoes_geradas += len(transacoes_geradas)
            except Exception as e:
                app.logger.error(f"Erro ao processar recorrência #{recorrente.id}: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f'{total_transacoes_geradas} transação(ões) gerada(s) no total',
            'recorrentes_processadas': total_recorrentes,
            'transacoes_geradas': total_transacoes_geradas
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
