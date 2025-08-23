import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    
    # Configuração do banco de dados
    DATABASE_TYPE = os.environ.get('DATABASE_TYPE', 'sqlite')
    
    if DATABASE_TYPE.lower() == 'postgresql':
        # PostgreSQL configuration
        POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
        POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'postgres')
        POSTGRES_DB = os.environ.get('POSTGRES_DB', 'controle_financeiro')
        POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
        POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')
        
        SQLALCHEMY_DATABASE_URI = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'
    else:
        # SQLite configuration (fallback)
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
            'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'controle_financeiro.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuração de email
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']     
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Outras configurações
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', '10'))
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ['true', 'on', '1']
    
    # Configurações de produção
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ['true', 'on', '1']
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    TRANSACOES_PER_PAGE_DEFAULT = 20
    TRANSACOES_PER_PAGE_MAX = 100
    
    # Configurações do Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', None)
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', None)
    GOOGLE_DISCOVERY_URL = 'https://accounts.google.com/.well-known/openid-configuration'
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://127.0.0.1:5000/callback')
