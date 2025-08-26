from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
import os
import logging
from logging.handlers import RotatingFileHandler

# Instâncias globais
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def create_app(config_class='config.Config'):
    """
    Factory pattern para criar a aplicação Flask
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Inicializar extensões
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Configurar login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # Configurar logs
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/controle_financeiro.log', 
                                      maxBytes=10240, 
                                      backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Aplicação iniciada')
    
    # Registrar blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.transactions import transactions_bp
    from app.routes.categories import categories_bp
    from app.routes.accounts import accounts_bp
    from app.routes.admin import admin_bp
    from app.routes.admin_payment import admin_payment_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_payment_bp)
    
    # Carregar o modelo de usuário
    from app.models.user import Usuario
    
    @login_manager.user_loader
    def load_user(id):
        return Usuario.query.get(int(id))
    
    # Criação de diretórios de uploads se não existirem
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    return app
