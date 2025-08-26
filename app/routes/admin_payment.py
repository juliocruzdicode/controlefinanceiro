from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, FormaPagamento

admin_payment_bp = Blueprint('admin_payment', __name__)


@admin_payment_bp.route('/admin/formas-pagamento')
@login_required
def listar_formas_pagamento():
    if not current_user.is_admin:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('dashboard'))
    formas = FormaPagamento.query.order_by(FormaPagamento.user_id.is_(None).desc(), FormaPagamento.nome).all()
    return render_template('admin/formas_pagamento.html', formas=formas)


@admin_payment_bp.route('/admin/formas-pagamento/nova', methods=['GET', 'POST'])
@login_required
def nova_forma_pagamento():
    if not current_user.is_admin:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        nome = request.form.get('nome')
        slug = request.form.get('slug')
        if not nome or not slug:
            flash('Nome e slug são obrigatórios.', 'danger')
            return redirect(url_for('admin_payment.nova_forma_pagamento'))
        f = FormaPagamento(nome=nome, slug=slug, user_id=None)
        db.session.add(f)
        db.session.commit()
        flash('Forma de pagamento criada.', 'success')
        return redirect(url_for('admin_payment.listar_formas_pagamento'))
    return render_template('admin/nova_forma_pagamento.html')


@admin_payment_bp.route('/admin/formas-pagamento/editar/<int:forma_id>', methods=['GET', 'POST'])
@login_required
def editar_forma_pagamento(forma_id):
    if not current_user.is_admin:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('dashboard'))
    forma = FormaPagamento.query.get_or_404(forma_id)
    if request.method == 'POST':
        forma.nome = request.form.get('nome') or forma.nome
        forma.slug = request.form.get('slug') or forma.slug
        forma.ativa = bool(request.form.get('ativa'))
        db.session.commit()
        flash('Forma de pagamento atualizada.', 'success')
        return redirect(url_for('admin_payment.listar_formas_pagamento'))
    return render_template('admin/editar_forma_pagamento.html', forma=forma)


@admin_payment_bp.route('/admin/formas-pagamento/excluir/<int:forma_id>', methods=['POST'])
@login_required
def excluir_forma_pagamento(forma_id):
    if not current_user.is_admin:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('dashboard'))
    forma = FormaPagamento.query.get_or_404(forma_id)
    db.session.delete(forma)
    db.session.commit()
    flash('Forma de pagamento excluída.', 'success')
    return redirect(url_for('admin_payment.listar_formas_pagamento'))
