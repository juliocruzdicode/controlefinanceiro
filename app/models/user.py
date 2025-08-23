"""
Modelo de usuário com autenticação
"""
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import pyotp
import json
from app import db

class Usuario(UserMixin, db.Model):
    """Modelo de usuário com suporte a MFA"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)  # Nome de exibição
    email = db.Column(db.String(120), unique=True, nullable=False)  # Login por email
    password_hash = db.Column(db.String(512), nullable=False)
    
    # Campos para autenticação com Google
    google_id = db.Column(db.String(100), unique=True, nullable=True)  # ID único do Google
    foto_url = db.Column(db.String(255), nullable=True)  # URL da foto do perfil
    
    # Campos adicionais de perfil
    telefone = db.Column(db.String(20), nullable=True)  # Telefone sem formatação
    data_nascimento = db.Column(db.Date, nullable=True)  # Data de nascimento
    sexo = db.Column(db.String(1), nullable=True)  # M, F ou O (outro)
    cidade = db.Column(db.String(100), nullable=True)  # Cidade onde mora
    
    # MFA fields
    mfa_secret = db.Column(db.String(32))  # Base32 secret para TOTP
    mfa_enabled = db.Column(db.Boolean, default=False)
    backup_codes = db.Column(db.Text)  # Códigos de backup separados por vírgula
    
    # Verificação de email
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100), unique=True)
    email_verification_sent_at = db.Column(db.DateTime)
    
    # Redefinição de senha
    password_reset_token = db.Column(db.Text)
    
    # Preferências de tema
    tema_id = db.Column(db.Integer, db.ForeignKey('tema.id'))
    tema = db.relationship('Tema', backref='usuarios', lazy=True)
    dark_mode = db.Column(db.Boolean, default=False)
    
    # Metadados
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    
    # Relacionamentos com as entidades do usuário
    transacoes = db.relationship('Transacao', backref='usuario', lazy=True, cascade='all, delete-orphan')
    categorias = db.relationship('Categoria', backref='usuario', lazy=True, cascade='all, delete-orphan')
    contas = db.relationship('Conta', backref='usuario', lazy=True, cascade='all, delete-orphan')
    tags = db.relationship('Tag', backref='usuario', lazy=True, cascade='all, delete-orphan')
    transacoes_recorrentes = db.relationship('TransacaoRecorrente', backref='usuario', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Define a senha do usuário com hash seguro"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica se a senha está correta"""
        return check_password_hash(self.password_hash, password)
    
    def generate_mfa_secret(self):
        """Gera um novo secret para MFA"""
        self.mfa_secret = pyotp.random_base32()
        return self.mfa_secret
    
    def get_mfa_uri(self):
        """Retorna URI para configuração no Google Authenticator"""
        if not self.mfa_secret:
            self.generate_mfa_secret()
        
        return pyotp.totp.TOTP(self.mfa_secret).provisioning_uri(
            name=self.email,  # Usar email como identificador
            issuer_name="Controle Financeiro"
        )
    
    def verify_mfa_token(self, token):
        """Verifica se o token MFA está correto"""
        if not self.mfa_secret:
            return False
        
        totp = pyotp.TOTP(self.mfa_secret)
        return totp.verify(token, valid_window=1)  # Aceita tokens de ±30 segundos
    
    def verify_backup_code(self, code):
        """Verifica e consome um código de backup"""
        if not self.backup_codes:
            return False
        
        codes = self.backup_codes.split(',')
        if code in codes:
            # Remove o código usado
            codes.remove(code)
            self.backup_codes = ','.join(codes)
            db.session.commit()
            return True
        
        return False
    
    def generate_backup_codes(self):
        """Gera novos códigos de backup"""
        import secrets
        import string
        
        codes = []
        for _ in range(10):  # 10 códigos de backup
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            codes.append(code)
        
        self.backup_codes = ','.join(codes)
        return codes
    
    def generate_email_verification_token(self):
        """Gera token para verificação de email"""
        import secrets
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_sent_at = datetime.utcnow()
        return self.email_verification_token
    
    def verify_email_token(self, token):
        """Verifica se o token de email é válido"""
        if not self.email_verification_token or self.email_verification_token != token:
            return False
        
        # Token expira em 24 horas
        if self.email_verification_sent_at:
            expires_at = self.email_verification_sent_at + timedelta(hours=24)
            if datetime.utcnow() > expires_at:
                return False
        
        return True
    
    def confirm_email(self):
        """Confirma o email do usuário"""
        self.email_verified = True
        self.email_verification_token = None
        self.email_verification_sent_at = None
        db.session.commit()
    
    def can_access_system(self):
        """Verifica se o usuário pode acessar o sistema"""
        return self.is_active and self.email_verified and not self.is_account_locked()
    
    def is_account_locked(self):
        """Verifica se a conta está bloqueada"""
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        return False
    
    def lock_account(self, minutes=15):
        """Bloqueia a conta por um período"""
        self.locked_until = datetime.utcnow() + timedelta(minutes=minutes)
        db.session.commit()
    
    def unlock_account(self):
        """Desbloqueia a conta"""
        self.locked_until = None
        self.failed_login_attempts = 0
        db.session.commit()
    
    def record_failed_login(self):
        """Registra tentativa de login falhada"""
        self.failed_login_attempts += 1
        
        # Bloquear após 5 tentativas
        if self.failed_login_attempts >= 5:
            self.lock_account(15)  # 15 minutos
        
        db.session.commit()
    
    def generate_password_reset_token(self):
        """Gera token para redefinição de senha"""
        import secrets
        token = secrets.token_urlsafe(32)
        
        # Salvar o token com prazo de validade na sessão
        token_data = {
            'token': token,
            'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        # Use JSON para armazenar dados estruturados no token
        self.password_reset_token = json.dumps(token_data)
        db.session.commit()
        
        return token
    
    def verify_password_reset_token(self, token):
        """Verifica se o token de redefinição de senha é válido"""
        if not self.password_reset_token:
            return False
        
        try:
            token_data = json.loads(self.password_reset_token)
            stored_token = token_data.get('token')
            expires_at = datetime.fromisoformat(token_data.get('expires_at'))
            
            # Verificar validade do token
            if stored_token != token:
                return False
            
            # Verificar se o token expirou
            if datetime.utcnow() > expires_at:
                return False
            
            return True
        except:
            return False
    
    def clear_password_reset_token(self):
        """Limpa o token de redefinição de senha"""
        self.password_reset_token = None
        db.session.commit()
        
    def record_successful_login(self):
        """Registra login bem-sucedido"""
        self.last_login = datetime.utcnow()
        self.failed_login_attempts = 0
        self.locked_until = None
        db.session.commit()
    
    def __repr__(self):
        return f'<Usuario {self.username}>'
