from flask import Blueprint, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Usuario
from utils import criar_categorias_padrao

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/adicionar-categorias-padrao/<int:user_id>')
@login_required
def adicionar_categorias_padrao(user_id):
    """Adiciona categorias padrão a um usuário existente"""
    # Verificar se é administrador
    if not current_user.is_admin:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Verificar se o usuário existe
    usuario = Usuario.query.get(user_id)
    if not usuario:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('admin.gerenciar_usuarios'))
    
    # Adicionar categorias padrão
    if criar_categorias_padrao(user_id):
        flash(f'Categorias padrão adicionadas para {usuario.username}.', 'success')
    else:
        flash(f'Erro ao adicionar categorias padrão para {usuario.username}.', 'danger')
    
    return redirect(url_for('admin.gerenciar_usuarios'))

@admin_bp.route('/admin/adicionar-categorias-padrao-todos')
@login_required
def adicionar_categorias_padrao_todos():
    """Adiciona categorias padrão para todos os usuários"""
    # Verificar se é administrador
    if not current_user.is_admin:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Buscar todos os usuários
    usuarios = Usuario.query.all()
    count_success = 0
    count_failed = 0
    
    for usuario in usuarios:
        if criar_categorias_padrao(usuario.id):
            count_success += 1
        else:
            count_failed += 1
    
    if count_failed == 0:
        flash(f'Categorias padrão adicionadas para {count_success} usuários.', 'success')
    else:
        flash(f'Categorias adicionadas para {count_success} usuários, falha em {count_failed}.', 'warning')
    
    return redirect(url_for('admin.index'))
