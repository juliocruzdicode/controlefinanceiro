"""
Serviço para gerenciamento de usuários
"""
from datetime import datetime, timedelta
import secrets
from flask import url_for
from flask_login import login_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.user import Usuario
from app.services.category_service import CategoriaService
from app.services.account_service import ContaService

class UsuarioService:
    """
    Serviço para gerenciamento de usuários, seguindo o princípio de responsabilidade única (S de SOLID)
    """
    
    @staticmethod
    def criar_usuario(nome, email, senha, nome_completo=None):
        """Cria um novo usuário e adiciona categorias e contas padrão"""
        # Verifica se o email já está em uso
        if Usuario.query.filter_by(email=email).first():
            return None
        
        # Hash da senha
        senha_hash = generate_password_hash(senha)
        
        # Cria o usuário
        usuario = Usuario(
            nome=nome,
            email=email,
            senha_hash=senha_hash,
            nome_completo=nome_completo or nome,
            data_cadastro=datetime.utcnow()
        )
        
        db.session.add(usuario)
        db.session.commit()
        
        # Cria categorias e contas padrão
        CategoriaService.criar_categorias_padrao(usuario.id)
        ContaService.criar_contas_padrao(usuario.id)
        
        return usuario
    
    @staticmethod
    def autenticar_usuario(email, senha):
        """Autentica um usuário e retorna o objeto de usuário se bem-sucedido"""
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and check_password_hash(usuario.senha_hash, senha):
            return usuario
        
        return None
    
    @staticmethod
    def fazer_login(usuario, lembrar=False):
        """Faz login do usuário utilizando flask-login"""
        return login_user(usuario, remember=lembrar)
    
    @staticmethod
    def obter_usuario_por_id(user_id):
        """Retorna um usuário pelo ID"""
        return Usuario.query.get(user_id)
    
    @staticmethod
    def obter_usuario_por_email(email):
        """Retorna um usuário pelo email"""
        return Usuario.query.filter_by(email=email).first()
    
    @staticmethod
    def atualizar_perfil(user_id, **kwargs):
        """Atualiza os dados do perfil do usuário"""
        usuario = UsuarioService.obter_usuario_por_id(user_id)
        if not usuario:
            return None
        
        # Campos que podem ser atualizados
        campos_permitidos = ['nome', 'nome_completo', 'bio', 'avatar', 'tema_id']
        
        for campo, valor in kwargs.items():
            if campo in campos_permitidos:
                setattr(usuario, campo, valor)
        
        db.session.commit()
        return usuario
    
    @staticmethod
    def alterar_senha(user_id, senha_atual, nova_senha):
        """Altera a senha de um usuário"""
        usuario = UsuarioService.obter_usuario_por_id(user_id)
        if not usuario:
            return False
        
        # Verifica a senha atual
        if not check_password_hash(usuario.senha_hash, senha_atual):
            return False
        
        # Atualiza a senha
        usuario.senha_hash = generate_password_hash(nova_senha)
        db.session.commit()
        return True
    
    @staticmethod
    def gerar_token_redefinicao_senha(email):
        """Gera um token de redefinição de senha e o armazena no banco de dados"""
        usuario = UsuarioService.obter_usuario_por_email(email)
        if not usuario:
            return None
        
        # Gera token
        token = secrets.token_urlsafe(32)
        
        # Define o prazo de expiração (24 horas)
        expiracao = datetime.utcnow() + timedelta(hours=24)
        
        # Salva no banco de dados
        usuario.reset_token = token
        usuario.reset_token_expiracao = expiracao
        db.session.commit()
        
        return token
    
    @staticmethod
    def verificar_token_redefinicao(token):
        """Verifica se um token de redefinição de senha é válido e retorna o usuário"""
        usuario = Usuario.query.filter_by(reset_token=token).first()
        
        # Verifica se o token existe e não expirou
        if usuario and usuario.reset_token_expiracao > datetime.utcnow():
            return usuario
        
        return None
    
    @staticmethod
    def redefinir_senha(token, nova_senha):
        """Redefine a senha do usuário usando um token válido"""
        usuario = UsuarioService.verificar_token_redefinicao(token)
        if not usuario:
            return False
        
        # Atualiza a senha
        usuario.senha_hash = generate_password_hash(nova_senha)
        
        # Limpa o token
        usuario.reset_token = None
        usuario.reset_token_expiracao = None
        
        db.session.commit()
        return True
    
    @staticmethod
    def gerar_token_verificacao_email(user_id):
        """Gera um token para verificação de email"""
        usuario = UsuarioService.obter_usuario_por_id(user_id)
        if not usuario:
            return None
        
        # Gera token
        token = secrets.token_urlsafe(16)
        
        # Define o prazo de expiração (7 dias)
        expiracao = datetime.utcnow() + timedelta(days=7)
        
        # Salva no banco de dados
        usuario.verificacao_token = token
        usuario.verificacao_token_expiracao = expiracao
        db.session.commit()
        
        return token
    
    @staticmethod
    def verificar_email(token):
        """Verifica o email do usuário usando um token válido"""
        usuario = Usuario.query.filter_by(verificacao_token=token).first()
        
        # Verifica se o token existe e não expirou
        if usuario and usuario.verificacao_token_expiracao > datetime.utcnow():
            usuario.email_verificado = True
            usuario.verificacao_token = None
            usuario.verificacao_token_expiracao = None
            
            db.session.commit()
            return usuario
        
        return None
    
    @staticmethod
    def listar_todos_usuarios():
        """Lista todos os usuários (apenas para admin)"""
        return Usuario.query.all()
    
    @staticmethod
    def contar_usuarios():
        """Conta o número total de usuários"""
        return Usuario.query.count()
