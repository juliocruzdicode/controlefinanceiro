from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, FormaPagamento
import re

admin_payment_bp = Blueprint('admin_payment', __name__)


@admin_payment_bp.route('/admin/formas-pagamento')
@login_required
def listar_formas_pagamento():
    # Admin vê todas as formas (globais e específicas); usuário vê apenas as suas + globais
    if current_user.is_admin:
        formas = FormaPagamento.query.order_by(FormaPagamento.user_id.is_(None).desc(), FormaPagamento.nome).all()
    else:
        formas = FormaPagamento.get_for_user(current_user.id)
    return render_template('admin/formas_pagamento.html', formas=formas)


@admin_payment_bp.route('/admin/formas-pagamento/nova', methods=['GET', 'POST'])
@login_required
def nova_forma_pagamento():
    # Qualquer usuário autenticado pode criar suas formas
    if request.method == 'POST':
        nome = request.form.get('nome')
        if not nome:
            flash('Nome é obrigatório.', 'danger')
            return redirect(url_for('admin_payment.nova_forma_pagamento'))
        # Admins criam formas globais por padrão; usuários criam formas associadas a si mesmos
        if current_user.is_admin and request.form.get('global'):
            user_id = None
        else:
            user_id = current_user.id
        # Gerar slug amigável automaticamente
        base = re.sub(r'[^a-z0-9]+', '_', nome.lower()).strip('_')
        if user_id is None:
            candidate = base
            # garantir unicidade entre slugs globais
            i = 0
            while FormaPagamento.query.filter_by(user_id=None, slug=candidate).first():
                i += 1
                candidate = f"{base}_{i}"
            slug_final = candidate
        else:
            # para formas do usuário, sufixar com -u<id> e garantir unicidade
            candidate = f"{base}-u{user_id}"
            i = 0
            while FormaPagamento.query.filter_by(user_id=user_id, slug=candidate).first():
                i += 1
                candidate = f"{base}-u{user_id}_{i}"
            slug_final = candidate
        f = FormaPagamento(nome=nome, slug=slug_final, user_id=user_id)
        db.session.add(f)
        db.session.commit()
        flash('Forma de pagamento criada.', 'success')
        return redirect(url_for('admin_payment.listar_formas_pagamento'))
    return render_template('admin/nova_forma_pagamento.html')


@admin_payment_bp.route('/admin/formas-pagamento/editar/<int:forma_id>', methods=['GET', 'POST'])
@login_required
def editar_forma_pagamento(forma_id):
    forma = FormaPagamento.query.get_or_404(forma_id)
    # Apenas admin ou dono podem editar
    if not (current_user.is_admin or (forma.user_id and forma.user_id == current_user.id)):
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        novo_nome = request.form.get('nome') or forma.nome
        # Regenerar slug automaticamente a partir do novo nome
        if novo_nome != forma.nome:
            base = re.sub(r'[^a-z0-9]+', '_', novo_nome.lower()).strip('_')
            if forma.user_id is None:
                candidate = base
                i = 0
                while FormaPagamento.query.filter(FormaPagamento.id != forma.id, FormaPagamento.user_id.is_(None), FormaPagamento.slug==candidate).first():
                    i += 1
                    candidate = f"{base}_{i}"
                forma.slug = candidate
            else:
                uid = forma.user_id
                candidate = f"{base}-u{uid}"
                i = 0
                while FormaPagamento.query.filter(FormaPagamento.id != forma.id, FormaPagamento.user_id==uid, FormaPagamento.slug==candidate).first():
                    i += 1
                    candidate = f"{base}-u{uid}_{i}"
                forma.slug = candidate
        forma.nome = novo_nome
        forma.ativa = bool(request.form.get('ativa'))
        db.session.commit()
        flash('Forma de pagamento atualizada.', 'success')
        return redirect(url_for('admin_payment.listar_formas_pagamento'))
    return render_template('admin/editar_forma_pagamento.html', forma=forma)


@admin_payment_bp.route('/admin/formas-pagamento/excluir/<int:forma_id>', methods=['POST'])
@login_required
def excluir_forma_pagamento(forma_id):
    forma = FormaPagamento.query.get_or_404(forma_id)
    # Apenas admin ou dono podem excluir
    if not (current_user.is_admin or (forma.user_id and forma.user_id == current_user.id)):
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('dashboard'))
    db.session.delete(forma)
    db.session.commit()
    flash('Forma de pagamento excluída.', 'success')
    return redirect(url_for('admin_payment.listar_formas_pagamento'))
