from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from urllib.parse import urlparse as url_parse
from models import db, Transacao, Categoria, TipoTransacao, TransacaoRecorrente, TipoRecorrencia, StatusRecorrencia, Conta, TipoConta, Tag, Usuario, Tema, FormaPagamento
from forms import TransacaoForm, CategoriaForm, TransacaoRecorrenteForm, ContaForm, LoginForm, MFAForm, BackupCodeForm, SetupMFAForm, RegisterForm, ChangePasswordForm, ForgotPasswordForm, ResetPasswordForm, TemaForm, UserThemeForm, CompletarCadastroForm
from config import Config
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
from sqlalchemy import func, or_
from sqlalchemy.exc import ProgrammingError, OperationalError
import qrcode
import io
import base64
import os
from utils import criar_categorias_padrao
import json
from pathlib import Path

# Cache for cidades list
_CIDADES_CACHE = None

def _load_cidades():
    global _CIDADES_CACHE
    if _CIDADES_CACHE is not None:
        return _CIDADES_CACHE
    try:
        path = Path(__file__).parent / 'data' / 'cidades.json'
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                _CIDADES_CACHE = json.load(f)
        else:
            _CIDADES_CACHE = []
    except Exception:
        _CIDADES_CACHE = []
    return _CIDADES_CACHE

# Carrega as variáveis de ambiente do arquivo .env
from dotenv import load_dotenv
load_dotenv()

# Importação opcional do pandas
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    logging.warning('Pandas não instalado - algumas funcionalidades de análise estarão limitadas')

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Register admin_payment blueprint if available (safe import)
try:
    from app.routes.admin_payment import admin_payment_bp
    app.register_blueprint(admin_payment_bp)
except Exception:
    # blueprint registration may fail in some environments; ignore to avoid startup crash
    pass

# Configuração da sessão para durar mais tempo
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config['SESSION_TYPE'] = 'filesystem'

# Centralizar configuração do horizonte de projeções (meses)
# MESES_FUTUROS_DEFAULT: valor padrão usado quando não fornecido via request
# MESES_FUTUROS_MAX: limite máximo permitido
app.config.setdefault('MESES_FUTUROS_DEFAULT', 24)
app.config.setdefault('MESES_FUTUROS_MAX', 36)


def obter_meses_futuros_from_request(param_name: str = 'meses', default: int | None = None) -> int:
    """Lê o parâmetro de meses da request e aplica valores padrão e limites a partir do app.config.

    Deve ser chamado dentro de um contexto de request.
    """
    if default is None:
        default = app.config.get('MESES_FUTUROS_DEFAULT', 36)
    try:
        meses = request.args.get(param_name, default, type=int)
    except Exception:
        meses = default
    if meses is None:
        meses = default
    # Garantir mínimo 1
    if meses < 1:
        meses = 1
    max_meses = app.config.get('MESES_FUTUROS_MAX', 60)
    if meses > max_meses:
        meses = max_meses
    return meses

# Debug - Verificar se as variáveis de ambiente estão carregadas (usando logger)
app.logger.debug('GOOGLE_CLIENT_ID: %s', os.environ.get('GOOGLE_CLIENT_ID'))
app.logger.debug('GOOGLE_CLIENT_SECRET: %s', os.environ.get('GOOGLE_CLIENT_SECRET'))
app.logger.debug("app.config['GOOGLE_CLIENT_ID']: %s", app.config.get('GOOGLE_CLIENT_ID'))
app.logger.debug("app.config['GOOGLE_CLIENT_SECRET']: %s", app.config.get('GOOGLE_CLIENT_SECRET'))

# Configuração do Flask-Mail
mail = Mail(app)

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# Disponibiliza now() nos templates (usar {{ now().year }})
@app.context_processor
def inject_now():
    from datetime import datetime
    return {'now': datetime.utcnow}

# Disponibiliza variáveis de tema para os templates
@app.context_processor
def inject_theme():
    tema = None
    is_dark_mode = False
    
    # Se o usuário estiver autenticado, pegar suas preferências
    if current_user.is_authenticated:
        # Verificar se o usuário tem um tema definido
        if current_user.tema_id:
            tema = Tema.query.get(current_user.tema_id)
        is_dark_mode = current_user.dark_mode
    
    # Se não tiver tema definido, usar o padrão
    if not tema:
        tema = Tema.get_default()
    
    # Pegar as cores corretas com base no modo
    if is_dark_mode:
        cores = {
            'primary': tema.cor_primaria_dark,
            'secondary': tema.cor_secundaria_dark,
            'success': tema.cor_sucesso_dark,
            'danger': tema.cor_perigo_dark,
            'warning': tema.cor_alerta_dark,
            'info': tema.cor_info_dark,
            'background': tema.cor_fundo_dark,
            'text': tema.cor_texto_dark
        }
    else:
        cores = {
            'primary': tema.cor_primaria,
            'secondary': tema.cor_secundaria,
            'success': tema.cor_sucesso,
            'danger': tema.cor_perigo,
            'warning': tema.cor_alerta,
            'info': tema.cor_info,
            'background': tema.cor_fundo,
            'text': tema.cor_texto
        }
    
    return {
        'tema': tema,
        'dark_mode': is_dark_mode,
        'cores': cores
    }

# Health check endpoint para Docker
@app.route('/health')
def health_check():
    """Endpoint de health check para monitoramento"""
    try:
        # Testa a conexão com o banco
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e), 'timestamp': datetime.now().isoformat()}, 500

@login_manager.user_loader
def load_user(user_id):
    """Carrega usuário pela ID"""
    return Usuario.query.get(int(user_id))

def send_verification_email(user):
    """Envia email de verificação para o usuário"""
    try:
        # Gerar token primeiro
        token = user.generate_email_verification_token()
        db.session.commit()
        
        verification_url = url_for('confirm_email', token=token, _external=True)
        
        # if not app.config['MAIL_USERNAME']:
        #     # Modo de desenvolvimento - apenas log
        #     print(f"\n{'='*60}")
        #     print(f"📧 EMAIL DE VERIFICAÇÃO PARA: {user.email}")
        #     print(f"👤 USUÁRIO: {user.username}")
        #     print(f"🔗 LINK DE CONFIRMAÇÃO:")
        #     print(f"{verification_url}")
        #     print(f"{'='*60}\n")
        #     return True
        
        msg = Message(
            'Confirme seu email - Controle Financeiro',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email]
        )
        
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #007bff;">Bem-vindo ao Controle Financeiro!</h2>
            
            <p>Olá <strong>{user.username}</strong>,</p>
            
            <p>Obrigado por se registrar! Para ativar sua conta, clique no link abaixo:</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_url}" 
                   style="background-color: #007bff; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; font-weight: bold;">
                    Confirmar Email
                </a>
            </div>
            
            <p>Ou copie e cole este link no seu navegador:</p>
            <p style="word-break: break-all; color: #666;">{verification_url}</p>
            
            <p><small>Este link expira em 24 horas.</small></p>
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #666; font-size: 12px;">
                Se você não se registrou em nosso sistema, ignore este email.
            </p>
        </div>
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        app.logger.error('Erro ao enviar email: %s', e)
        # Em caso de erro, mostrar link no console como fallback
        try:
            token = user.generate_email_verification_token()
            db.session.commit()
            verification_url = url_for('confirm_email', token=token, _external=True)
            app.logger.info('FALLBACK - Link de verificacao para %s: %s', user.email, verification_url)
            return True
        except Exception as fallback_error:
            app.logger.error('Erro no fallback: %s', fallback_error)
            return False

def send_password_reset_email(user):
    """Envia email com link para redefinição de senha"""
    try:
        # Gera um novo token
        token = user.generate_password_reset_token()
        db.session.commit()
        
        # Cria a URL de redefinição
        reset_url = url_for('reset_password', token=token, _external=True)
        
        msg = Message(
            'Redefinição de Senha - Controle Financeiro',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email]
        )
        
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #007bff;">Redefinição de Senha</h2>
            
            <p>Olá <strong>{user.username}</strong>,</p>
            
            <p>Recebemos uma solicitação para redefinir sua senha. Clique no link abaixo para definir uma nova senha:</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" 
                   style="background-color: #007bff; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; font-weight: bold;">
                    Redefinir Senha
                </a>
            </div>
            
            <p>Ou copie e cole este link no seu navegador:</p>
            <p style="word-break: break-all; color: #666;">{reset_url}</p>
            
            <p><small>Este link expira em 24 horas.</small></p>
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #666; font-size: 12px;">
                Se você não solicitou esta redefinição, ignore este email. Sua senha atual continuará funcionando normalmente.
            </p>
        </div>
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        app.logger.error('Erro ao enviar email de redefinicao: %s', e)
        # Em caso de erro, mostrar link no console como fallback
        try:
            token = user.generate_password_reset_token()
            db.session.commit()
            reset_url = url_for('reset_password', token=token, _external=True)
            app.logger.info('FALLBACK - Link de redefinicao para %s: %s', user.email, reset_url)
            return True
        except Exception as fallback_error:
            app.logger.error('Erro no fallback: %s', fallback_error)
            return False

# === ROTAS DE AUTENTICAÇÃO ===

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login com verificação por email"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Buscar usuário pelo email
        user = Usuario.query.filter_by(email=form.email.data).first()
        
        if user is None or not user.check_password(form.password.data):
            # Registrar tentativa falhada se usuário existe
            if user:
                user.record_failed_login()
            flash('Email ou senha inválidos', 'danger')
            return redirect(url_for('login'))
        
        # Verificar se conta está bloqueada
        if user.is_account_locked():
            flash('Conta bloqueada devido a muitas tentativas de login. Tente novamente mais tarde.', 'danger')
            return redirect(url_for('login'))
        
        if not user.is_active:
            flash('Conta desativada. Entre em contato com o administrador.', 'danger')
            return redirect(url_for('login'))
        
        # Verificar se email foi confirmado
        if not user.email_verified:
            flash('Por favor, confirme seu email antes de fazer login. Verifique sua caixa de entrada.', 'warning')
            return render_template('auth/email_verification_required.html', user=user)
        
        # Se MFA não está habilitado, login direto
        if not user.mfa_enabled:
            login_user(user, remember=form.remember_me.data)
            user.record_successful_login()
            
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('dashboard')
            
            flash(f'Bem-vindo, {user.username}!', 'success')
            return redirect(next_page)
        
        # MFA habilitado - armazenar dados na sessão
        session['pre_2fa_user_id'] = user.id
        session['remember_me'] = form.remember_me.data
        return redirect(url_for('verify_mfa'))
    
    # Verifica se as configurações do Google estão disponíveis
    has_google_auth = bool(app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'))
    
    return render_template('auth/login.html', form=form, has_google_auth=has_google_auth)

@app.route('/login/google')
def login_google():
    """Rota para iniciar o fluxo de autenticação com Google para login"""
    return _google_auth('login')

@app.route('/register/google')
def register_google():
    """Rota para iniciar o fluxo de autenticação com Google para registro"""
    return _google_auth('register')

def _google_auth(auth_type):
    """Função auxiliar para autenticação com Google (login ou registro)"""
    # Verificar se as configurações do Google estão disponíveis
    app.logger.debug('google_auth: GOOGLE_CLIENT_ID: %s', app.config.get('GOOGLE_CLIENT_ID'))
    app.logger.debug('google_auth: GOOGLE_CLIENT_SECRET: %s', app.config.get('GOOGLE_CLIENT_SECRET'))
    
    if not app.config.get('GOOGLE_CLIENT_ID') or not app.config.get('GOOGLE_CLIENT_SECRET'):
        app.logger.debug('As configuracoes do Google nao estao disponiveis')
        flash('A autenticação com Google não está configurada.', 'danger')
        return redirect(url_for('login' if auth_type == 'login' else 'register'))
    
    try:
        # Configuração do cliente OAuth
        from authlib.integrations.flask_client import OAuth
        
        # Inicializa o cliente OAuth
        oauth = OAuth(app)
        
        # Registra o provedor Google
        google = oauth.register(
            name='google',
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            server_metadata_url=app.config['GOOGLE_DISCOVERY_URL'],
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
        
        # Gera um nonce e armazena na sessão
        import secrets
        from flask import session
        nonce = secrets.token_urlsafe(16)
        session['google_auth_nonce'] = nonce
        
        # Armazena o tipo de autenticação na sessão (login ou registro)
        session['google_auth_type'] = auth_type
        
        # Inicia o fluxo de autenticação
        redirect_uri = app.config.get('GOOGLE_REDIRECT_URI')
        app.logger.debug('Redirecionando para %s', redirect_uri)
        app.logger.debug('Nonce gerado: %s', nonce)
        app.logger.debug('Tipo de autenticacao: %s', auth_type)
        return google.authorize_redirect(redirect_uri, nonce=nonce)
    except Exception as e:
        app.logger.error('Erro na autenticacao Google: %s', str(e))
        flash(f'Erro na autenticação com Google: {str(e)}', 'danger')
        return redirect(url_for('login' if auth_type == 'login' else 'register'))

@app.route('/callback')
def callback():
    """Rota para callback do Google OAuth (login ou registro)"""
    # Verificar se as configurações do Google estão disponíveis
    if not app.config.get('GOOGLE_CLIENT_ID') or not app.config.get('GOOGLE_CLIENT_SECRET'):
        flash('A autenticação com Google não está configurada.', 'danger')
        return redirect(url_for('login'))
    
    try:
        # Importar bibliotecas necessárias
        from authlib.integrations.flask_client import OAuth
        import json

        # Log de diagnóstico
        client_id = app.config.get('GOOGLE_CLIENT_ID', '')
        client_secret = app.config.get('GOOGLE_CLIENT_SECRET', '')
        redirect_uri = app.config.get('GOOGLE_REDIRECT_URI', '')

        app.logger.debug(client_id[:10] + '...' if client_id else 'GOOGLE_CLIENT_ID não definido')
        app.logger.debug(client_secret[:5] + '...' if client_secret else 'GOOGLE_CLIENT_SECRET não definido')
        app.logger.debug('GOOGLE_REDIRECT_URI: %s', redirect_uri)

        # Inicializa o cliente OAuth
        oauth = OAuth(app)
        
        # Registra o provedor Google
        google = oauth.register(
            name='google',
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            server_metadata_url=app.config['GOOGLE_DISCOVERY_URL'],
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
        
        # Obtém o token e os dados do usuário
        try:
            token = google.authorize_access_token()
            app.logger.debug('Token obtido com sucesso')
            
            # Recupera o nonce da sessão
            from flask import session
            nonce = session.get('google_auth_nonce')
            app.logger.debug('Nonce recuperado da sessao: %s', nonce)
            
            # Recupera o tipo de autenticação (login ou registro)
            auth_type = session.get('google_auth_type', 'login')
            app.logger.debug('Tipo de autenticacao: %s', auth_type)
            
            # Limpa o nonce da sessão após o uso
            session.pop('google_auth_nonce', None)
            # Usa o nonce para validar o token
            userinfo = google.parse_id_token(token, nonce=nonce)
            app.logger.debug('Informacoes do usuario obtidas: %s', userinfo.get('email'))
        except Exception as token_error:
            app.logger.error('ERRO DETALHADO na obtacao do token: %s', str(token_error))
            raise token_error  # Re-lança para ser capturado pelo try/except principal
        
        # Validar email
        if not userinfo.get("email_verified"):
            flash('Email não verificado pelo Google. Por favor, use outro método.', 'danger')
            return redirect(url_for('login'))
        
        # Obter dados do usuário
        google_id = userinfo["sub"]
        email = userinfo["email"]
        nome = userinfo.get("given_name", email.split("@")[0])
        nome_completo = userinfo.get("name", "")
        foto = userinfo.get("picture", None)
    except Exception as e:
        # Log do erro
        app.logger.error('Falha na autenticacao Google: %s', str(e))

        # Mensagens mais específicas para erros comuns
        error_msg = str(e)
        if "invalid_client" in error_msg:
            flash('Falha na autenticação com Google: As credenciais do cliente são inválidas. Verifique se o ID do cliente e o segredo correspondem aos valores no Google Cloud Console.', 'danger')
            app.logger.debug('DICA: Verifique se o ID do cliente e o segredo no arquivo .env correspondem exatamente aos valores no Google Cloud Console.')
        elif "redirect_uri_mismatch" in error_msg:
            flash('Falha na autenticação com Google: O URI de redirecionamento não está autorizado no Console do Google Cloud.', 'danger')
            app.logger.debug('DICA: Adicione %s as URIs de redirecionamento autorizadas no Google Cloud Console.', app.config.get('GOOGLE_REDIRECT_URI'))
        elif "nonce" in error_msg:
            flash('Falha na autenticação com Google: Problema com a verificação de segurança. Tente novamente.', 'danger')
            app.logger.debug('DICA: Ocorreu um problema com o parametro nonce. A sessao pode ter expirado ou sido perdida. Tentar novamente deve resolver.')
        else:
            flash(f'Falha na autenticação com Google: {error_msg}', 'danger')
            app.logger.debug('DICA: Erro nao especifico. Verifique as configuracoes do Google OAuth e tente novamente.')
        
        return redirect(url_for('login'))
    
    # Verificar o tipo de autenticação (login ou registro)
    auth_type = session.pop('google_auth_type', 'login')
    
    # Procurar usuário pelo Google ID
    user = Usuario.query.filter_by(google_id=google_id).first()
    
    # Se não encontrou por Google ID, tenta pelo email
    if not user:
        user = Usuario.query.filter_by(email=email).first()
        
        # Se encontrou pelo email, atualiza o Google ID
        if user:
            user.google_id = google_id
            db.session.commit()
    
    # Se não encontrou o usuário, direciona para completar cadastro 
    # independente se é fluxo de login ou registro
    if not user:
        # Armazenar dados na sessão para o formulário de completar cadastro
        session['google_register_data'] = {
            'google_id': google_id,
            'email': email,
            'nome': nome_completo or nome,
            'foto': foto
        }
        
        # Se for fluxo de login, adiciona uma mensagem específica
        if auth_type == 'login':
            flash('Você ainda não possui uma conta. Por favor, complete seu cadastro para continuar.', 'info')
        
        # Redirecionar para completar cadastro
        return redirect(url_for('completar_cadastro'))
    
    # Se chegou aqui, o usuário existe e podemos fazer login
    login_user(user)
    flash(f'Bem-vindo, {user.username}!', 'success')
    
    # Redirecionar para a página principal
    return redirect(url_for('dashboard'))

@app.route('/completar-cadastro', methods=['GET', 'POST'])
def completar_cadastro():
    """Página para completar o cadastro após autenticação com Google"""
    # Verificar se existem dados de registro do Google na sessão
    google_data = session.get('google_register_data')
    if not google_data:
        flash('Acesso inválido. Inicie o cadastro novamente.', 'danger')
        return redirect(url_for('register'))
    
    form = CompletarCadastroForm()
    
    if form.validate_on_submit():
        # Verificar se o email já está em uso
        existing_user = Usuario.query.filter_by(email=google_data['email']).first()
        if existing_user:
            flash('Este email já está cadastrado. Faça login.', 'warning')
            return redirect(url_for('login'))
        
        # Criar novo usuário com os dados do Google e do formulário
        import secrets
        senha_temp = secrets.token_urlsafe(16)
        
        user = Usuario(
            username=form.username.data,
            email=google_data['email'],
            google_id=google_data['google_id'],
            telefone=form.telefone.data,
            data_nascimento=form.data_nascimento.data,
            sexo=form.sexo.data,
            cidade=form.cidade.data,
            email_verified=True  # Email já verificado pelo Google
        )
        user.set_password(senha_temp)
        
        # Verificar se é o primeiro usuário para torná-lo admin
        if Usuario.query.count() == 0:
            user.is_admin = True
            flash('Primeiro usuário criado como administrador!', 'info')
        
        # Salvar usuário no banco
        db.session.add(user)
        db.session.commit()
        
        # Criar categorias padrão
        criar_categorias_padrao(user.id)
        
        # Limpar dados da sessão
        session.pop('google_register_data', None)
        
        # Fazer login do usuário
        login_user(user)
        
        flash('Cadastro completado com sucesso! Bem-vindo ao Controle Financeiro!', 'success')
        return redirect(url_for('dashboard'))
    
    # Pre-preencher o formulário com dados do Google
    if not form.username.data and google_data.get('nome'):
        form.username.data = google_data['nome']
    
    return render_template('auth/completar_cadastro.html', 
                           form=form,
                           google_email=google_data['email'],
                           google_name=google_data['nome'],
                           google_picture=google_data.get('foto'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro de novos usuários"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegisterForm()
    
    if form.validate_on_submit():
        # Verificar se email já existe
        existing_email = Usuario.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('Email já está em uso. Use outro email.', 'danger')
            return redirect(url_for('register'))
        
        # Criar novo usuário
        user = Usuario(
            username=form.username.data,
            email=form.email.data,
            telefone=form.telefone.data,
            data_nascimento=form.data_nascimento.data,
            sexo=form.sexo.data,
            cidade=form.cidade.data
        )
        user.set_password(form.password.data)
        
        # Primeiro usuário se torna admin automaticamente
        if Usuario.query.count() == 0:
            user.is_admin = True
            user.email_verified = True  # Admin não precisa verificar email
            flash('Primeiro usuário criado como administrador!', 'info')
        
        db.session.add(user)
        
        try:
            db.session.commit()
            
            # Criar categorias padrão para o novo usuário
            criar_categorias_padrao(user.id)
            
            # Enviar email de verificação (exceto para admin)
            if not user.is_admin:
                if send_verification_email(user):
                    flash(f'Conta criada com sucesso! Enviamos um email de confirmação para {user.email}', 'success')
                    flash('Por favor, confirme seu email antes de fazer login.', 'info')
                else:
                    flash(f'Conta criada, mas houve problema ao enviar email. Contate o suporte.', 'warning')
            else:
                flash(f'Conta de administrador criada com sucesso!', 'success')
                # Login automático para admin
                login_user(user)
                return redirect(url_for('dashboard'))
            
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao criar conta. Tente novamente.', 'danger')
            return redirect(url_for('register'))
    
    # Verifica se as configurações do Google estão disponíveis
    has_google_auth = bool(app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'))
    
    return render_template('auth/register.html', form=form, has_google_auth=has_google_auth)

@app.route('/confirm-email/<token>')
def confirm_email(token):
    """Confirma o email do usuário através do token"""
    user = Usuario.query.filter_by(email_verification_token=token).first()
    
    if user is None:
        flash('Token de verificação inválido.', 'danger')
        return redirect(url_for('login'))
    
    if user.email_verified:
        flash('Email já foi confirmado anteriormente.', 'info')
        return redirect(url_for('login'))
    
    if not user.verify_email_token(token):
        flash('Token de verificação expirado. Solicite um novo.', 'danger')
        return redirect(url_for('resend_verification'))
    
    user.confirm_email()
    flash('Email confirmado com sucesso! Agora você pode fazer login.', 'success')
    return redirect(url_for('login'))

@app.route('/resend-verification')
def resend_verification():
    """Página para reenviar email de verificação"""
    return render_template('auth/resend_verification.html')

@app.route('/resend-verification', methods=['POST'])
def resend_verification_post():
    """Reenvia email de verificação"""
    email = request.form.get('email')
    
    if not email:
        flash('Email é obrigatório.', 'danger')
        return redirect(url_for('resend_verification'))
    
    user = Usuario.query.filter_by(email=email).first()
    
    if user is None:
        flash('Email não encontrado.', 'danger')
        return redirect(url_for('resend_verification'))
    
    if user.email_verified:
        flash('Este email já foi confirmado.', 'info')
        return redirect(url_for('login'))
    
    if send_verification_email(user):
        flash(f'Email de verificação reenviado para {email}', 'success')
    else:
        flash('Erro ao enviar email. Tente novamente mais tarde.', 'danger')
    
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Página para solicitar redefinição de senha"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        
        # Sempre mostrar a mesma mensagem, mesmo se o email não existir (por segurança)
        flash('Se o email estiver cadastrado, você receberá um link para redefinição de senha.', 'info')
        
        if user:
            if send_password_reset_email(user):
                app.logger.info(f"✅ Email de redefinição enviado para {user.email}")
            else:
                app.logger.error(f"❌ Falha ao enviar email de redefinição para {user.email}")
        
        return redirect(url_for('login'))
    
    return render_template('auth/forgot_password.html', form=form)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Página para redefinir a senha com o token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # Encontrar usuário pelo token
    user = None
    try:
        # Buscar usuários e verificar token para cada um (JSON format)
        for u in Usuario.query.all():
            if u.password_reset_token and token in u.password_reset_token:
                if u.verify_password_reset_token(token):
                    user = u
                    break
    except:
        user = None
    
    if not user:
        flash('Link de redefinição inválido ou expirado.', 'danger')
        return redirect(url_for('forgot_password'))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.clear_password_reset_token()  # Limpar token após uso
        db.session.commit()
        flash('Sua senha foi redefinida com sucesso! Você já pode fazer login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/reset_password.html', form=form)

@app.route('/verify-mfa', methods=['GET', 'POST'])
def verify_mfa():
    """Verificação do código MFA"""
    if 'pre_2fa_user_id' not in session:
        return redirect(url_for('login'))
    
    user = Usuario.query.get(session['pre_2fa_user_id'])
    if not user:
        session.pop('pre_2fa_user_id', None)
        return redirect(url_for('login'))
    
    form = MFAForm()
    
    if form.validate_on_submit():
        if user.verify_mfa_token(form.mfa_code.data):
            # MFA válido - fazer login
            login_user(user, remember=session.get('remember_me', False))
            user.record_successful_login()
            
            # Limpar dados da sessão
            session.pop('pre_2fa_user_id', None)
            session.pop('remember_me', None)
            
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('dashboard')
            
            flash(f'Login realizado com sucesso! Bem-vindo, {user.username}!', 'success')
            return redirect(next_page)
        else:
            user.record_failed_login()
            flash('Código de verificação inválido', 'danger')
    
    return render_template('auth/verify_mfa.html', form=form)

@app.route('/backup-code', methods=['GET', 'POST'])
def backup_code():
    """Usar código de backup"""
    if 'pre_2fa_user_id' not in session:
        return redirect(url_for('login'))
    
    user = Usuario.query.get(session['pre_2fa_user_id'])
    if not user:
        session.pop('pre_2fa_user_id', None)
        return redirect(url_for('login'))
    
    form = BackupCodeForm()
    
    if form.validate_on_submit():
        if user.verify_backup_code(form.backup_code.data):
            # Código válido - fazer login
            login_user(user, remember=session.get('remember_me', False))
            user.record_successful_login()
            
            # Limpar dados da sessão
            session.pop('pre_2fa_user_id', None)
            session.pop('remember_me', None)
            
            flash(f'Login realizado com código de backup! Bem-vindo, {user.username}!', 'warning')
            flash('Código de backup usado. Considere gerar novos códigos.', 'info')
            return redirect(url_for('dashboard'))
        else:
            user.record_failed_login()
            flash('Código de backup inválido ou já utilizado', 'danger')
    
    return render_template('auth/backup_code.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    username = current_user.username
    logout_user()
    flash(f'Até logo, {username}!', 'info')
    return redirect(url_for('login'))

@app.route('/setup-mfa', methods=['GET', 'POST'])
@login_required
def setup_mfa():
    """Configurar MFA para o usuário"""
    if current_user.mfa_enabled:
        flash('MFA já está configurado', 'info')
        return redirect(url_for('profile'))
    
    form = SetupMFAForm()
    
    # Gerar ou usar secret existente
    if not current_user.mfa_secret:
        current_user.generate_mfa_secret()
        db.session.commit()
    
    # Gerar QR code
    qr_uri = current_user.get_mfa_uri()
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_uri)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    qr_code_b64 = base64.b64encode(buffer.getvalue()).decode()
    
    if form.validate_on_submit():
        if current_user.verify_mfa_token(form.mfa_code.data):
            # Código válido - ativar MFA
            current_user.mfa_enabled = True
            
            # Gerar códigos de backup
            backup_codes = current_user.generate_backup_codes()
            db.session.commit()
            
            flash('MFA configurado com sucesso!', 'success')
            return render_template('auth/backup_codes.html', codes=backup_codes)
        else:
            flash('Código de verificação inválido. Tente novamente.', 'danger')
    
    return render_template('auth/setup_mfa.html', 
                         form=form, 
                         qr_code=qr_code_b64, 
                         secret=current_user.mfa_secret)

@app.route('/disable-mfa', methods=['POST'])
@login_required
def disable_mfa():
    """Desabilitar MFA"""
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    current_user.backup_codes = None
    db.session.commit()
    
    flash('MFA desabilitado com sucesso', 'warning')
    return redirect(url_for('profile'))

@app.route('/profile')
@login_required
def profile():
    """Perfil do usuário"""
    # Buscar todos os temas para o formulário
    temas = Tema.query.all()
    return render_template('auth/profile.html', temas=temas)

@app.route('/atualizar-tema-usuario', methods=['POST'])
@login_required
def atualizar_tema_usuario():
    """Atualiza as preferências de tema do usuário"""
    tema_id = request.form.get('tema_id', type=int)
    dark_mode = request.form.get('dark_mode', type=int)
    
    # Verificar se o tema existe
    if tema_id:
        tema = Tema.query.get(tema_id)
        if not tema:
            flash('Tema não encontrado', 'danger')
            return redirect(url_for('profile'))
    
    # Atualizar preferências
    current_user.tema_id = tema_id
    current_user.dark_mode = bool(dark_mode)
    
    try:
        db.session.commit()
        flash('Preferências de tema atualizadas com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar preferências: {str(e)}', 'danger')
    
    return redirect(url_for('profile'))

@app.route('/change-password', methods=['GET', 'POST'])
@login_required  
def change_password():
    """Alterar senha"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Senha atual incorreta', 'danger')
            return redirect(url_for('change_password'))
        
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('auth/change_password.html', form=form)

# === ROTAS PRINCIPAIS (PROTEGIDAS) ===

@app.before_request
def make_session_permanent():
    """Torna a sessão permanente para evitar perdas durante o fluxo de autenticação"""
    session.permanent = True

@app.route('/')
def landing():
    # redireciona usuário autenticado para o dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal com resumo financeiro"""
    try:
        # Calculando totais - filtrar por usuário
        receitas_total = db.session.query(func.sum(Transacao.valor)).filter(
            Transacao.tipo == TipoTransacao.RECEITA,
            Transacao.user_id == current_user.id
        ).scalar() or 0
        
        despesas_total = db.session.query(func.sum(Transacao.valor)).filter(
            Transacao.tipo == TipoTransacao.DESPESA,
            Transacao.user_id == current_user.id
        ).scalar() or 0
        
        saldo = receitas_total - despesas_total
        
        # Últimas transações - filtrar por usuário
        transacoes_recentes = Transacao.query.filter_by(user_id=current_user.id).order_by(
            Transacao.data_transacao.desc()
        ).limit(5).all()
        
        # Dados do mês atual - filtrar por usuário
        inicio_mes = datetime.now().replace(day=1)
        receitas_mes = db.session.query(func.sum(Transacao.valor)).filter(
            Transacao.tipo == TipoTransacao.RECEITA,
            Transacao.data_transacao >= inicio_mes,
            Transacao.user_id == current_user.id
        ).scalar() or 0
        
        despesas_mes = db.session.query(func.sum(Transacao.valor)).filter(
            Transacao.tipo == TipoTransacao.DESPESA,
            Transacao.data_transacao >= inicio_mes,
            Transacao.user_id == current_user.id
        ).scalar() or 0
        
        return render_template('dashboard.html',
                             receitas_total=receitas_total,
                             despesas_total=despesas_total,
                             saldo=saldo,
                             receitas_mes=receitas_mes,
                             despesas_mes=despesas_mes,
                             transacoes_recentes=transacoes_recentes)
    except (ProgrammingError, OperationalError) as e:
        # DB schema mismatch (e.g. missing coluna forma_pagamento) - show degraded dashboard
        app.logger.exception('DB SCHEMA ERROR in dashboard: %s', e)
        flash('Erro no banco de dados: coluna ausente. Execute a migração de esquema (veja logs).', 'danger')
        return render_template('dashboard.html',
                             receitas_total=0,
                             despesas_total=0,
                             saldo=0,
                             receitas_mes=0,
                             despesas_mes=0,
                             transacoes_recentes=[])

@app.route('/transacoes')
@login_required
def transacoes():
    """Lista transações do usuário atual com paginação"""
    # Parâmetros de paginação
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', app.config['TRANSACOES_PER_PAGE_DEFAULT'], type=int)
    
    # Validar limite máximo por página
    if per_page > app.config['TRANSACOES_PER_PAGE_MAX']:
        per_page = app.config['TRANSACOES_PER_PAGE_MAX']
    
    # Aplicar filtros se fornecidos
    query = Transacao.query.filter_by(user_id=current_user.id)
    
    # Parâmetros para navegação por mês
    from datetime import datetime, date
    from dateutil.relativedelta import relativedelta
    
    # Determinar o mês e ano atuais ou navegados
    hoje = date.today()
    mes_param = request.args.get('mes')
    ano_atual = request.args.get('ano', hoje.year, type=int)
    mes_atual = request.args.get('mes_atual', hoje.month, type=int)
    
    # Ajustar mês e ano com base na navegação
    if mes_param == 'anterior':
        # Mês anterior
        if mes_atual == 1:
            mes_atual = 12
            ano_atual -= 1
        else:
            mes_atual -= 1
    elif mes_param == 'proximo':
        # Próximo mês
        if mes_atual == 12:
            mes_atual = 1
            ano_atual += 1
        else:
            mes_atual += 1
    
    # Lista de nomes dos meses em português
    meses_nomes = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    mes_nome = meses_nomes[mes_atual - 1]
    
    # Sempre filtrar por mês/ano selecionado (navegação)
    from datetime import datetime, date
    primeiro_dia = date(ano_atual, mes_atual, 1)
    if mes_atual == 12:
        ultimo_dia = date(ano_atual + 1, 1, 1) - relativedelta(days=1)
    else:
        ultimo_dia = date(ano_atual, mes_atual + 1, 1) - relativedelta(days=1)

    # Aplicar filtro de período do mês visualizado
    query = query.filter(Transacao.data_transacao >= datetime.combine(primeiro_dia, datetime.min.time()))
    query = query.filter(Transacao.data_transacao <= datetime.combine(ultimo_dia, datetime.max.time()))
    
    # Paginação
    query_final = query.order_by(Transacao.data_transacao.desc())
    
    # NOVA FUNCIONALIDADE: Incluir projeções futuras não consolidadas
    # Mostrar projeções apenas para meses futuros
    mostrar_projecoes = request.args.get('mostrar_projecoes', 'true').lower() == 'true'
    projecoes = []
    hoje = datetime.utcnow().date()
    
    # Logs para debug via logger
    app.logger.debug('Parâmetros da rota transacoes: mostrar_projecoes=%s, hoje=%s, mes_atual=%s, ano_atual=%s', mostrar_projecoes, hoje, mes_atual, ano_atual)

    # Se estamos visualizando um mês futuro, buscar projeções
    data_visualizada_obj = datetime(ano_atual, mes_atual, 1).date()
    app.logger.debug('Data visualizada=%s; primeiro dia do mes atual=%s; condicao mostrar_projecoes=%s', data_visualizada_obj, hoje.replace(day=1), (mostrar_projecoes and data_visualizada_obj >= hoje.replace(day=1)))
    
    if mostrar_projecoes and data_visualizada_obj >= hoje.replace(day=1):
        app.logger.debug('Gerando projecoes para mes futuro: %s/%s', mes_atual, ano_atual)
        
        # Obter projeções para este mês específico
        primeiro_dia_mes = datetime(ano_atual, mes_atual, 1)
        if mes_atual == 12:
            ultimo_dia_mes = datetime(ano_atual + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia_mes = datetime(ano_atual, mes_atual + 1, 1) - timedelta(days=1)
        
        # Obter recorrências ativas
        recorrentes_ativas = TransacaoRecorrente.query.filter_by(
            status=StatusRecorrencia.ATIVA, 
            user_id=current_user.id
        ).all()
        
        # ID temporário para projeções (negativo para evitar conflitos)
        next_temp_id = -1

        app.logger.debug('Total de recorrencias ativas: %s', len(recorrentes_ativas))

        # usar configuração centralizada para horizonte de projeções
        meses_padrao_projecoes = app.config.get('MESES_FUTUROS_DEFAULT', 36)
        for recorrente in recorrentes_ativas:
            app.logger.debug('Processando recorrencia: %s - %s', recorrente.id, recorrente.descricao)
            # Gerar transações projetadas usando o método atualizado (apenas projeções)
            transacoes_projetadas = recorrente.gerar_transacoes_pendentes(meses_futuros=meses_padrao_projecoes, apenas_projetar=True)
            # Filtrar apenas as transações deste mês
            for projecao in transacoes_projetadas:
                if primeiro_dia_mes <= projecao.data_transacao <= ultimo_dia_mes:
                    projecoes.append(projecao)
                    app.logger.debug('Projecao adicionada: %s para %s', projecao.descricao, projecao.data_transacao)
    
    # Paginar transações do banco de dados
    transacoes_pagination = query_final.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # Combinar transações do banco com projeções, sem duplicar datas
    transacoes_combinadas = list(transacoes_pagination.items)
    # Adicionar flag is_projetada=False para transações reais
    for transacao in transacoes_combinadas:
        transacao.is_projetada = False

    # Montar set de datas já ocupadas por transações reais
    datas_reais = set()
    for t in transacoes_combinadas:
        datas_reais.add((t.data_transacao, t.recorrencia_id))

    # Só adicionar projeções para datas que não têm transação real
    projecoes_filtradas = [p for p in projecoes if (p.data_transacao, p.recorrencia_id) not in datas_reais]
    app.logger.debug('Projecoes filtradas (sem datas duplicadas): %s', len(projecoes_filtradas))

    if projecoes_filtradas:
        projecoes_filtradas.sort(key=lambda x: x.data_transacao)
        transacoes_combinadas.extend(projecoes_filtradas)
        transacoes_combinadas.sort(key=lambda x: x.data_transacao, reverse=True)
        transacoes_pagination.total += len(projecoes_filtradas)
        app.logger.debug('Lista final: %s transacoes, das quais %s sao projecoes', len(transacoes_combinadas), len(projecoes_filtradas))
        for p in projecoes_filtradas:
            app.logger.debug('Projecao: ID=%s, Data=%s, Valor=%s, Descricao=%s', p.id, p.data_transacao, p.valor, p.descricao)
    else:
        app.logger.debug('Nenhuma projecao gerada')
    
    # Verificar se estamos próximos ao fim das transações recorrentes e gerar mais se necessário
    # CRÍTICO: Esta é a parte que garante a geração contínua de transações
    
    app.logger.debug('INICIANDO VERIFICACAO DE TRANSACOES RECORRENTES; mes visualizado=%s/%s (%s)', mes_atual, ano_atual, mes_nome)
    
    # Definir data limite com base no mês visualizado
    # SEMPRE considerar o mês visualizado como referência, não filtros
    # Usar o mês visualizado como referência para decisões de geração
    data_visualizada = datetime.combine(primeiro_dia, datetime.min.time())
    app.logger.debug('Usando mes visualizado como referencia: %s', data_visualizada)
    
    # Calcular quantos meses no futuro estamos visualizando
    hoje = datetime.utcnow()
    diferenca_meses = ((data_visualizada.year - hoje.year) * 12 + data_visualizada.month - hoje.month)
    app.logger.debug('Diferenca em meses entre hoje e mes visualizado: %s', diferenca_meses)
    
    # Definir horizonte de geração baseado na navegação
    # SEMPRE gerar pelo menos X meses além do mês visualizado
    meses_alem_visualizacao = 24  # Buffer de visualização futura aumentado para 24
    
    # Calcular quantos meses no total gerar a partir de hoje
    if diferenca_meses <= 0:
        # Para meses atuais ou passados, gerar pelo menos o padrão configurado à frente
        meses_para_gerar = app.config.get('MESES_FUTUROS_DEFAULT', 36)
    else:
        # Para meses futuros, gerar até a data visualizada + buffer
        meses_para_gerar = diferenca_meses + meses_alem_visualizacao
    
    app.logger.debug('Meses para gerar a partir de hoje: %s', meses_para_gerar)
    
    # Data limite para geração de transações
    data_limite = hoje + relativedelta(months=meses_para_gerar)
    app.logger.debug('Data limite para geracao: %s', data_limite)
    
    # Buscar todas as transações recorrentes ATIVAS do usuário
    app.logger.debug('Buscando recorrencias ativas')
    
    # IMPORTANTE: Verifique se estamos usando o valor correto para o status ativo
    app.logger.debug('Valor do status ativo na enumeracao: %s', StatusRecorrencia.ATIVA.value)
    
    # Buscar por todas as recorrências do usuário para diagnóstico
    todas_recorrencias = TransacaoRecorrente.query.filter_by(
        user_id=current_user.id
    ).all()
    
    app.logger.debug('Encontradas %s recorrencias para o usuario (de qualquer status)', len(todas_recorrencias))
    for r in todas_recorrencias:
        app.logger.debug('  - ID: %s, Descricao: %s, Status: %s, Tipo: %s', r.id, r.descricao, r.status.value, r.tipo_recorrencia.value)
    
    # Buscar corretamente por status (usando a enumeração diretamente, não o valor)
    recorrentes_ativas = TransacaoRecorrente.query.filter_by(
        user_id=current_user.id, 
        status=StatusRecorrencia.ATIVA
    ).all()
    
    app.logger.debug('Recorrencias ATIVAS encontradas: %s de %s total', len(recorrentes_ativas), len(todas_recorrencias))
    
    # Se não encontrou nenhuma, tente buscar todas as recorrências do usuário para diagnóstico
    if not recorrentes_ativas:
        app.logger.debug('Nenhuma recorrencia com status ATIVA encontrada usando a enumeracao.')
    else:
        app.logger.debug('Encontradas %s recorrencias ativas:', len(recorrentes_ativas))
        for r in recorrentes_ativas:
            app.logger.debug('  - ID: %s, Descricao: %s, Tipo: %s, Status: %s', r.id, r.descricao, r.tipo_recorrencia.value, r.status.value)
    
    if not recorrentes_ativas:
        app.logger.debug('Nenhuma recorrencia ativa encontrada para o usuario %s. Nao ha transacoes para gerar.', current_user.id)
    else:
        app.logger.debug('Processando %s recorrencias ativas encontradas', len(recorrentes_ativas))
    
    # Para cada recorrente ativa, SEMPRE verificar e gerar transações
    transacoes_recorrentes_geradas = 0
    recorrentes_atualizadas = []
    
    for recorrente in recorrentes_ativas:
        try:
            app.logger.debug('\nProcessando recorrencia %s: %s', recorrente.id, recorrente.descricao)
            app.logger.debug('Gerando transacoes para %s meses', meses_para_gerar)

            # Chamar diretamente o método de geração com o horizonte calculado
            novas_transacoes = recorrente.gerar_transacoes_pendentes(meses_futuros=meses_para_gerar)

            transacoes_recorrentes_geradas += len(novas_transacoes)
            if len(novas_transacoes) > 0:
                recorrentes_atualizadas.append(recorrente.id)
                app.logger.debug('Geradas %s novas transacoes', len(novas_transacoes))
            else:
                app.logger.debug('Nenhuma nova transacao gerada')
                
        except Exception as e:
            app.logger.error('ERRO ao gerar transacoes para recorrencia %s: %s', recorrente.id, str(e))
            import traceback
            traceback.print_exc()  # Exibir stack trace completo
    
    # Se foram geradas novas transações, refazer a consulta e a paginação
    if transacoes_recorrentes_geradas > 0:
        # Reconstruir a consulta completa — apenas pelo mês visualizado para manter comportamento
        query = Transacao.query.filter_by(user_id=current_user.id)
        query = query.filter(Transacao.data_transacao >= datetime.combine(primeiro_dia, datetime.min.time()))
        query = query.filter(Transacao.data_transacao <= datetime.combine(ultimo_dia, datetime.max.time()))

        # Refazer a paginação
        transacoes_pagination = query.order_by(Transacao.data_transacao.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Preparar mensagem para o usuário
        recorrentes_texto = ", ".join([f"#{id}" for id in recorrentes_atualizadas[:3]])
        if len(recorrentes_atualizadas) > 3:
            recorrentes_texto += f" e mais {len(recorrentes_atualizadas) - 3}"
        
        # flash(f'Foram geradas automaticamente {transacoes_recorrentes_geradas} transações recorrentes ({recorrentes_texto}) para visualização futura.', 'info')
    
    # Opções de itens por página (mantidas)
    per_page_options = [10, 20, 50, 100]
    per_page_options = [opt for opt in per_page_options if opt <= app.config['TRANSACOES_PER_PAGE_MAX']]

    # Renderizar sem filtros (filtros vazios para compatibilidade com paginação)
    return render_template('transacoes.html', 
                         transacoes=transacoes_combinadas,
                         pagination=transacoes_pagination,
                         per_page_options=per_page_options,
                         current_per_page=per_page,
                         ano_atual=ano_atual,
                         mes_atual=mes_atual,
                         mes_nome=mes_nome,
                         filtros={})
                         
@app.route('/confirmar-transacao/<int:recorrencia_id>/<data_transacao>')
@login_required
def exibir_confirmacao_transacao(recorrencia_id, data_transacao):
    """Exibe a página de confirmação para uma transação projetada"""
    # Buscar a recorrência
    recorrencia = TransacaoRecorrente.query.filter_by(
        id=recorrencia_id, 
        user_id=current_user.id
    ).first_or_404()
    
    # Converter a data para objeto datetime
    try:
        data = datetime.strptime(data_transacao, '%Y-%m-%d')
    except ValueError:
        flash('Data inválida', 'danger')
        return redirect(url_for('transacoes'))
    
    # Verificar se já existe uma transação para esta data
    transacao_existente = Transacao.query.filter_by(
        recorrencia_id=recorrencia_id,
        data_transacao=data
    ).first()
    
    if transacao_existente:
        flash('Esta transação já foi confirmada anteriormente', 'warning')
        return redirect(url_for('transacoes'))
    
    # Criar transação projetada (não salva no banco)
    transacao = Transacao(
        id=-1,  # ID temporário
        descricao=recorrencia.descricao,
        valor=recorrencia.valor,
        tipo=recorrencia.tipo,
        data_transacao=data,
        categoria_id=recorrencia.categoria_id,
        conta_id=recorrencia.conta_id,
        recorrencia_id=recorrencia_id,
        user_id=current_user.id
    )
    
    # Carregar categoria e conta para exibição
    transacao.categoria = recorrencia.categoria
    transacao.conta = recorrencia.conta
    
    # Salvar URL de redirecionamento para retornar após a confirmação
    redirect_url = request.args.get('redirect_url', url_for('transacoes'))
    
    return render_template('confirmar_transacao.html', 
                          transacao=transacao,
                          redirect_url=redirect_url)

@app.route('/confirmar-transacao', methods=['POST'])
@login_required
def confirmar_transacao():
    """Confirma uma transação projetada, salvando-a no banco de dados"""
    # Obter dados do formulário
    recorrencia_id = request.form.get('recorrencia_id', type=int)
    data_transacao = request.form.get('data_transacao')
    confirmo = request.form.get('confirmo')
    redirect_url = request.form.get('redirect_url', url_for('transacoes'))
    
    # Validar dados
    if not recorrencia_id or not data_transacao or not confirmo:
        flash('Dados incompletos para confirmar a transação', 'danger')
        return redirect(redirect_url)
    
    # Buscar a recorrência
    recorrencia = TransacaoRecorrente.query.filter_by(
        id=recorrencia_id, 
        user_id=current_user.id
    ).first_or_404()
    
    # Converter a data para objeto datetime
    try:
        data = datetime.strptime(data_transacao, '%Y-%m-%d')
    except ValueError:
        flash('Data inválida', 'danger')
        return redirect(redirect_url)
    
    # Verificar se já existe uma transação para esta data
    transacao_existente = Transacao.query.filter_by(
        recorrencia_id=recorrencia_id,
        data_transacao=data
    ).first()
    
    if transacao_existente:
        flash('Esta transação já foi confirmada anteriormente', 'warning')
        return redirect(redirect_url)
    
    # Calcular número da parcela igual à lógica da projeção
    descricao_final = recorrencia.descricao
    if recorrencia.is_parcelada:
        # Conta quantas transações (reais) já existem para esta recorrência antes desta data
        total_existentes = len([
            t for t in recorrencia.transacoes
            if t.recorrencia_id == recorrencia_id and t.data_transacao < data
        ])
        numero_parcela = total_existentes + 1
        descricao_final += f" - Parcela {numero_parcela}/{recorrencia.total_parcelas}"
    nova_transacao = Transacao(
        descricao=descricao_final,
        valor=recorrencia.valor,
        tipo=recorrencia.tipo,
    forma_pagamento_id=recorrencia.forma_pagamento_id,
        data_transacao=data,
        categoria_id=recorrencia.categoria_id,
        conta_id=recorrencia.conta_id,
        recorrencia_id=recorrencia_id,
        user_id=current_user.id
    )
    
    # Salvar no banco de dados
    try:
        db.session.add(nova_transacao)
        
        # Atualizar contador de parcelas geradas para recorrências parceladas
        if recorrencia.is_parcelada:
            recorrencia.parcelas_geradas += 1
            # Verificar se atingiu o total de parcelas
            if recorrencia.parcelas_geradas >= recorrencia.total_parcelas:
                recorrencia.status = StatusRecorrencia.FINALIZADA
        
        db.session.commit()
        flash('Transação confirmada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao confirmar transação: {str(e)}', 'danger')
    
    return redirect(redirect_url)

@app.route('/api/consolidar-projecoes', methods=['POST'])
@login_required
def api_consolidar_projecoes():
    """API para consolidar múltiplas projeções de uma vez"""
    # Receber dados do formulário
    dados = request.get_json()
    
    if not dados or 'projecoes_ids' not in dados:
        return jsonify({'success': False, 'message': 'Dados inválidos'})
    
    projecoes_ids = dados.get('projecoes_ids', [])
    
    if not projecoes_ids:
        return jsonify({'success': False, 'message': 'Nenhuma projeção selecionada'})
    
    # Contador de transações processadas com sucesso
    transacoes_confirmadas = 0
    erros = []
    
    # Processar cada projeção
    for projecao_id in projecoes_ids:
        try:
            # Obter os dados da projeção
            projecao_id_abs = abs(int(projecao_id))
            recorrencia_id = dados.get(f'recorrencia_{projecao_id_abs}')
            data_transacao = dados.get(f'data_{projecao_id_abs}')
            
            if not recorrencia_id or not data_transacao:
                erros.append(f"Dados incompletos para projeção {projecao_id}")
                continue
            
            # Buscar a recorrência
            recorrencia = TransacaoRecorrente.query.filter_by(
                id=recorrencia_id, 
                user_id=current_user.id
            ).first()
            
            if not recorrencia:
                erros.append(f"Recorrência {recorrencia_id} não encontrada")
                continue
            
            # Converter a data para objeto datetime
            try:
                data = datetime.strptime(data_transacao, '%Y-%m-%d')
            except ValueError:
                erros.append(f"Data inválida: {data_transacao}")
                continue
            
            # Verificar se já existe uma transação para esta data
            transacao_existente = Transacao.query.filter_by(
                recorrencia_id=recorrencia_id,
                data_transacao=data
            ).first()
            
            if transacao_existente:
                erros.append(f"Transação para {data_transacao} já existe")
                continue
            
            # Criar nova transação real
            nova_transacao = Transacao(
                descricao=recorrencia.descricao,
                valor=recorrencia.valor,
                tipo=recorrencia.tipo,
                forma_pagamento_id=recorrencia.forma_pagamento_id,
                data_transacao=data,
                categoria_id=recorrencia.categoria_id,
                conta_id=recorrencia.conta_id,
                recorrencia_id=recorrencia_id,
                user_id=current_user.id
            )
            
            # Salvar no banco de dados
            db.session.add(nova_transacao)
            
            # Atualizar contador de parcelas geradas para recorrências parceladas
            if recorrencia.is_parcelada:
                recorrencia.parcelas_geradas += 1
                # Verificar se atingiu o total de parcelas
                if recorrencia.parcelas_geradas >= recorrencia.total_parcelas:
                    recorrencia.status = StatusRecorrencia.FINALIZADA
            
            # Incrementar contador de sucesso
            transacoes_confirmadas += 1
            
        except Exception as e:
            erros.append(f"Erro ao processar projeção {projecao_id}: {str(e)}")
    
    # Commit das alterações se houver transações confirmadas
    if transacoes_confirmadas > 0:
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False, 
                'message': f'Erro ao salvar as transações: {str(e)}'
            })
    
    # Construir mensagem de resposta
    if transacoes_confirmadas == 0:
        return jsonify({
            'success': False,
            'message': f'Nenhuma transação confirmada. Erros: {", ".join(erros)}'
        })
    elif erros:
        return jsonify({
            'success': True,
            'message': f'{transacoes_confirmadas} transação(ões) confirmada(s) com {len(erros)} erro(s)'
        })
    else:
        return jsonify({
            'success': True,
            'message': f'{transacoes_confirmadas} transação(ões) confirmada(s) com sucesso!'
        })

@app.route('/nova-transacao', methods=['GET', 'POST'])
@login_required
def nova_transacao():
    """Adiciona nova transação (única ou recorrente)"""
    form = TransacaoForm(user_id=current_user.id)
    
    # Filtrar opções por usuário
    form.categoria_id.choices = []
    categorias_raiz = Categoria.query.filter_by(parent_id=None, user_id=current_user.id).all()
    
    def add_categoria_choices(categoria, prefix=""):
        display_name = f"{prefix}{categoria.nome}"
        form.categoria_id.choices.append((categoria.id, display_name))
        
        for subcategoria in categoria.subcategorias:
            if subcategoria.user_id == current_user.id:
                add_categoria_choices(subcategoria, f"{prefix}└─ ")
    
    for categoria in categorias_raiz:
        add_categoria_choices(categoria)
        
    # Filtrar contas por usuário
    contas_ativas = Conta.query.filter_by(ativa=True, user_id=current_user.id).all()
    form.conta_id.choices = [(conta.id, conta.nome) for conta in contas_ativas]
    
    if form.validate_on_submit():
        try:
            if form.is_recorrente.data:
                # Criar transação recorrente
                recorrente = TransacaoRecorrente(
                    descricao=form.descricao.data,
                    valor=form.valor.data,
                    tipo=TipoTransacao(form.tipo.data),
                    tipo_recorrencia=TipoRecorrencia(form.tipo_recorrencia.data),
                    data_inicio=form.data_transacao.data,
                    data_fim=form.data_fim.data,
                    forma_pagamento_id=int(form.forma_pagamento.data) if form.forma_pagamento.data else None,
                    categoria_id=form.categoria_id.data,
                    conta_id=form.conta_id.data,
                    total_parcelas=form.total_parcelas.data if form.is_parcelada.data else None,
                    user_id=current_user.id  # Associar ao usuário atual
                )
                
                db.session.add(recorrente)
                db.session.commit()
                
                # Definir horizonte de meses futuros (usar valor padrão da configuração)
                meses_futuros = app.config.get('MESES_FUTUROS_DEFAULT', 36)
                
                # Se tem data_fim, usar isso como limite
                if recorrente.data_fim:
                    # Gerar transações passadas e projetar futuras
                    transacoes_geradas = recorrente.gerar_transacoes_pendentes(apenas_projetar=True)
                    transacoes_reais = [t for t in transacoes_geradas if not hasattr(t, 'is_projetada') or not t.is_projetada]
                    projecoes = [t for t in transacoes_geradas if hasattr(t, 'is_projetada') and t.is_projetada]
                    mensagem = f'Transação recorrente criada! {len(transacoes_reais)} transação(ões) gerada(s) e {len(projecoes)} projetada(s) até {recorrente.data_fim.strftime("%d/%m/%Y")}.'
                else:
                    # Gerar transações para os próximos meses
                    transacoes_geradas = recorrente.gerar_transacoes_pendentes(meses_futuros=meses_futuros, apenas_projetar=True)
                    transacoes_reais = [t for t in transacoes_geradas if not hasattr(t, 'is_projetada') or not t.is_projetada]
                    projecoes = [t for t in transacoes_geradas if hasattr(t, 'is_projetada') and t.is_projetada]
                    mensagem = f'Transação recorrente criada! {len(transacoes_reais)} transação(ões) gerada(s) e {len(projecoes)} projetada(s) para os próximos {meses_futuros} meses.'
                
                flash(mensagem, 'success')
            else:
                # Criar transação única
                transacao = Transacao(
                    descricao=form.descricao.data,
                    valor=form.valor.data,
                    tipo=TipoTransacao(form.tipo.data),
                    forma_pagamento_id=int(form.forma_pagamento.data) if form.forma_pagamento.data else None,
                    categoria_id=form.categoria_id.data,
                    conta_id=form.conta_id.data,
                    data_transacao=form.data_transacao.data,
                    user_id=current_user.id  # Associar ao usuário atual
                )
                
                # Processar tags
                if form.tags.data:
                    transacao.set_tags_from_string(form.tags.data)
                
                db.session.add(transacao)
                db.session.commit()
                flash('Transação adicionada com sucesso!', 'success')
            
            return redirect(url_for('transacoes'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar transação: {str(e)}', 'error')
    
    return render_template('nova_transacao.html', form=form)

@app.route('/editar-transacao/<int:transacao_id>', methods=['GET', 'POST'])
@login_required
def editar_transacao(transacao_id):
    """Edita uma transação existente"""
    transacao = Transacao.query.filter_by(id=transacao_id, user_id=current_user.id).first_or_404()
    form = TransacaoForm(obj=transacao, user_id=current_user.id)
    
    # Configurar valores iniciais para campos específicos
    if request.method == 'GET':
        form.tipo.data = transacao.tipo.value
        form.data_transacao.data = transacao.data_transacao.date()
        form.tags.data = transacao.tags_string  # Carregar tags existentes
        # Para transações existentes, assumir que não são recorrentes por padrão
        form.is_recorrente.data = transacao.is_recorrente
        if transacao.is_recorrente:
            # Se a transação faz parte de uma recorrência, buscar dados da recorrência
            if transacao.recorrencia:
                form.tipo_recorrencia.data = transacao.recorrencia.tipo_recorrencia.value
                form.is_parcelada.data = transacao.recorrencia.is_parcelada
                form.total_parcelas.data = transacao.recorrencia.total_parcelas
                form.data_fim.data = transacao.recorrencia.data_fim
    
    if form.validate_on_submit():
        try:
            # Verificar se é uma transação recorrente sendo editada
            if transacao.is_recorrente and transacao.recorrencia:
                flash('Atenção: Esta transação faz parte de uma recorrência. Edite a recorrência para alterar todas as transações futuras.', 'warning')
            
            # Atualizar campos da transação
            transacao.descricao = form.descricao.data
            transacao.valor = form.valor.data
            transacao.tipo = TipoTransacao(form.tipo.data)
            transacao.forma_pagamento_id = int(form.forma_pagamento.data) if form.forma_pagamento.data else None
            transacao.categoria_id = form.categoria_id.data
            transacao.conta_id = form.conta_id.data
            transacao.data_transacao = form.data_transacao.data
            
            # Atualizar tags
            transacao.set_tags_from_string(form.tags.data or '')
            
            db.session.commit()
            flash('Transação atualizada com sucesso!', 'success')
            # Redirecionar de volta para a lista de transações para que a tela seja recarregada
            # e o usuário veja imediatamente a alteração; incluir updated_id para destaque
            return redirect(url_for('transacoes', updated_id=transacao.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar transação: {str(e)}', 'error')
    
    return render_template('editar_transacao.html', form=form, transacao=transacao)

@app.route('/api/transacao/<int:transacao_id>', methods=['DELETE'])
@login_required
def excluir_transacao(transacao_id):
    """Exclui uma transação"""
    try:
        transacao = Transacao.query.filter_by(id=transacao_id, user_id=current_user.id).first_or_404()
        
    # Permitir exclusão de transações recorrentes individuais.
    # Antes bloqueávamos a exclusão por padrão, mas agora o usuário pode remover
    # uma instância consolidada se desejar. A recorrência (se existir) permanece
    # e continuará gerando futuras transações.
        
        descricao = transacao.descricao
        db.session.delete(transacao)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Transação "{descricao}" excluída com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao excluir transação: {str(e)}'
        }), 500

@app.route('/categorias')
@login_required
def categorias():
    """Lista todas as categorias do usuário atual"""
    categorias = Categoria.query.filter_by(user_id=current_user.id).all()
    return render_template('categorias.html', categorias=categorias)

@app.route('/nova-categoria', methods=['GET', 'POST'])
@login_required
def nova_categoria():
    """Adiciona nova categoria"""
    form = CategoriaForm()
    
    # Filtrar categorias parent por usuário
    form.parent_id.choices = [(0, 'Nenhuma (Categoria Raiz)')]
    categorias_raiz = Categoria.query.filter_by(parent_id=None, user_id=current_user.id).all()
    
    def add_categoria_choices(categoria, prefix=""):
        display_name = f"{prefix}{categoria.nome}"
        form.parent_id.choices.append((categoria.id, display_name))
        
        for subcategoria in categoria.subcategorias:
            if subcategoria.user_id == current_user.id:
                add_categoria_choices(subcategoria, f"{prefix}└─ ")
    
    for categoria in categorias_raiz:
        add_categoria_choices(categoria)
    
    if form.validate_on_submit():
        parent_id = form.parent_id.data if form.parent_id.data != 0 else None
        
        categoria = Categoria(
            nome=form.nome.data,
            descricao=form.descricao.data,
            cor=form.cor.data,
            parent_id=parent_id,
            user_id=current_user.id  # Associar ao usuário atual
        )
        db.session.add(categoria)
        db.session.commit()
        flash('Categoria adicionada com sucesso!', 'success')
        return redirect(url_for('categorias'))
    
    return render_template('nova_categoria.html', form=form)

@app.route('/relatorios', methods=['GET', 'POST'])
@login_required  # ← ADICIONAR ESTA LINHA
def relatorios():
    """Página de relatórios com filtros funcionais"""
    from datetime import datetime
    from sqlalchemy import extract, and_, or_
    
    # Valores padrão dos filtros
    ano_atual = datetime.now().year

    # Implementar Post-Redirect-Get para manter filtros no refresh:
    # - Se vier via POST, coletar valores e redirecionar para GET com query params
    # - Se vier via GET, ler valores de request.args
    if request.method == 'POST':
        ano = request.form.get('ano', ano_atual)
        tipo = request.form.get('tipo', 'todos')
        categoria_id = request.form.get('categoria')
        conta_id = request.form.get('conta')
        # Filtro por intervalo de datas (opcional)
        data_inicio_str = request.form.get('data_inicio')
        data_fim_str = request.form.get('data_fim')

        # Montar query params apenas com valores relevantes
        params = {}
        try:
            params['ano'] = int(ano)
        except Exception:
            params['ano'] = ano_atual
        params['tipo'] = tipo or 'todos'
        if categoria_id:
            params['categoria'] = categoria_id
        if conta_id:
            params['conta'] = conta_id
        if data_inicio_str:
            params['data_inicio'] = data_inicio_str
        if data_fim_str:
            params['data_fim'] = data_fim_str

        return redirect(url_for('relatorios', **params))
    else:
        ano = request.args.get('ano', ano_atual)
        tipo = request.args.get('tipo', 'todos')
        categoria_id = request.args.get('categoria')
        conta_id = request.args.get('conta')
        # Filtro por intervalo de datas (opcional)
        data_inicio_str = request.args.get('data_inicio')
        data_fim_str = request.args.get('data_fim')
    
    try:
        ano = int(ano)
    except (ValueError, TypeError):
        ano = ano_atual

    # Parse de data_inicio/data_fim se fornecidos (espera formato YYYY-MM-DD)
    start_dt = None
    end_dt = None
    try:
        if data_inicio_str:
            start_dt = datetime.strptime(data_inicio_str, '%Y-%m-%d')
        if data_fim_str:
            end_dt = datetime.strptime(data_fim_str, '%Y-%m-%d')
    except Exception:
        start_dt = None
        end_dt = None
    
    # Obter anos disponíveis - FILTRAR POR USUÁRIO
    # Anos disponíveis: incluir anos futuros até 5 anos à frente
    anos_transacoes = db.session.query(
        extract('year', Transacao.data_transacao).label('ano')
    ).filter(
        Transacao.user_id == current_user.id
    ).distinct().order_by('ano').all()
    anos_disponiveis = [int(a[0]) for a in anos_transacoes]
    ano_max = max(anos_disponiveis) if anos_disponiveis else ano_atual
    ano_limite = max(ano_max, ano_atual) + 5
    anos_futuros = [a for a in range(ano_atual, ano_limite+1)]
    # Unir anos do banco e futuros, sem duplicar
    anos_disponiveis = sorted(set(anos_disponiveis + anos_futuros))
    
    # Todas as categorias para o filtro - FILTRAR POR USUÁRIO
    todas_categorias = Categoria.query.filter_by(user_id=current_user.id).all()  # ← ADICIONAR FILTRO
    
    # Todas as contas para o filtro - FILTRAR POR USUÁRIO
    todas_contas = Conta.query.filter_by(
        ativa=True, 
        user_id=current_user.id  # ← ADICIONAR FILTRO
    ).order_by(Conta.nome).all()
    
    # Construir query base - FILTRAR POR USUÁRIO
    query = db.session.query(Transacao).filter(
        Transacao.user_id == current_user.id
    )
    
    # ...resto do código permanece igual...
    if tipo != 'todos':
        query = query.filter(Transacao.tipo == TipoTransacao(tipo))
    
    # Aplicar filtro de categoria
    if categoria_id:
        try:
            categoria_id = int(categoria_id)
            categoria_selecionada = Categoria.query.filter_by(
                id=categoria_id,
                user_id=current_user.id  # ← VERIFICAR PROPRIEDADE
            ).first()
            if categoria_selecionada:
                # Incluir categoria e todas suas subcategorias
                subcategorias = categoria_selecionada.get_all_subcategorias(include_self=True)
                categoria_ids = [cat.id for cat in subcategorias]
                query = query.filter(Transacao.categoria_id.in_(categoria_ids))
        except (ValueError, TypeError):
            categoria_id = None
    
    # Aplicar filtro de conta
    if conta_id:
        try:
            conta_id = int(conta_id)
            # Verificar se a conta pertence ao usuário
            conta_do_usuario = Conta.query.filter_by(
                id=conta_id,
                user_id=current_user.id
            ).first()
            if conta_do_usuario:
                query = query.filter(Transacao.conta_id == conta_id)
            else:
                conta_id = None  # Reset se conta não pertence ao usuário
        except (ValueError, TypeError):
            conta_id = None
    
    # Obter transações reais
    # Aplicar filtro de data (intervalo ou ano)
    if start_dt and end_dt:
        # usar intervalo fornecido
        query = query.filter(Transacao.data_transacao >= start_dt, Transacao.data_transacao <= end_dt)
        periodo_inicio = start_dt
        periodo_fim = end_dt
    else:
        # usar ano selecionado
        periodo_inicio = datetime(ano, 1, 1)
        periodo_fim = datetime(ano, 12, 31, 23, 59, 59)
        query = query.filter(Transacao.data_transacao >= periodo_inicio, Transacao.data_transacao <= periodo_fim)

    transacoes = query.all()

    # Gerar projeções futuras para recorrências ativas do usuário
    from models import TransacaoRecorrente
    recorrentes_ativas = TransacaoRecorrente.query.filter_by(user_id=current_user.id, status=StatusRecorrencia.ATIVA).all()
    transacoes_projetadas = []
    # Calcular quantos meses projetar: até o fim do período filtrado
    agora = datetime.utcnow()
    try:
        fim_periodo = periodo_fim
    except NameError:
        fim_periodo = datetime(ano, 12, 31, 23, 59, 59)

    # meses entre agora (mes atual) e fim_periodo (incluir meses)
    meses_futuros_relatorio = 0
    if fim_periodo > agora:
        meses_futuros_relatorio = (fim_periodo.year - agora.year) * 12 + (fim_periodo.month - agora.month)

    for recorrente in recorrentes_ativas:
        # Só gera se não tiver data_fim ou se data_fim for no futuro
        if not recorrente.data_fim or recorrente.data_fim > agora:
            # Gerar apenas o número de meses necessário para cobrir o ano filtrado
            projecoes = recorrente.gerar_transacoes_pendentes(meses_futuros=meses_futuros_relatorio, apenas_projetar=True)
            # Se houver filtro por conta, filtrar também as projeções para a mesma conta
            if conta_id:
                try:
                    conta_filter_val = int(conta_id)
                except Exception:
                    conta_filter_val = None
            else:
                conta_filter_val = None

            filtered_projecoes = []
            for p in projecoes:
                # p pode ter atributo conta_id; respeitar o filtro quando presente
                if conta_filter_val is not None:
                    if getattr(p, 'conta_id', None) != conta_filter_val:
                        continue
                p.is_projetada = True
                filtered_projecoes.append(p)

            transacoes_projetadas.extend(filtered_projecoes)

    # Unir transações reais e projetadas, evitando duplicidade
    # Para recorrentes: priorizar real sobre projetada por (ano, mês, recorrencia_id)
    # Para não recorrentes: deduplicar por (ano, mês, categoria_id, tipo)
    transacoes_unicas = {}
    app.logger.debug('RELATORIO: TRANSACOES REAIS: %s itens', len(transacoes))
    for t in transacoes:
        if t.recorrencia_id:
            chave = (t.data_transacao.year, t.data_transacao.month, t.recorrencia_id)
        else:
            chave = (t.data_transacao.year, t.data_transacao.month, t.categoria_id, t.tipo)
        app.logger.debug('REAL: chave=%s valor=%s id=%s recorrencia_id=%s data=%s', chave, t.valor, getattr(t, 'id', None), t.recorrencia_id, t.data_transacao)
        transacoes_unicas[chave] = t
    app.logger.debug('RELATORIO: TRANSACOES PROJETADAS: %s itens', len(transacoes_projetadas))
    for p in transacoes_projetadas:
        if p.recorrencia_id:
            chave = (p.data_transacao.year, p.data_transacao.month, p.recorrencia_id)
        else:
            chave = (p.data_transacao.year, p.data_transacao.month, p.categoria_id, p.tipo)
        app.logger.debug('PROJETADA: chave=%s valor=%s recorrencia_id=%s data=%s', chave, p.valor, p.recorrencia_id, p.data_transacao)
        if chave not in transacoes_unicas:
            transacoes_unicas[chave] = p
    app.logger.debug('RELATORIO: TOTAL TRANSACOES UNICAS: %s', len(transacoes_unicas))
    transacoes = list(transacoes_unicas.values())
    # Filtrar apenas transações do ano selecionado (evita somar projeções de outros anos)
    try:
        ano = int(ano)
    except Exception:
        ano = datetime.now().year

    # Filtrar transações para o intervalo selecionado (periodo_inicio..periodo_fim)
    # Antes era filtrado apenas pelo ano, o que incluía meses fora do intervalo quando
    # o usuário aplicava um filtro de data mais específico.
    transacoes = [t for t in transacoes if t.data_transacao >= periodo_inicio and t.data_transacao <= periodo_fim]
    
    # Gerar lista de meses baseada no período (rótulos em PT)
    meses_pt = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    meses = []
    month_starts = []
    cur = periodo_inicio.replace(day=1)
    while cur <= periodo_fim:
        month_starts.append(cur)
        meses.append(f"{meses_pt[cur.month-1]} {cur.year}")
        # avançar um mês
        if cur.month == 12:
            cur = cur.replace(year=cur.year+1, month=1)
        else:
            cur = cur.replace(month=cur.month+1)
    
    # Calcular totais mensais sem duplicidade por recorrencia/categoria/tipo
    totais_mensais = {}
    for idx, month_start in enumerate(month_starts):
        # Agrupar por (categoria_id, tipo, recorrencia_id) para evitar duplicidade
        vistos = set()
        receita = 0
        despesa = 0
        for t in transacoes:
            if t.data_transacao.year != month_start.year or t.data_transacao.month != month_start.month:
                continue
            if t.recorrencia_id:
                chave = (t.data_transacao.year, t.data_transacao.month, t.recorrencia_id)
            else:
                chave = (t.data_transacao.year, t.data_transacao.month, t.categoria_id, t.tipo)
            if chave in vistos:
                continue
            vistos.add(chave)
            if t.tipo == TipoTransacao.RECEITA:
                receita += t.valor
            elif t.tipo == TipoTransacao.DESPESA:
                despesa += t.valor
        totais_mensais[meses[idx]] = {'receita': receita, 'despesa': despesa}

    # Calcular totais gerais
    vistos = set()
    total_receitas = 0
    total_despesas = 0
    for t in transacoes:
        if t.recorrencia_id:
            chave = (t.data_transacao.year, t.data_transacao.month, t.recorrencia_id)
        else:
            chave = (t.data_transacao.year, t.data_transacao.month, t.categoria_id, t.tipo)
        if chave in vistos:
            continue
        vistos.add(chave)
        if t.tipo == TipoTransacao.RECEITA:
            total_receitas += t.valor
        elif t.tipo == TipoTransacao.DESPESA:
            total_despesas += t.valor
    saldo_geral = total_receitas - total_despesas
    total_transacoes = len(vistos)
    
    # Organizar categorias por tipo (agregando por categorias primárias/raiz)
    categorias_receitas = []
    categorias_despesas = []

    # Obter categorias raiz do usuário
    categorias_raiz = Categoria.query.filter_by(parent_id=None, user_id=current_user.id).order_by(Categoria.nome).all()

    # Se o usuário filtrou por uma categoria específica, obter seus ids (inclui subcategorias)
    filtro_categoria_ids = None
    if categoria_id:
        categoria_selecionada = Categoria.query.get(categoria_id)
        if categoria_selecionada:
            subcategorias = categoria_selecionada.get_all_subcategorias(include_self=True)
            filtro_categoria_ids = set(cat.id for cat in subcategorias)

    # Map of root_id -> list of descendant ids (including self)
    raiz_descendentes = {}

    for raiz in categorias_raiz:
        descendentes = raiz.get_all_subcategorias(include_self=True)
        descendentes_ids = [c.id for c in descendentes]

        # Se houve filtro por categoria, pular raízes que não contêm a categoria filtrada
        if filtro_categoria_ids is not None and not (set(descendentes_ids) & filtro_categoria_ids):
            continue

        raiz_descendentes[raiz.id] = set(descendentes_ids)

        # Calcular totais a partir da lista de transações já filtrada (ano, conta, tipo, etc.)
        total_receita = sum(t.valor for t in transacoes if t.categoria_id in raiz_descendentes[raiz.id] and t.tipo == TipoTransacao.RECEITA)
        total_despesa = sum(t.valor for t in transacoes if t.categoria_id in raiz_descendentes[raiz.id] and t.tipo == TipoTransacao.DESPESA)

        if total_receita > 0:
            raiz.total_receita = total_receita
            categorias_receitas.append(raiz)

        if total_despesa > 0:
            raiz.total_despesa = total_despesa
            categorias_despesas.append(raiz)

    # ----------------------
    # Agregação por SUBCATEGORIAS
    # ----------------------
    categorias_sub_receitas = []
    categorias_sub_despesas = []

    categorias_sub = Categoria.query.filter(Categoria.user_id == current_user.id, Categoria.parent_id != None).order_by(Categoria.nome).all()
    sub_descendentes = {}
    for sub in categorias_sub:
        descendentes = sub.get_all_subcategorias(include_self=True)
        descendentes_ids = [c.id for c in descendentes]

        # Respeitar filtro por categoria (se houver)
        if filtro_categoria_ids is not None and not (set(descendentes_ids) & filtro_categoria_ids):
            continue

        sub_descendentes[sub.id] = set(descendentes_ids)

        total_receita_sub = sum(t.valor for t in transacoes if t.categoria_id in sub_descendentes[sub.id] and t.tipo == TipoTransacao.RECEITA)
        total_despesa_sub = sum(t.valor for t in transacoes if t.categoria_id in sub_descendentes[sub.id] and t.tipo == TipoTransacao.DESPESA)

        if total_receita_sub > 0:
            sub.total_receita = total_receita_sub
            categorias_sub_receitas.append(sub)

        if total_despesa_sub > 0:
            sub.total_despesa = total_despesa_sub
            categorias_sub_despesas.append(sub)

    # Criar matriz de dados (categoria raiz x mês) sem duplicidade, usando os conjuntos de descendentes
    matriz_dados = {}
    categorias_unicas = {c.id: c for c in (categorias_receitas + categorias_despesas)}
    for categoria_id_key, categoria in categorias_unicas.items():
        matriz_dados[categoria.id] = {}
        descendentes_set = raiz_descendentes.get(categoria.id, {categoria.id})
        for idx, month_start in enumerate(month_starts):
            vistos = set()
            valor_mes = 0
            for t in transacoes:
                if t.categoria_id not in descendentes_set or t.data_transacao.year != month_start.year or t.data_transacao.month != month_start.month:
                    continue
                if t.recorrencia_id:
                    chave = (t.data_transacao.year, t.data_transacao.month, t.recorrencia_id)
                else:
                    chave = (t.data_transacao.year, t.data_transacao.month, t.categoria_id, t.tipo)
                if chave in vistos:
                    continue
                vistos.add(chave)
                valor_mes += t.valor
            matriz_dados[categoria.id][meses[idx]] = valor_mes if valor_mes > 0 else 0
    
    # Debug: imprimir totais_mensais e matriz_dados para inspeção (logger)
    try:
        app.logger.debug('RELATORIO: TOTAIS_MENSAIS')
        for m in meses:
            app.logger.debug('%s: receita=%s, despesa=%s', m, totais_mensais[m]['receita'], totais_mensais[m]['despesa'])
        app.logger.debug('RELATORIO: MATRIZ_DADOS')
        for cat_id, row in matriz_dados.items():
            app.logger.debug('Categoria %s: %s', cat_id, ', '.join([f"{mes}={row.get(mes,0)}" for mes in meses]))
    except Exception as e:
        app.logger.exception('RELATORIO ERROR: %s', e)

    # Preparar linhas por transação para a tabela detalhada
    # Agrupar informação de categoria raiz / subcategoria para exibição
    categorias_map = {c.id: c for c in todas_categorias}
    # Agrupar transações por (descrição normalizada, categoria_raiz, subcategoria) e somar por mês
    grupos = {}
    for t in transacoes:
        # Month label compatível com lista `meses` (ex: 'Jan 2025')
        try:
            month_label = f"{meses_pt[t.data_transacao.month-1]} {t.data_transacao.year}"
        except Exception:
            month_label = None

        # Categoria e subcategoria
        cat = categorias_map.get(t.categoria_id) or (Categoria.query.get(t.categoria_id) if t.categoria_id else None)
        subcategoria_nome = ''
        categoria_raiz_nome = ''
        try:
            if cat:
                if cat.parent_id:
                    subcategoria_nome = cat.nome
                    raiz_temp = cat
                    while raiz_temp and raiz_temp.parent_id:
                        raiz_temp = categorias_map.get(raiz_temp.parent_id) or Categoria.query.get(raiz_temp.parent_id)
                    categoria_raiz_nome = raiz_temp.nome if raiz_temp else ''
                else:
                    categoria_raiz_nome = cat.nome
        except Exception:
            categoria_raiz_nome = getattr(cat, 'nome', '') if cat else ''
        # Normalizar descrição para agrupar independentemente de caixa/espacos
        raw_desc = (getattr(t, 'descricao', '') or '').strip()
        # Remover sufixos comuns de parcela (ex: ' - Parcela 1/8', 'Parcela-1/8', 'Parcela 1 de 8')
        import re
        cleaned_desc = raw_desc
        # padrão principal: 'parcela X/Y' possivelmente precedido por '-' ou similar
        cleaned_desc = re.sub(r"(?i)\s*(?:[-–—])?\s*parcela\s*\d+\s*[\\/\-]\s*\d+", "", cleaned_desc)
        # padrão alternativo: 'parcela X de Y' ou 'parcela X of Y'
        cleaned_desc = re.sub(r"(?i)\s*(?:[-–—])?\s*parcela\s*\d+\s*(?:de|of)\s*\d+", "", cleaned_desc)
        # remover termos isolados como 'parcela X' no final
        cleaned_desc = re.sub(r"(?i)\s*(?:[-–—])?\s*parcela\s*\d+\s*$", "", cleaned_desc)
        # limpar espaços redundantes e traços finais
        cleaned_desc = cleaned_desc.strip().rstrip('-').strip()

        norm_desc = ' '.join(cleaned_desc.split()).lower()

        chave = (norm_desc, categoria_raiz_nome or '', subcategoria_nome or '')

        if chave not in grupos:
            # inicializar mapas mensais (total, real e projetado) com zeros para todos os meses
            monthly = {m: 0 for m in meses}
            monthly_real = {m: 0 for m in meses}
            monthly_proj = {m: 0 for m in meses}
            grupos[chave] = {
                # descrição exibida: usar a versão limpa (sem texto de parcela) para agrupar
                'descricao': cleaned_desc or raw_desc,
                'categoria_raiz': categoria_raiz_nome or '',
                'subcategoria': subcategoria_nome or '',
                'monthly': monthly,
                'monthly_real': monthly_real,
                'monthly_proj': monthly_proj,
                'total': 0,
                'is_projetada': getattr(t, 'is_projetada', False)
            }
            # coletar variantes originais para fallback
            grupos[chave].setdefault('_orig_variants', [])

        # registrar variante original (para preservar capitalização quando não houver consolidada)
        if raw_desc and raw_desc not in grupos[chave].get('_orig_variants', []):
            grupos[chave]['_orig_variants'].append(raw_desc)

        # somar valor no mês correto (se o mês estiver dentro do período)
        if month_label and month_label in grupos[chave]['monthly']:
            # sempre atualizar o total combinado
            grupos[chave]['monthly'][month_label] += t.valor
            grupos[chave]['total'] += t.valor
            # e também atualizar as partições real vs projetada
            if getattr(t, 'is_projetada', False):
                grupos[chave]['monthly_proj'][month_label] += t.valor
            else:
                grupos[chave]['monthly_real'][month_label] += t.valor
        else:
            # valores fora do período somam para o total geral
            grupos[chave]['total'] += t.valor

        # se encontrarmos uma transação real (não projetada), preferi-la como label exibido
        if not getattr(t, 'is_projetada', False):
            grupos[chave]['descricao'] = raw_desc

        # qualquer transação projetada marca o grupo como projetado (mas não cria nova linha)
        if getattr(t, 'is_projetada', False):
            grupos[chave]['is_projetada'] = True

    # Preparar lista final: usar a variante original mais legível como descrição exibida
    for g in grupos.values():
        if (not g.get('descricao')) and g.get('_orig_variants'):
            g['descricao'] = g['_orig_variants'][0]
        # remover campo auxiliar antes de enviar ao template
        if '_orig_variants' in g:
            del g['_orig_variants']

    # Converter para lista ordenada por descrição (caso-insensitivo)
    transacoes_linhas = sorted(list(grupos.values()), key=lambda g: (g.get('descricao') or '').lower())

    # Garantir que valores usados no template para seleção sejam strings (ou vazio)
    categoria_for_template = str(categoria_id) if categoria_id is not None else ''
    conta_for_template = str(conta_id) if conta_id is not None else ''

    # DEBUG: imprimir primeiras linhas agrupadas para facilitar troubleshooting nos testes
    try:
        app.logger.debug('DEBUG_MESES: %s', meses)
        app.logger.debug('DEBUG_TRANSACOES_LINHAS: %s', transacoes_linhas[:5])
        for g in transacoes_linhas[:5]:
            app.logger.debug('DEBUG_KEYS_MONTHLY: %s', list(g['monthly'].keys()))
    except Exception:
        pass

    return render_template('relatorios.html',
                         anos_disponiveis=anos_disponiveis,
                         ano=ano,
                         tipo=tipo,
                         categoria=categoria_for_template,
                         conta=conta_for_template,
                         todas_categorias=todas_categorias,
                         todas_contas=todas_contas,
                         meses=meses,
                         totais_mensais=totais_mensais,
                         total_receitas=total_receitas,
                         total_despesas=total_despesas,
                         saldo_geral=saldo_geral,
                         total_transacoes=total_transacoes,
                         categorias_receitas=categorias_receitas,
                         categorias_despesas=categorias_despesas,
                         categorias_sub_receitas=categorias_sub_receitas,
                         categorias_sub_despesas=categorias_sub_despesas,
                         matriz_dados=matriz_dados,
                         transacoes_linhas=transacoes_linhas)

@app.route('/api/comparar-contas-ano')
@login_required
def api_comparar_contas_ano():
    """Retorna comparação mensal (net) por conta para um ano.

    Query params:
      - year (int): ano para calcular (padrão: ano atual)
      - contas (csv ids): opcional, filtrar contas específicas

    Response JSON:
      {
        'success': True,
        'year': 2025,
        'months': ['Jan 2025', ...],
        'accounts': [
           {'id': 1, 'nome': 'Conta X', 'cor': '#abc', 'monthly': [..12 values..], 'total': 123.45},
           ...
        ]
      }
    """
    try:
        try:
            year = int(request.args.get('year', datetime.now().year))
        except Exception:
            year = datetime.now().year

        # Optional filter: contas=1,2,3
        contas_param = request.args.get('contas')
        if contas_param:
            try:
                conta_ids = [int(x) for x in contas_param.split(',') if x.strip()]
                contas = Conta.query.filter(Conta.user_id == current_user.id, Conta.id.in_(conta_ids)).all()
            except Exception:
                contas = Conta.query.filter_by(user_id=current_user.id).all()
        else:
            contas = Conta.query.filter_by(user_id=current_user.id).all()

        # Fetch transactions for the year
        periodo_inicio = datetime(year, 1, 1)
        periodo_fim = datetime(year, 12, 31, 23, 59, 59)
        transacoes = Transacao.query.filter(
            Transacao.user_id == current_user.id,
            Transacao.data_transacao >= periodo_inicio,
            Transacao.data_transacao <= periodo_fim
        ).all()

        # Also include projected transactions from recorrentes so the chart reflects projections
        try:
            # determine months ahead needed from today to include the target year
            hoje = datetime.utcnow()
            meses_needed = max(0, (year - hoje.year) * 12 + (12 - hoje.month) + 1)

            # fetch recorrentes (optionally filter by contas if provided)
            recorrentes_q = TransacaoRecorrente.query.filter_by(user_id=current_user.id)
            if contas_param and 'conta_ids' in locals():
                recorrentes_q = recorrentes_q.filter(TransacaoRecorrente.conta_id.in_(conta_ids))
            recorrentes = recorrentes_q.all()

            for recorrente in recorrentes:
                try:
                    proj = recorrente.gerar_transacoes_pendentes(meses_futuros=meses_needed, apenas_projetar=True)
                    # filtrar apenas as projeções que caem dentro do ano solicitado
                    for p in proj:
                        if p and hasattr(p, 'data_transacao') and periodo_inicio <= p.data_transacao <= periodo_fim:
                            transacoes.append(p)
                except Exception:
                    # segurança: não falhar toda a API por problema em uma recorrência
                    app.logger.exception('Erro ao gerar projeções para recorrente %s', getattr(recorrente, 'id', None))
        except Exception:
            app.logger.exception('Erro ao coletar projeções de recorrentes')

        # Prepare months labels
        meses_pt = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        months = [f"{meses_pt[m-1]} {year}" for m in range(1,13)]

        # Group transactions by conta and month (net: receita +, despesa -)
        accounts_data = []
        for conta in contas:
            monthly = [0.0] * 12
            for t in transacoes:
                if t.conta_id != conta.id:
                    continue
                m = t.data_transacao.month - 1
                if t.tipo == TipoTransacao.RECEITA:
                    monthly[m] += t.valor
                else:
                    monthly[m] -= t.valor
            total = sum(monthly)
            accounts_data.append({
                'id': conta.id,
                'nome': conta.nome,
                'cor': getattr(conta, 'cor', None),
                'monthly': monthly,
                'total': total
            })

        return jsonify({'success': True, 'year': year, 'months': months, 'accounts': accounts_data})
    except Exception as e:
        app.logger.exception('Erro ao gerar comparação por contas')
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/dados-grafico')
@login_required
def dados_grafico():
    """API para dados dos gráficos"""
    # Ler filtros opcionais via query params (ano, conta)
    conta_id = request.args.get('conta')
    ano = request.args.get('ano')

    # Base filter por usuário
    base_filter = [Transacao.user_id == current_user.id]
    if conta_id:
        try:
            conta_id = int(conta_id)
            base_filter.append(Transacao.conta_id == conta_id)
        except Exception:
            pass
    if ano:
        try:
            ano_int = int(ano)
            base_filter.append(func.strftime('%Y', Transacao.data_transacao) == str(ano_int))
        except Exception:
            pass

    # Dados por categoria (filtrados por usuário e opcionalmente por conta/ano)
    resultado = db.session.query(
        Categoria.nome,
        Categoria.cor,
        func.sum(Transacao.valor)
    ).join(Transacao).filter(*base_filter).group_by(Categoria.nome, Categoria.cor).all()
    
    dados_categoria = {
        'labels': [r[0] for r in resultado],
        'data': [float(r[2]) for r in resultado],
        'colors': [r[1] for r in resultado]
    }
    
    # Dados mensais (filtrados por usuário)
    dados_mensais = db.session.query(
        func.strftime('%Y-%m', Transacao.data_transacao).label('mes'),
        Transacao.tipo,
        func.sum(Transacao.valor)
    ).filter(*base_filter).group_by('mes', Transacao.tipo).all()
    
    # Organizando dados mensais
    meses = {}
    for registro in dados_mensais:
        mes, tipo, valor = registro
        if mes not in meses:
            meses[mes] = {'receitas': 0, 'despesas': 0}
        meses[mes][f'{tipo.value}s'] = float(valor)
    
    dados_tempo = {
        'labels': list(meses.keys()),
        'receitas': [meses[m]['receitas'] for m in meses.keys()],
        'despesas': [meses[m]['despesas'] for m in meses.keys()]
    }
    
    return jsonify({
        'categoria': dados_categoria,
        'tempo': dados_tempo
    })

@app.route('/api/categorias-arvore')
@login_required
def categorias_arvore():
    """API para árvore de categorias"""
    categorias_raiz = Categoria.query.filter_by(parent_id=None, user_id=current_user.id).all()
    return jsonify([cat.to_dict_hierarquico() for cat in categorias_raiz])

@app.route('/api/categorias')
@login_required
def api_categorias():
    """API para lista de categorias com hierarquia do usuário atual"""
    categorias = Categoria.query.filter_by(user_id=current_user.id).all()
    return jsonify([cat.to_dict(include_hierarchy=True) for cat in categorias])

@app.route('/api/categoria/<int:categoria_id>')
@login_required
def api_categoria_detalhes(categoria_id):
    """API para detalhes de uma categoria específica"""
    categoria = Categoria.query.filter_by(id=categoria_id, user_id=current_user.id).first_or_404()
    return jsonify(categoria.to_dict(include_hierarchy=True))

@app.route('/api/tags')
@login_required
def api_tags():
    """API para lista de tags ativas do usuário atual"""
    from models import Tag
    tags = Tag.query.filter_by(user_id=current_user.id, ativa=True).order_by(Tag.nome).all()
    return jsonify([tag.to_dict() for tag in tags])

@app.route('/api/tag/<int:tag_id>')
@login_required
def api_tag_detalhes(tag_id):
    """API para detalhes de uma tag específica"""
    from models import Tag
    tag = Tag.query.filter_by(id=tag_id, user_id=current_user.id).first_or_404()
    return jsonify(tag.to_dict())

# ==================== ROTAS DE TAGS ====================

@app.route('/tags')
@login_required
def tags():
    """Página de gerenciamento de tags"""
    from models import Tag
    todas_tags = Tag.query.filter_by(user_id=current_user.id).order_by(Tag.ativa.desc(), Tag.nome).all()
    
    # Calcular estatísticas
    stats = {
        'total_tags': len(todas_tags),
        'tags_ativas': len([tag for tag in todas_tags if tag.ativa]),
        'tags_inativas': len([tag for tag in todas_tags if not tag.ativa]),
        'tags_em_uso': len([tag for tag in todas_tags if tag.total_transacoes > 0])
    }
    
    return render_template('tags.html', tags=todas_tags, stats=stats)

@app.route('/nova-tag', methods=['GET', 'POST'])
def nova_tag():
    """Criar nova tag"""
    from models import Tag
    from forms import TagForm
    
    form = TagForm()
    
    if form.validate_on_submit():
        try:
            # Verificar se já existe uma tag com o mesmo nome para este usuário
            nome_lower = form.nome.data.strip().lower()
            tag_existente = Tag.query.filter(
                db.func.lower(Tag.nome) == nome_lower,
                Tag.user_id == current_user.id
            ).first()
            
            if tag_existente:
                flash(f'Você já possui uma tag com o nome "{form.nome.data}".', 'error')
                return render_template('nova_tag.html', form=form)
            
            tag = Tag(
                nome=form.nome.data.strip().title(),
                descricao=form.descricao.data,
                cor=form.cor.data,
                ativa=form.ativa.data,
                user_id=current_user.id  # Associar ao usuário atual
            )
            
            db.session.add(tag)
            db.session.commit()
            flash(f'Tag "{tag.nome}" criada com sucesso!', 'success')
            return redirect(url_for('tags'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar tag: {str(e)}', 'error')
    
    return render_template('nova_tag.html', form=form)

@app.route('/editar-tag/<int:tag_id>', methods=['GET', 'POST'])
def editar_tag(tag_id):
    """Editar tag existente"""
    from models import Tag
    from forms import TagForm
    
    tag = Tag.query.get_or_404(tag_id)
    form = TagForm(obj=tag)
    
    if form.validate_on_submit():
        try:
            # Verificar se já existe outra tag com o mesmo nome
            nome_lower = form.nome.data.strip().lower()
            tag_existente = Tag.query.filter(
                db.and_(
                    db.func.lower(Tag.nome) == nome_lower,
                    Tag.id != tag_id
                )
            ).first()
            
            if tag_existente:
                flash(f'Já existe outra tag com o nome "{form.nome.data}".', 'error')
                return render_template('editar_tag.html', form=form, tag=tag)
            
            tag.nome = form.nome.data.strip().title()
            tag.descricao = form.descricao.data
            tag.cor = form.cor.data
            tag.ativa = form.ativa.data
            
            db.session.commit()
            flash(f'Tag "{tag.nome}" atualizada com sucesso!', 'success')
            return redirect(url_for('tags'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar tag: {str(e)}', 'error')
    
    return render_template('editar_tag.html', form=form, tag=tag)

@app.route('/excluir-tag/<int:tag_id>', methods=['POST'])
def excluir_tag(tag_id):
    """Excluir tag"""
    from models import Tag
    
    try:
        tag = Tag.query.get_or_404(tag_id)
        
        # Verificar se a tag está sendo usada
        if tag.total_transacoes > 0:
            return jsonify({
                'success': False, 
                'message': f'Não é possível excluir a tag "{tag.nome}" pois ela está sendo usada em {tag.total_transacoes} transação(ões). Desative-a ao invés de excluir.'
            })
        
        nome_tag = tag.nome
        db.session.delete(tag)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Tag "{nome_tag}" excluída com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'Erro ao excluir tag: {str(e)}'
        })

@app.route('/toggle-tag-status/<int:tag_id>', methods=['POST'])
def toggle_tag_status(tag_id):
    """Ativar/Desativar tag"""
    from models import Tag
    
    try:
        tag = Tag.query.get_or_404(tag_id)
        tag.ativa = not tag.ativa
        db.session.commit()
        
        status = "ativada" if tag.ativa else "desativada"
        return jsonify({
            'success': True, 
            'message': f'Tag "{tag.nome}" {status} com sucesso!',
            'nova_status': tag.ativa
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'Erro ao alterar status da tag: {str(e)}'
        })

@app.route('/editar-categoria/<int:categoria_id>', methods=['GET', 'POST'])
@login_required
def editar_categoria(categoria_id):
    """Edita uma categoria existente"""
    categoria = Categoria.query.filter_by(id=categoria_id, user_id=current_user.id).first_or_404()
    form = CategoriaForm(obj=categoria)
    
    # Remover a própria categoria e suas subcategorias das opções de parent
    categorias_disponiveis = []
    todas_categorias = Categoria.query.filter_by(user_id=current_user.id).all()
    categoria_e_subcategorias = categoria.get_all_subcategorias(include_self=True)
    ids_proibidos = [cat.id for cat in categoria_e_subcategorias]
    
    for cat in todas_categorias:
        if cat.id not in ids_proibidos:
            categorias_disponiveis.append(cat)
    
    # Reconstruir choices do formulário
    form.parent_id.choices = [(0, 'Nenhuma (Categoria Raiz)')]
    
    def add_categoria_choices(cat, prefix=""):
        """Adiciona categoria e suas subcategorias recursivamente"""
        if cat.id not in ids_proibidos:
            display_name = f"{prefix}{cat.nome}"
            form.parent_id.choices.append((cat.id, display_name))
            
            for subcategoria in cat.subcategorias:
                if subcategoria.id not in ids_proibidos:
                    add_categoria_choices(subcategoria, f"{prefix}└─ ")
    
    # Adicionar categorias disponíveis
    categorias_raiz = Categoria.query.filter_by(parent_id=None, user_id=current_user.id).all()
    categorias_raiz_filtradas = [cat for cat in categorias_raiz if cat.id not in ids_proibidos]
    for cat in categorias_raiz_filtradas:
        add_categoria_choices(cat)
    
    if form.validate_on_submit():
        # Verificar se não está tentando criar um ciclo
        novo_parent_id = form.parent_id.data if form.parent_id.data != 0 else None
        
        if novo_parent_id and novo_parent_id in ids_proibidos:
            flash('Erro: Não é possível criar uma referência circular!', 'danger')
        else:
            categoria.nome = form.nome.data
            categoria.descricao = form.descricao.data
            categoria.cor = form.cor.data
            categoria.parent_id = novo_parent_id
            
            db.session.commit()
            flash('Categoria atualizada com sucesso!', 'success')
            return redirect(url_for('categorias'))
    
    return render_template('editar_categoria.html', form=form, categoria=categoria)

@app.route('/api/categoria/<int:categoria_id>', methods=['PUT'])
@login_required
def api_editar_categoria(categoria_id):
    """API para editar categoria via AJAX"""
    categoria = Categoria.query.filter_by(id=categoria_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    
    try:
        if 'nome' in data:
            categoria.nome = data['nome']
        if 'descricao' in data:
            categoria.descricao = data['descricao']
        if 'cor' in data:
            categoria.cor = data['cor']
        if 'parent_id' in data:
            novo_parent_id = data['parent_id'] if data['parent_id'] != 0 else None
            
            # Verificar referência circular
            if novo_parent_id:
                categoria_e_subcategorias = categoria.get_all_subcategorias(include_self=True)
                ids_proibidos = [cat.id for cat in categoria_e_subcategorias]
                
                if novo_parent_id in ids_proibidos:
                    return jsonify({'error': 'Referência circular não permitida'}), 400
            
            categoria.parent_id = novo_parent_id
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Categoria atualizada com sucesso',
            'categoria': categoria.to_dict(include_hierarchy=True)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/categoria/<int:categoria_id>', methods=['DELETE'])
@login_required
def api_excluir_categoria(categoria_id):
    """API para excluir categoria via AJAX"""
    categoria = Categoria.query.filter_by(id=categoria_id, user_id=current_user.id).first_or_404()
    
    try:
        # Verificar se tem transações associadas
        if len(categoria.transacoes) > 0:
            return jsonify({
                'error': f'Não é possível excluir. A categoria possui {len(categoria.transacoes)} transação(ões) associada(s).'
            }), 400
        
        # Verificar se tem subcategorias
        if len(categoria.subcategorias) > 0:
            return jsonify({
                'error': f'Não é possível excluir. A categoria possui {len(categoria.subcategorias)} subcategoria(s).'
            }), 400
        
        nome_categoria = categoria.nome
        db.session.delete(categoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Categoria "{nome_categoria}" excluída com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============ ROTAS DE TRANSAÇÕES RECORRENTES ============

@app.route('/transacoes-recorrentes')
@login_required
def transacoes_recorrentes():
    """Lista todas as transações recorrentes"""
    recorrentes = TransacaoRecorrente.query.filter_by(user_id=current_user.id).all()
    return render_template('transacoes_recorrentes.html', recorrentes=recorrentes)

@app.route('/nova-transacao-recorrente', methods=['GET', 'POST'])
@login_required
def nova_transacao_recorrente():
    """Cria uma nova transação recorrente"""
    form = TransacaoRecorrenteForm(user_id=current_user.id)
    
    # Carregar opções filtradas por usuário
    categorias = Categoria.query.filter_by(user_id=current_user.id).all()
    contas = Conta.query.filter_by(user_id=current_user.id).all()
    
    form.categoria_id.choices = [(c.id, c.nome) for c in categorias]
    form.conta_id.choices = [(c.id, c.nome) for c in contas]
    
    if form.validate_on_submit():
        try:
            # Criar a transação recorrente
            recorrente = TransacaoRecorrente(
                descricao=form.descricao.data,
                valor=form.valor.data,
                tipo=TipoTransacao(form.tipo.data),
                tipo_recorrencia=TipoRecorrencia(form.tipo_recorrencia.data),
                data_inicio=form.data_inicio.data,
                data_fim=form.data_fim.data,
                forma_pagamento_id=int(form.forma_pagamento.data) if form.forma_pagamento.data else None,
                categoria_id=form.categoria_id.data,
                conta_id=form.conta_id.data,
                total_parcelas=form.total_parcelas.data if form.is_parcelada.data else None,
                user_id=current_user.id
            )

            db.session.add(recorrente)
            db.session.commit()
            
            # Definir horizonte de meses futuros (usar valor padrão da configuração)
            meses_futuros = app.config.get('MESES_FUTUROS_DEFAULT', 36)
            
            # Se tem data_fim, usar isso como limite
            if recorrente.data_fim:
                # Gerar transações passadas e projetar futuras
                transacoes_geradas = recorrente.gerar_transacoes_pendentes(apenas_projetar=True)
                transacoes_reais = [t for t in transacoes_geradas if not hasattr(t, 'is_projetada') or not t.is_projetada]
                projecoes = [t for t in transacoes_geradas if hasattr(t, 'is_projetada') and t.is_projetada]
                mensagem = f'Transação recorrente criada! {len(transacoes_reais)} transação(ões) gerada(s) e {len(projecoes)} projetada(s) até {recorrente.data_fim.strftime("%d/%m/%Y")}.'
            else:
                # Gerar transações para os próximos meses
                transacoes_geradas = recorrente.gerar_transacoes_pendentes(meses_futuros=meses_futuros, apenas_projetar=True)
                transacoes_reais = [t for t in transacoes_geradas if not hasattr(t, 'is_projetada') or not t.is_projetada]
                projecoes = [t for t in transacoes_geradas if hasattr(t, 'is_projetada') and t.is_projetada]
                mensagem = f'Transação recorrente criada! {len(transacoes_reais)} transação(ões) gerada(s) e {len(projecoes)} projetada(s) para os próximos {meses_futuros} meses.'
            
            flash(mensagem, 'success')
            return redirect(url_for('transacoes_recorrentes'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar transação recorrente: {str(e)}', 'error')
    
    return render_template('nova_transacao_recorrente.html', form=form)

@app.route('/editar-transacao-recorrente/<int:recorrente_id>', methods=['GET', 'POST'])
@login_required
def editar_transacao_recorrente(recorrente_id):
    """Edita uma transação recorrente"""
    recorrente = TransacaoRecorrente.query.filter_by(id=recorrente_id, user_id=current_user.id).first_or_404()
    form = TransacaoRecorrenteForm(obj=recorrente, user_id=current_user.id)
    
    # Carregar opções filtradas por usuário
    categorias = Categoria.query.filter_by(user_id=current_user.id).all()
    contas = Conta.query.filter_by(user_id=current_user.id).all()
    
    form.categoria_id.choices = [(c.id, c.nome) for c in categorias]
    form.conta_id.choices = [(c.id, c.nome) for c in contas]
    
    # Configurar campos específicos
    if request.method == 'GET':
        form.tipo.data = recorrente.tipo.value
        form.tipo_recorrencia.data = recorrente.tipo_recorrencia.value
        form.is_parcelada.data = recorrente.is_parcelada
    
    if form.validate_on_submit():
        try:
            recorrente.descricao = form.descricao.data
            recorrente.valor = form.valor.data
            recorrente.tipo = TipoTransacao(form.tipo.data)
            recorrente.tipo_recorrencia = TipoRecorrencia(form.tipo_recorrencia.data)
            recorrente.data_inicio = form.data_inicio.data
            recorrente.data_fim = form.data_fim.data
            recorrente.forma_pagamento_id = int(form.forma_pagamento.data) if form.forma_pagamento.data else None
            recorrente.categoria_id = form.categoria_id.data
            recorrente.conta_id = form.conta_id.data
            recorrente.total_parcelas = form.total_parcelas.data if form.is_parcelada.data else None
            
            db.session.commit()
            flash('Transação recorrente atualizada com sucesso!', 'success')
            return redirect(url_for('transacoes_recorrentes'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar transação recorrente: {str(e)}', 'error')
    
    return render_template('editar_transacao_recorrente.html', form=form, recorrente=recorrente)

@app.route('/api/transacao-recorrente/<int:recorrente_id>/gerar')
@login_required
def gerar_transacoes_pendentes(recorrente_id):
    """Gera manualmente as transações pendentes de uma recorrência"""
    try:
        # Parâmetro para número de meses (usa helper que aplica limites/config)
        meses_futuros = obter_meses_futuros_from_request()
        
        recorrente = TransacaoRecorrente.query.filter_by(id=recorrente_id, user_id=current_user.id).first_or_404()
        
        # Se tem data_fim, usar isso como limite
        if recorrente.data_fim:
            # Gerar transações passadas e projetar futuras
            transacoes_geradas = recorrente.gerar_transacoes_pendentes(apenas_projetar=True)
            transacoes_reais = [t for t in transacoes_geradas if not hasattr(t, 'is_projetada') or not t.is_projetada]
            projecoes = [t for t in transacoes_geradas if hasattr(t, 'is_projetada') and t.is_projetada]
            mensagem = f'{len(transacoes_reais)} transação(ões) gerada(s) e {len(projecoes)} projetada(s) até {recorrente.data_fim.strftime("%d/%m/%Y")}'
        else:
            # Gerar transações para os próximos meses
            transacoes_geradas = recorrente.gerar_transacoes_pendentes(meses_futuros=meses_futuros, apenas_projetar=True)
            transacoes_reais = [t for t in transacoes_geradas if not hasattr(t, 'is_projetada') or not t.is_projetada]
            projecoes = [t for t in transacoes_geradas if hasattr(t, 'is_projetada') and t.is_projetada]
            mensagem = f'{len(transacoes_reais)} transação(ões) gerada(s) e {len(projecoes)} projetada(s) para os próximos {meses_futuros} meses'
        
        return jsonify({
            'success': True,
            'message': mensagem,
            'transacoes_geradas': len(transacoes_geradas),
            'meses_futuros': meses_futuros,
            'tem_data_fim': recorrente.data_fim is not None,
            'data_fim': recorrente.data_fim.strftime('%d/%m/%Y') if recorrente.data_fim else None
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/transacao-recorrente/<int:recorrente_id>/pausar', methods=['POST'])
@login_required
def pausar_transacao_recorrente(recorrente_id):
    """Pausa ou reativa uma transação recorrente"""
    try:
        recorrente = TransacaoRecorrente.query.filter_by(id=recorrente_id, user_id=current_user.id).first_or_404()
        
        if recorrente.status == StatusRecorrencia.ATIVA:
            recorrente.status = StatusRecorrencia.PAUSADA
            message = 'Transação recorrente pausada'
        elif recorrente.status == StatusRecorrencia.PAUSADA:
            recorrente.status = StatusRecorrencia.ATIVA
            message = 'Transação recorrente reativada'
        else:
            return jsonify({'success': False, 'message': 'Transação já foi finalizada'}), 400
        
        db.session.commit()
        return jsonify({'success': True, 'message': message, 'status': recorrente.status.value})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/transacao-recorrente/<int:recorrente_id>/finalizar', methods=['POST'])
@login_required
def finalizar_transacao_recorrente(recorrente_id):
    """Finaliza uma transação recorrente"""
    try:
        recorrente = TransacaoRecorrente.query.filter_by(id=recorrente_id, user_id=current_user.id).first_or_404()
        recorrente.status = StatusRecorrencia.FINALIZADA
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Transação recorrente finalizada'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/transacoes-recorrentes')
@login_required
def api_transacoes_recorrentes():
    """API para listar transações recorrentes"""
    recorrentes = TransacaoRecorrente.query.filter_by(user_id=current_user.id).all()
    return jsonify([r.to_dict() for r in recorrentes])

@app.route('/api/projetar-transacoes-futuras')
@login_required
def projetar_transacoes_futuras():
    """Projeta transações futuras sem salvá-las no banco de dados"""
    try:
        # Parâmetro para número de meses (usa helper que aplica limites/config)
        meses_futuros = obter_meses_futuros_from_request()
        
        recorrentes_ativas = TransacaoRecorrente.query.filter_by(
            status=StatusRecorrencia.ATIVA, 
            user_id=current_user.id
        ).all()
        
        # Lista para armazenar todas as projeções
        projecoes = []
        # ID temporário para projeções (negativo para evitar conflitos)
        next_temp_id = -1
        
        # Data atual para separar transações existentes de projeções
        hoje = datetime.utcnow().date()
        
        for recorrente in recorrentes_ativas:
            # Determinar a data limite de projeção
            if recorrente.data_fim:
                data_limite = recorrente.data_fim
            else:
                data_limite = datetime.utcnow() + relativedelta(months=meses_futuros)
            
            # Obter a última transação existente
            ultima_transacao = Transacao.query.filter_by(
                recorrencia_id=recorrente.id
            ).order_by(Transacao.data_transacao.desc()).first()
            
            # Determinar a data da próxima projeção
            if ultima_transacao:
                proxima_data = recorrente.calcular_proxima_data(ultima_transacao.data_transacao)
            else:
                proxima_data = recorrente.data_inicio
            
            # Gerar projeções
            while proxima_data and proxima_data <= data_limite:
                # Verificar se já é uma transação consolidada
                transacao_existente = Transacao.query.filter_by(
                    recorrencia_id=recorrente.id,
                    data_transacao=proxima_data
                ).first()
                
                if transacao_existente:
                    # Adicionar à lista como consolidada
                    projecoes.append({
                        'id': transacao_existente.id,
                        'descricao': transacao_existente.descricao,
                        'valor': transacao_existente.valor,
                        'tipo': transacao_existente.tipo.value,
                        'data': transacao_existente.data_transacao.strftime('%Y-%m-%d'),
                        'forma_pagamento': transacao_existente.forma_pagamento.nome if transacao_existente.forma_pagamento else None,
                        'categoria': transacao_existente.categoria.nome,
                        'categoria_cor': transacao_existente.categoria.cor,
                        'conta': transacao_existente.conta.nome,
                        'conta_cor': transacao_existente.conta.cor,
                        'recorrencia_id': recorrente.id,
                        'status': 'consolidada'
                    })
                else:
                    # Adicionar como projeção não consolidada
                    # Apenas se a data for futura
                    if proxima_data.date() >= hoje:
                        projecoes.append({
                            'id': next_temp_id,
                            'descricao': recorrente.descricao,
                            'valor': recorrente.valor,
                            'tipo': recorrente.tipo.value,
                            'data': proxima_data.strftime('%Y-%m-%d'),
                            'categoria': recorrente.categoria.nome,
                            'categoria_cor': recorrente.categoria.cor,
                            'conta': recorrente.conta.nome,
                            'conta_cor': recorrente.conta.cor,
                            'forma_pagamento': recorrente.forma_pagamento.nome if recorrente.forma_pagamento else None,
                            'recorrencia_id': recorrente.id,
                            'status': 'projetada'
                        })
                        next_temp_id -= 1
                
                # Calcular próxima data
                proxima_data = recorrente.calcular_proxima_data(proxima_data)
                
                # Verificar se atingimos o limite de parcelas para recorrências parceladas
                if recorrente.is_parcelada:
                    parcelas_projetadas = len([p for p in projecoes if p['recorrencia_id'] == recorrente.id])
                    if recorrente.parcelas_geradas + parcelas_projetadas >= recorrente.total_parcelas:
                        break
        
        return jsonify({
            'success': True,
            'projecoes': projecoes,
            'total_projecoes': len(projecoes),
            'projecoes_consolidadas': len([p for p in projecoes if p['status'] == 'consolidada']),
            'projecoes_pendentes': len([p for p in projecoes if p['status'] == 'projetada']),
            'meses_futuros': meses_futuros
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/cidades')
def api_cidades():
    """Retorna sugestões de cidades a partir do parâmetro q (substring, case-insensitive)."""
    q = request.args.get('q', '', type=str).strip()
    if not q:
        return jsonify({'success': True, 'results': []})

    cidades = _load_cidades()
    q_lower = q.lower()
    matches = [c for c in cidades if q_lower in c.lower()]
    # limitar resultados
    matches = matches[:10]
    return jsonify({'success': True, 'results': matches})

@app.route('/api/consolidar-projecoes', methods=['POST'])
@login_required
def consolidar_projecoes():
    """Consolida projeções selecionadas, salvando-as no banco de dados"""
    try:
        data = request.json or {}
        projecoes_ids = data.get('projecoes_ids', [])

        app.logger.info(f"Solicitação para consolidar projeções: {projecoes_ids}")

        if not projecoes_ids:
            return jsonify({'success': False, 'message': 'Nenhuma projeção selecionada'}), 400

        # Filtrar apenas IDs negativos (projeções não consolidadas)
        projecoes_ids = [int(pid) for pid in projecoes_ids if int(pid) < 0]
        if not projecoes_ids:
            return jsonify({'success': False, 'message': 'Todas as projeções selecionadas já estão consolidadas'}), 400

        consolidadas = []
        erros = []

        for projecao_id in projecoes_ids:
            key_rec = f'recorrencia_{abs(projecao_id)}'
            key_data = f'data_{abs(projecao_id)}'
            recorrencia_id = data.get(key_rec)
            data_projecao = data.get(key_data)

            if not recorrencia_id or not data_projecao:
                erros.append(f'Dados incompletos para projeção {projecao_id}')
                continue

            try:
                recorrente = TransacaoRecorrente.query.filter_by(id=int(recorrencia_id), user_id=current_user.id).first()
                if not recorrente:
                    erros.append(f'Recorrência {recorrencia_id} não encontrada')
                    continue

                data_dt = datetime.strptime(data_projecao, '%Y-%m-%d')

                # Verificar se já existe transação para essa data
                existente = Transacao.query.filter_by(recorrencia_id=recorrente.id, data_transacao=data_dt).first()
                if existente:
                    erros.append(f'Transação para {data_projecao} já existe')
                    continue

                nova_transacao = Transacao(
                    descricao=recorrente.descricao,
                    valor=recorrente.valor,
                    tipo=recorrente.tipo,
                    data_transacao=data_dt,
                    categoria_id=recorrente.categoria_id,
                    conta_id=recorrente.conta_id,
                    recorrencia_id=recorrente.id,
                    user_id=current_user.id
                )

                db.session.add(nova_transacao)

                if recorrente.is_parcelada:
                    recorrente.parcelas_geradas += 1
                    if recorrente.parcelas_geradas >= recorrente.total_parcelas:
                        recorrente.status = StatusRecorrencia.FINALIZADA

                consolidadas.append(projecao_id)
                app.logger.info(f"Projeção ID {projecao_id} consolidada para {data_projecao}")

            except Exception as e:
                erros.append(f'Erro ao processar projeção {projecao_id}: {str(e)}')

        if consolidadas:
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': f'Erro ao salvar transações: {str(e)}'}), 500

        if not consolidadas:
            return jsonify({'success': False, 'message': f'Nenhuma projeção consolidada. Erros: {"; ".join(erros)}'}), 400

        return jsonify({'success': True, 'message': f'{len(consolidadas)} projeção(ões) consolidada(s) com sucesso', 'consolidadas': consolidadas})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/gerar-todas-transacoes-pendentes')
@login_required
def gerar_todas_transacoes_pendentes():
    """Gera todas as transações pendentes de todas as recorrências ativas"""
    try:
        # Parâmetro para número de meses (usa helper que aplica limites/config)
        meses_futuros = obter_meses_futuros_from_request()
        
        recorrentes_ativas = TransacaoRecorrente.query.filter_by(
            status=StatusRecorrencia.ATIVA, 
            user_id=current_user.id
        ).all()
        total_transacoes_geradas = 0
        recorrentes_com_data_fim = 0
        
        for recorrente in recorrentes_ativas:
            # Se tem data_fim, usar isso como limite
            if recorrente.data_fim:
                transacoes_geradas = recorrente.gerar_transacoes_pendentes(apenas_projetar=True)
                recorrentes_com_data_fim += 1
            else:
                # Gerar transações para os próximos meses
                transacoes_geradas = recorrente.gerar_transacoes_pendentes(meses_futuros=meses_futuros, apenas_projetar=True)
            
            total_transacoes_geradas += len(transacoes_geradas)
        
        # Construir mensagem personalizada
        if recorrentes_com_data_fim > 0 and recorrentes_com_data_fim < len(recorrentes_ativas):
            mensagem = f'{total_transacoes_geradas} transação(ões) gerada(s): {recorrentes_com_data_fim} recorrência(s) até a data fim e {len(recorrentes_ativas) - recorrentes_com_data_fim} para os próximos {meses_futuros} meses'
        elif recorrentes_com_data_fim == len(recorrentes_ativas):
            mensagem = f'{total_transacoes_geradas} transação(ões) gerada(s) até as datas de fim das recorrências'
        else:
            mensagem = f'{total_transacoes_geradas} transação(ões) gerada(s) para os próximos {meses_futuros} meses'
        
        return jsonify({
            'success': True,
            'message': mensagem,
            'recorrentes_processadas': len(recorrentes_ativas),
            'recorrentes_com_data_fim': recorrentes_com_data_fim,
            'transacoes_geradas': total_transacoes_geradas,
            'meses_futuros': meses_futuros
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def criar_tabelas():
    """Cria as tabelas do banco de dados"""
    with app.app_context():
        db.create_all()
        
        # Criar contas padrão se não existirem
        if not Conta.query.first():
            contas_padrao = [
                Conta(nome="Minha Conta", descricao="Conta principal", tipo=TipoConta.CORRENTE, cor="#007bff"),
                Conta(nome="Conta da Jéssica", descricao="Conta da Jéssica", tipo=TipoConta.CORRENTE, cor="#28a745"),
                Conta(nome="Conta do Gabriel", descricao="Conta do Gabriel", tipo=TipoConta.CORRENTE, cor="#17a2b8"),
                Conta(nome="Dinheiro", descricao="Dinheiro físico", tipo=TipoConta.DINHEIRO, cor="#ffc107"),
                Conta(nome="Cartão de Crédito", descricao="Cartão principal", tipo=TipoConta.CARTAO_CREDITO, cor="#dc3545"),
            ]
            
            for conta in contas_padrao:
                db.session.add(conta)
            
            db.session.commit()
            app.logger.info("✅ Contas padrão criadas!")
        
        # Criar categorias padrão se não existirem
        if not Categoria.query.first():
            # Categorias raiz
            alimentacao = Categoria(nome='Alimentação', descricao='Gastos com comida', cor='#ff6384')
            transporte = Categoria(nome='Transporte', descricao='Gastos com transporte', cor='#36a2eb')
            moradia = Categoria(nome='Moradia', descricao='Aluguel, conta de luz, etc.', cor='#ffce56')
            saude = Categoria(nome='Saúde', descricao='Plano de saúde, medicamentos', cor='#4bc0c0')
            educacao = Categoria(nome='Educação', descricao='Cursos, livros, etc.', cor='#9966ff')
            lazer = Categoria(nome='Lazer', descricao='Entretenimento e diversão', cor='#ff9f40')
            trabalho = Categoria(nome='Trabalho', descricao='Receitas do trabalho', cor='#2ecc71')
            
            # Adicionar categorias raiz
            categorias_raiz = [alimentacao, transporte, moradia, saude, educacao, lazer, trabalho]
            for categoria in categorias_raiz:
                db.session.add(categoria)
            
            db.session.commit()  # Commit para gerar IDs
            
            # Subcategorias de Alimentação
            subcategorias_alimentacao = [
                Categoria(nome='Restaurantes', descricao='Refeições em restaurantes', cor='#ff6384', parent_id=alimentacao.id),
                Categoria(nome='Supermercado', descricao='Compras no supermercado', cor='#ff4757', parent_id=alimentacao.id),
                Categoria(nome='Delivery', descricao='Comida por delivery', cor='#ff3838', parent_id=alimentacao.id),
            ]
            
            # Subcategorias de Transporte
            subcategorias_transporte = [
                Categoria(nome='Combustível', descricao='Gasolina, álcool, diesel', cor='#36a2eb', parent_id=transporte.id),
                Categoria(nome='Transporte Público', descricao='Ônibus, metro, trem', cor='#2f80ed', parent_id=transporte.id),
                Categoria(nome='Uber/Taxi', descricao='Corridas de aplicativo', cor='#1e40af', parent_id=transporte.id),
            ]
            
            # Subcategorias de Moradia
            subcategorias_moradia = [
                Categoria(nome='Aluguel', descricao='Pagamento do aluguel', cor='#ffce56', parent_id=moradia.id),
                Categoria(nome='Contas', descricao='Luz, água, internet, etc.', cor='#ffd93d', parent_id=moradia.id),
                Categoria(nome='Manutenção', descricao='Reparos e melhorias', cor='#ffb347', parent_id=moradia.id),
            ]
            
            # Subcategorias de Trabalho
            subcategorias_trabalho = [
                Categoria(nome='Salário', descricao='Salário principal', cor='#2ecc71', parent_id=trabalho.id),
                Categoria(nome='Freelance', descricao='Trabalhos extras', cor='#27ae60', parent_id=trabalho.id),
                Categoria(nome='Investimentos', descricao='Rendimentos de investimentos', cor='#16a085', parent_id=trabalho.id),
            ]
            
            # Adicionar todas as subcategorias
            todas_subcategorias = (subcategorias_alimentacao + subcategorias_transporte + 
                                 subcategorias_moradia + subcategorias_trabalho)
            
            for subcategoria in todas_subcategorias:
                db.session.add(subcategoria)
            
            db.session.commit()
            
            # Exemplo de subcategorias de terceiro nível
            # Subcategorias de Restaurantes
            restaurante_id = Categoria.query.filter_by(nome='Restaurantes').first().id
            subcategorias_restaurantes = [
                Categoria(nome='Fast Food', descricao='McDonald\'s, KFC, etc.', cor='#ff6b6b', parent_id=restaurante_id),
                Categoria(nome='Comida Japonesa', descricao='Sushi, yakisoba, etc.', cor='#ee5a24', parent_id=restaurante_id),
                Categoria(nome='Pizzaria', descricao='Pizza e massas', cor='#ff9ff3', parent_id=restaurante_id),
            ]
            
            for subcategoria in subcategorias_restaurantes:
                db.session.add(subcategoria)
            
            db.session.commit()
            app.logger.info("✅ Categorias hierárquicas criadas com sucesso!")

@app.route('/admin/limpar-todas-transacoes', methods=['POST'])
@app.route('/admin/limpar-transacoes', methods=['POST'])
@login_required
def limpar_todas_transacoes():
    if not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('admin'))

    try:
        # Primeiro apaga todas as associações de tags
        from sqlalchemy import text
        db.session.execute(text('DELETE FROM transacao_tags'))
        db.session.commit()
        # Depois apaga todas as transações
        Transacao.query.delete()
        db.session.commit()
        # Depois apaga todas as recorrências
        TransacaoRecorrente.query.delete()
        db.session.commit()
        flash('Todas as transações, tags e recorrências foram removidas com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erro ao limpar transações: {e}', 'danger')
    return redirect(url_for('admin'))

@app.route('/admin')
@login_required
def admin():
    """Página administrativa - apenas para admins"""
    # VERIFICAR SE É ADMIN
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Estatísticas GLOBAIS para admin
    total_usuarios = Usuario.query.count()
    total_transacoes = Transacao.query.count()
    total_recorrentes = TransacaoRecorrente.query.count()
    
    # Listar usuários para o admin
    usuarios = Usuario.query.all()
    
    return render_template('admin.html', 
                          total_usuarios=total_usuarios,
                          total_transacoes=total_transacoes,
                          total_recorrentes=total_recorrentes,
                          usuarios=usuarios)

# === ROTAS DE ADMINISTRAÇÃO DE CATEGORIAS PADRÃO ===

@app.route('/admin/adicionar-categorias-padrao/<int:user_id>')
@login_required
def admin_adicionar_categorias_padrao(user_id):
    """Adiciona categorias padrão a um usuário existente"""
    # Verificar se é administrador
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem acessar esta página.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Verificar se o usuário existe
    usuario = Usuario.query.get(user_id)
    try:
        # Parâmetro para número de meses (usa helper que aplica limites/config)
        meses_futuros = obter_meses_futuros_from_request()
        recorrentes_ativas = TransacaoRecorrente.query.filter_by(
            status=StatusRecorrencia.ATIVA, 
            user_id=current_user.id
        ).all()
        total_transacoes_geradas = 0
        recorrentes_com_data_fim = 0
        for recorrente in recorrentes_ativas:
            # Se tem data_fim, usar isso como limite
            if recorrente.data_fim:
                transacoes_geradas = recorrente.gerar_transacoes_pendentes(apenas_projetar=True)
                recorrentes_com_data_fim += 1
            else:
                # Gerar transações para os próximos meses
                transacoes_geradas = recorrente.gerar_transacoes_pendentes(meses_futuros=meses_futuros, apenas_projetar=True)
            total_transacoes_geradas += len(transacoes_geradas)
        # Construir mensagem personalizada
        if recorrentes_com_data_fim > 0 and recorrentes_com_data_fim < len(recorrentes_ativas):
            mensagem = f'{total_transacoes_geradas} transação(ões) gerada(s): {recorrentes_com_data_fim} recorrência(s) até a data fim e {len(recorrentes_ativas) - recorrentes_com_data_fim} para os próximos {meses_futuros} meses'
        elif recorrentes_com_data_fim == len(recorrentes_ativas):
            mensagem = f'{total_transacoes_geradas} transação(ões) gerada(s) até as datas de fim das recorrências'
        else:
            mensagem = f'{total_transacoes_geradas} transação(ões) gerada(s) para os próximos {meses_futuros} meses'
        return jsonify({
            'success': True,
            'message': mensagem,
            'recorrentes_processadas': len(recorrentes_ativas),
            'recorrentes_com_data_fim': recorrentes_com_data_fim,
            'transacoes_geradas': total_transacoes_geradas,
            'meses_futuros': meses_futuros
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    # Buscar todos os usuários
    usuarios = Usuario.query.all()
    count_success = 0
    count_failed = 0
    total_adicionadas = 0
    total_ja_existentes = 0
    total_categorias = 0
    
    for usuario in usuarios:
        resultado = criar_categorias_padrao(usuario.id)
        if resultado:
            count_success += 1
            total_adicionadas += resultado['adicionadas']
            total_ja_existentes += resultado['ja_existentes']
            total_categorias += resultado['total']
        else:
            count_failed += 1
    
    if count_failed == 0:
        flash(f'Categorias padrão processadas para {count_success} usuários. '
              f'Total: {total_adicionadas} adicionadas, {total_ja_existentes} já existentes.', 'success')
    else:
        flash(f'Categorias processadas para {count_success} usuários, falha em {count_failed}. '
              f'Total: {total_adicionadas} adicionadas, {total_ja_existentes} já existentes.', 'warning')
    
    return redirect(url_for('admin'))
    
# === ROTAS DE ADMINISTRAÇÃO DE TEMAS ===

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
    total_categorias = Categoria.query.count()
    total_contas = Conta.query.count()
    total_tags = Tag.query.count()
    
    # Estatísticas por usuário
    usuarios_stats = db.session.query(
        Usuario.username,
        Usuario.email,
        Usuario.created_at,
        Usuario.is_admin,
        func.count(Transacao.id).label('total_transacoes')
    ).outerjoin(Transacao).group_by(Usuario.id).all()
    
    return render_template('admin.html', 
                         total_usuarios=total_usuarios,
                         total_transacoes=total_transacoes,
                         total_recorrentes=total_recorrentes,
                         total_categorias=total_categorias,
                         total_contas=total_contas,
                         total_tags=total_tags,
                         usuarios_stats=usuarios_stats)

# === ROTAS DE GERENCIAMENTO DE CONTAS ===

@app.route('/contas')
@login_required
def contas():
    """Lista todas as contas do usuário atual"""
    contas = Conta.query.filter_by(user_id=current_user.id).all()
    return render_template('contas.html', contas=contas)

@app.route('/nova-conta', methods=['GET', 'POST'])
def nova_conta():
    """Adiciona nova conta"""
    form = ContaForm()
    
    if form.validate_on_submit():
        try:
            conta = Conta(
                nome=form.nome.data,
                descricao=form.descricao.data,
                tipo=TipoConta(form.tipo.data),
                saldo_inicial=form.saldo_inicial.data,
                cor=form.cor.data,
                ativa=form.ativa.data,
                user_id=current_user.id  # Associar ao usuário atual
            )
            
            db.session.add(conta)
            db.session.commit()
            flash('Conta criada com sucesso!', 'success')
            return redirect(url_for('contas'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar conta: {str(e)}', 'error')
    
    return render_template('nova_conta.html', form=form)

@app.route('/editar-conta/<int:conta_id>', methods=['GET', 'POST'])
@login_required
def editar_conta(conta_id):
    """Edita uma conta existente"""
    conta = Conta.query.filter_by(id=conta_id, user_id=current_user.id).first_or_404()
    form = ContaForm(obj=conta)
    
    # Configurar valores iniciais
    if request.method == 'GET':
        form.tipo.data = conta.tipo.value
    
    if form.validate_on_submit():
        try:
            conta.nome = form.nome.data
            conta.descricao = form.descricao.data
            conta.tipo = TipoConta(form.tipo.data)
            conta.saldo_inicial = form.saldo_inicial.data
            conta.cor = form.cor.data
            conta.ativa = form.ativa.data
            
            db.session.commit()
            flash('Conta atualizada com sucesso!', 'success')
            return redirect(url_for('contas'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar conta: {str(e)}', 'error')
    
    return render_template('editar_conta.html', form=form, conta=conta)

@app.route('/api/conta/<int:conta_id>', methods=['DELETE'])
@login_required
def deletar_conta_api(conta_id):
    """API para deletar conta"""
    try:
        conta = Conta.query.filter_by(id=conta_id, user_id=current_user.id).first_or_404()
        
        # Verificar se há transações associadas
        transacoes_count = Transacao.query.filter_by(conta_id=conta_id, user_id=current_user.id).count()
        if transacoes_count > 0:
            return jsonify({
                'success': False,
                'message': f'Não é possível excluir a conta "{conta.nome}" pois ela possui {transacoes_count} transações associadas.'
            }), 400
        
        nome_conta = conta.nome
        db.session.delete(conta)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Conta "{nome_conta}" removida com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao remover conta: {str(e)}'
        }), 500

@app.route('/api/conta/<int:conta_id>/saldo')
@login_required
def saldo_conta_api(conta_id):
    """API para obter o saldo atual da conta"""
    conta = Conta.query.filter_by(id=conta_id, user_id=current_user.id).first_or_404()
    return jsonify({
        'conta_id': conta.id,
        'nome': conta.nome,
        'saldo_inicial': conta.saldo_inicial,
        'saldo_atual': conta.saldo_atual,
        'total_receitas': conta.total_receitas,
        'total_despesas': conta.total_despesas
    })

@app.route('/api/categoria/nova', methods=['POST'])
@login_required
def nova_categoria_api():
    """API para criar nova categoria via AJAX"""
    try:
        data = request.get_json()
        
        if not data or not data.get('nome'):
            return jsonify({'success': False, 'message': 'Nome da categoria é obrigatório'}), 400
        
        nome_categoria = data.get('nome').strip()
        descricao = data.get('descricao', '').strip()
        parent_id = data.get('parent_id') if data.get('parent_id') else None
        
        # Verificar se já existe uma categoria com esse nome para o usuário
        categoria_existente = Categoria.query.filter_by(
            nome=nome_categoria, 
            user_id=current_user.id
        ).first()
        
        if categoria_existente:
            return jsonify({
                'success': False, 
                'message': f'Já existe uma categoria com o nome "{nome_categoria}"'
            }), 400
        
        # Criar nova categoria
        nova_categoria = Categoria(
            nome=nome_categoria,
            descricao=descricao,
            user_id=current_user.id,
            parent_id=parent_id
        )
        
        db.session.add(nova_categoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Categoria criada com sucesso!',
            'categoria': {
                'id': nova_categoria.id,
                'nome': nova_categoria.nome,
                'nome_completo': nova_categoria.nome_completo,
                'descricao': nova_categoria.descricao
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'Erro ao criar categoria: {str(e)}'
        }), 500

@app.route('/api/conta/nova', methods=['POST'])
@login_required
def nova_conta_api():
    """API para criar nova conta via AJAX"""
    try:
        data = request.get_json()
        
        if not data or not data.get('nome'):
            return jsonify({'success': False, 'message': 'Nome da conta é obrigatório'}), 400
        
        nome_conta = data.get('nome').strip()
        descricao = data.get('descricao', '').strip()
        tipo_conta = data.get('tipo', 'corrente')
        saldo_inicial = float(data.get('saldo_inicial', 0))
        
        # Verificar se já existe uma conta com esse nome para o usuário
        conta_existente = Conta.query.filter_by(
            nome=nome_conta, 
            user_id=current_user.id
        ).first()
        
        if conta_existente:
            return jsonify({
                'success': False, 
                'message': f'Já existe uma conta com o nome "{nome_conta}"'
            }), 400
        
        # Criar nova conta
        nova_conta = Conta(
            nome=nome_conta,
            descricao=descricao,
            tipo=TipoConta(tipo_conta),
            saldo_inicial=saldo_inicial,
            user_id=current_user.id
        )
        
        db.session.add(nova_conta)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Conta criada com sucesso!',
            'conta': {
                'id': nova_conta.id,
                'nome': nova_conta.nome,
                'descricao': nova_conta.descricao,
                'tipo': nova_conta.tipo.value,
                'saldo_inicial': nova_conta.saldo_inicial
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'Erro ao criar conta: {str(e)}'
        }), 500

@app.route('/api/tag/nova', methods=['POST'])
@login_required
def nova_tag_api():
    """API para criar nova tag via AJAX"""
    try:
        data = request.get_json()
        
        if not data or not data.get('nome'):
            return jsonify({'success': False, 'message': 'Nome da tag é obrigatório'}), 400
        
        nome_tag = data.get('nome').strip()
        descricao = data.get('descricao', '').strip()
        cor = data.get('cor', '#6c757d')
        
        # Verificar se já existe uma tag com esse nome para o usuário
        tag_existente = Tag.query.filter_by(
            nome=nome_tag, 
            user_id=current_user.id
        ).first()
        
        if tag_existente:
            return jsonify({
                'success': False, 
                'message': f'Já existe uma tag com o nome "{nome_tag}"'
            }), 400
        
        # Criar nova tag
        nova_tag = Tag(
            nome=nome_tag,
            descricao=descricao,
            cor=cor,
            user_id=current_user.id
        )
        
        db.session.add(nova_tag)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tag criada com sucesso!',
            'tag': {
                'id': nova_tag.id,
                'nome': nova_tag.nome,
                'descricao': nova_tag.descricao,
                'cor': nova_tag.cor
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'Erro ao criar tag: {str(e)}'
        }), 500


@app.route('/api/forma/nova', methods=['POST'])
@login_required
def nova_forma_api():
    """Cria nova forma de pagamento para o usuário atual (inline via AJAX)"""
    try:
        data = request.get_json() or {}
        nome = (data.get('nome') or '').strip()

        if not nome:
            return jsonify({'success': False, 'message': 'Nome é obrigatório'}), 400

        # Gerar slug amigável e garantir unicidade para o usuário
        import re as _re
        base = _re.sub(r'[^a-z0-9]+', '_', nome.lower()).strip('_')
        candidate = f"{base}-u{current_user.id}"
        i = 0
        while FormaPagamento.query.filter_by(user_id=current_user.id, slug=candidate).first():
            i += 1
            candidate = f"{base}-u{current_user.id}_{i}"

        forma = FormaPagamento(nome=nome, slug=candidate, user_id=current_user.id)
        db.session.add(forma)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Forma criada com sucesso', 'forma': {'id': forma.id, 'nome': forma.nome}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Usar configurações adequadas para desenvolvimento vs produção
    import argparse
    parser = argparse.ArgumentParser(description='Controle Financeiro')
    parser.add_argument('--port', type=int, default=5005, help='Porta para executar o servidor')
    args = parser.parse_args()
    
    port = args.port
    debug = True  # Forçar modo debug
    
    app.logger.info('Starting app on port %s with debug=%s', port, debug)
    app.run(host='0.0.0.0', port=port, debug=debug)
