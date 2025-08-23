"""
Inicialização do serviço de autenticação e das rotas de autenticação
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.forms.auth_forms import LoginForm, RegistrationForm, PasswordResetRequestForm, PasswordResetForm
from app.services.user_service import UsuarioService
from app.services.email_service import EmailService
from app.services.google_auth_service import GoogleAuthService

# Cria o blueprint de autenticação
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Rota para login de usuários"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Autentica o usuário
        usuario = UsuarioService.autenticar_usuario(form.email.data, form.senha.data)
        
        if usuario:
            # Faz login e redireciona
            login_user(usuario, remember=form.lembrar.data)
            
            # Redireciona para a página solicitada antes do login (se houver)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            return redirect(url_for('main.dashboard'))
        else:
            flash('Email ou senha inválidos.', 'danger')
    
    # Verifica se as configurações do Google estão disponíveis
    has_google_auth = current_app.config.get('GOOGLE_CLIENT_ID') and current_app.config.get('GOOGLE_CLIENT_SECRET')
    
    return render_template('auth/login.html', form=form, title='Login', has_google_auth=has_google_auth)

@auth_bp.route('/logout')
def logout():
    """Rota para logout de usuários"""
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Rota para registro de novos usuários"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Cria o novo usuário
        usuario = UsuarioService.criar_usuario(
            nome=form.nome.data,
            email=form.email.data,
            senha=form.senha.data,
            nome_completo=form.nome_completo.data
        )
        
        if usuario:
            # Gera token de verificação de email
            token = UsuarioService.gerar_token_verificacao_email(usuario.id)
            
            # Envia email de verificação
            EmailService.enviar_email_verificacao(usuario.email, usuario.nome, token)
            
            flash('Conta criada com sucesso! Um email de verificação foi enviado.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Este email já está em uso.', 'danger')
    
    # Verifica se as configurações do Google estão disponíveis
    has_google_auth = current_app.config.get('GOOGLE_CLIENT_ID') and current_app.config.get('GOOGLE_CLIENT_SECRET')
    
    return render_template('auth/register.html', form=form, title='Registro', has_google_auth=has_google_auth)

@auth_bp.route('/verify/<token>')
def verify_email(token):
    """Rota para verificação de email"""
    usuario = UsuarioService.verificar_email(token)
    
    if usuario:
        flash('Email verificado com sucesso!', 'success')
        # Faz login do usuário após verificação
        login_user(usuario)
        return redirect(url_for('main.dashboard'))
    
    flash('O link de verificação é inválido ou expirou.', 'danger')
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    """Rota para solicitar redefinição de senha"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        usuario = UsuarioService.obter_usuario_por_email(form.email.data)
        
        if usuario:
            # Gera token de redefinição
            token = UsuarioService.gerar_token_redefinicao_senha(usuario.email)
            
            # Envia email de redefinição
            EmailService.enviar_email_redefinicao_senha(usuario.email, usuario.nome, token)
        
        # Mesmo que o email não exista, mostra mensagem de sucesso por segurança
        flash('Um email com instruções para redefinir sua senha foi enviado, se o endereço estiver registrado.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html', form=form, title='Redefinir Senha')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Rota para redefinir senha"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Verifica se o token é válido
    usuario = UsuarioService.verificar_token_redefinicao(token)
    if not usuario:
        flash('O link de redefinição de senha é inválido ou expirou.', 'danger')
        return redirect(url_for('auth.login'))
    
    form = PasswordResetForm()
    if form.validate_on_submit():
        # Redefine a senha
        if UsuarioService.redefinir_senha(token, form.senha.data):
            flash('Sua senha foi redefinida com sucesso!', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Ocorreu um erro. Por favor, tente novamente.', 'danger')
            return redirect(url_for('auth.reset_password_request'))
    
    return render_template('auth/reset_password.html', form=form, title='Redefinir Senha')

# Rotas para autenticação com Google
@auth_bp.route('/login/google')
def login_google():
    """Rota para iniciar o fluxo de autenticação com Google"""
    # Verifica se as configurações do Google estão disponíveis
    if not current_app.config.get('GOOGLE_CLIENT_ID') or not current_app.config.get('GOOGLE_CLIENT_SECRET'):
        flash('A autenticação com Google não está configurada.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Gera URL de autenticação do Google
    auth_url = GoogleAuthService.get_auth_url()
    
    # Redireciona para o Google
    return redirect(auth_url)

@auth_bp.route('/callback')
def callback():
    """Rota para callback do Google OAuth"""
    # Verifica se as configurações do Google estão disponíveis
    if not current_app.config.get('GOOGLE_CLIENT_ID') or not current_app.config.get('GOOGLE_CLIENT_SECRET'):
        flash('A autenticação com Google não está configurada.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Processa o callback
    usuario = GoogleAuthService.process_callback(request.url)
    
    if not usuario:
        flash('Falha na autenticação com Google. Por favor, tente novamente.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Sucesso na autenticação
    flash(f'Bem-vindo, {usuario.nome}!', 'success')
    return redirect(url_for('main.dashboard'))
