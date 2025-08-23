@app.route('/admin/temas')
@login_required
def admin_temas():
    """Lista de temas do sistema (apenas para admins)"""
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))
    
    temas = Tema.query.all()
    return render_template('admin/temas.html', temas=temas)

@app.route('/admin/novo-tema', methods=['GET', 'POST'])
@login_required
def novo_tema():
    """Adiciona novo tema (apenas para admins)"""
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))
    
    form = TemaForm()
    
    # Valores padrão para as cores
    if request.method == 'GET':
        form.cor_primaria.data = '#007bff'
        form.cor_secundaria.data = '#6c757d'
        form.cor_sucesso.data = '#28a745'
        form.cor_perigo.data = '#dc3545'
        form.cor_alerta.data = '#ffc107'
        form.cor_info.data = '#17a2b8'
        form.cor_fundo.data = '#ffffff'
        form.cor_texto.data = '#212529'
        
        form.cor_primaria_dark.data = '#375a7f'
        form.cor_secundaria_dark.data = '#444444'
        form.cor_sucesso_dark.data = '#00bc8c'
        form.cor_perigo_dark.data = '#e74c3c'
        form.cor_alerta_dark.data = '#f39c12'
        form.cor_info_dark.data = '#3498db'
        form.cor_fundo_dark.data = '#222222'
        form.cor_texto_dark.data = '#ffffff'
    
    if form.validate_on_submit():
        # Verificar se nome já existe
        tema_existente = Tema.query.filter_by(nome=form.nome.data).first()
        if tema_existente:
            flash(f'Já existe um tema com o nome "{form.nome.data}"', 'danger')
            return render_template('admin/novo_tema.html', form=form)
        
        # Criar novo tema
        tema = Tema(
            nome=form.nome.data,
            descricao=form.descricao.data,
            is_default=form.is_default.data,
            cor_primaria=form.cor_primaria.data,
            cor_secundaria=form.cor_secundaria.data,
            cor_sucesso=form.cor_sucesso.data,
            cor_perigo=form.cor_perigo.data,
            cor_alerta=form.cor_alerta.data,
            cor_info=form.cor_info.data,
            cor_fundo=form.cor_fundo.data,
            cor_texto=form.cor_texto.data,
            cor_primaria_dark=form.cor_primaria_dark.data,
            cor_secundaria_dark=form.cor_secundaria_dark.data,
            cor_sucesso_dark=form.cor_sucesso_dark.data,
            cor_perigo_dark=form.cor_perigo_dark.data,
            cor_alerta_dark=form.cor_alerta_dark.data,
            cor_info_dark=form.cor_info_dark.data,
            cor_fundo_dark=form.cor_fundo_dark.data,
            cor_texto_dark=form.cor_texto_dark.data
        )
        
        try:
            db.session.add(tema)
            
            # Se for tema padrão, desmarcar todos os outros
            if form.is_default.data:
                Tema.query.filter(Tema.id != tema.id).update({Tema.is_default: False})
            
            db.session.commit()
            flash('Tema criado com sucesso!', 'success')
            return redirect(url_for('admin_temas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar tema: {str(e)}', 'danger')
    
    return render_template('admin/novo_tema.html', form=form)

@app.route('/admin/editar-tema/<int:tema_id>', methods=['GET', 'POST'])
@login_required
def editar_tema(tema_id):
    """Edita um tema existente (apenas para admins)"""
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))
    
    tema = Tema.query.get_or_404(tema_id)
    form = TemaForm(obj=tema)
    
    if form.validate_on_submit():
        # Verificar se nome já existe e não é o atual
        tema_existente = Tema.query.filter(
            Tema.nome == form.nome.data,
            Tema.id != tema_id
        ).first()
        
        if tema_existente:
            flash(f'Já existe um tema com o nome "{form.nome.data}"', 'danger')
            return render_template('admin/editar_tema.html', form=form, tema=tema)
        
        # Atualizar tema
        tema.nome = form.nome.data
        tema.descricao = form.descricao.data
        tema.is_default = form.is_default.data
        tema.cor_primaria = form.cor_primaria.data
        tema.cor_secundaria = form.cor_secundaria.data
        tema.cor_sucesso = form.cor_sucesso.data
        tema.cor_perigo = form.cor_perigo.data
        tema.cor_alerta = form.cor_alerta.data
        tema.cor_info = form.cor_info.data
        tema.cor_fundo = form.cor_fundo.data
        tema.cor_texto = form.cor_texto.data
        tema.cor_primaria_dark = form.cor_primaria_dark.data
        tema.cor_secundaria_dark = form.cor_secundaria_dark.data
        tema.cor_sucesso_dark = form.cor_sucesso_dark.data
        tema.cor_perigo_dark = form.cor_perigo_dark.data
        tema.cor_alerta_dark = form.cor_alerta_dark.data
        tema.cor_info_dark = form.cor_info_dark.data
        tema.cor_fundo_dark = form.cor_fundo_dark.data
        tema.cor_texto_dark = form.cor_texto_dark.data
        
        try:
            # Se for tema padrão, desmarcar todos os outros
            if form.is_default.data:
                Tema.query.filter(Tema.id != tema.id).update({Tema.is_default: False})
            
            db.session.commit()
            flash('Tema atualizado com sucesso!', 'success')
            return redirect(url_for('admin_temas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar tema: {str(e)}', 'danger')
    
    return render_template('admin/editar_tema.html', form=form, tema=tema)

@app.route('/admin/excluir-tema/<int:tema_id>', methods=['POST'])
@login_required
def excluir_tema(tema_id):
    """Exclui um tema (apenas para admins)"""
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))
    
    tema = Tema.query.get_or_404(tema_id)
    
    # Não permitir excluir o tema padrão
    if tema.is_default:
        flash('Não é possível excluir o tema padrão', 'danger')
        return redirect(url_for('admin_temas'))
    
    # Não permitir excluir tema em uso
    if Usuario.query.filter_by(tema_id=tema_id).count() > 0:
        flash('Não é possível excluir um tema que está sendo usado por usuários', 'danger')
        return redirect(url_for('admin_temas'))
    
    try:
        db.session.delete(tema)
        db.session.commit()
        flash('Tema excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir tema: {str(e)}', 'danger')
    
    return redirect(url_for('admin_temas'))
