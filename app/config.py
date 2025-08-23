"""
Configurações da aplicação
"""

import os
from datetime import timedelta

class Config:
    """Configurações base da aplicação"""
    # Segurança
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave-secreta-padrao-desenvolvimento'
    
    # Flask-SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/controle_financeiro.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    
    # Configurações de email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@controlefinanceiro.com')
    
    # Configurações do Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_DISCOVERY_URL = 'https://accounts.google.com/.well-known/openid-configuration'
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI')
    # Configurações da aplicação
    APP_NAME = 'Controle Financeiro'
    APP_ADMIN_EMAIL = os.environ.get('APP_ADMIN_EMAIL', 'admin@example.com')
    APP_DEFAULT_THEME = 'Padrão'
    
    # Logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'false').lower() in ['true', 'on', '1']
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Paginação
    ITEMS_PER_PAGE = 20
    
    # Timeout para sessão (em minutos)
    SESSION_TIMEOUT = 60
    
    # Outros
    DEBUG = os.environ.get('DEBUG', 'false').lower() in ['true', 'on', '1']

class DevelopmentConfig(Config):
    """Configurações para ambiente de desenvolvimento"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class TestingConfig(Config):
    """Configurações para ambiente de testes"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Configurações para ambiente de produção"""
    # Sobrescrever configurações sensíveis aqui
    SQLALCHEMY_ECHO = False
    DEBUG = False
    
    # Em produção, SECRET_KEY deve ser definido como variável de ambiente
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Configurações de segurança adicionais
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True

# Dicionário de configurações
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
