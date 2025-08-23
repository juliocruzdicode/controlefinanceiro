"""
Serviço para autenticação OAuth com Google
"""
from flask import current_app, url_for, session, redirect, request
from flask_login import login_user
import requests
import json
import os
from oauthlib.oauth2 import WebApplicationClient
from app import db
from app.models.user import Usuario
from app.services.category_service import CategoriaService
from app.services.account_service import ContaService

class GoogleAuthService:
    """
    Serviço para autenticação via Google OAuth, seguindo o princípio de responsabilidade única (S de SOLID)
    """
    
    @staticmethod
    def get_client():
        """
        Retorna o cliente OAuth configurado
        
        Returns:
            WebApplicationClient: Cliente OAuth configurado
        """
        client_id = current_app.config['GOOGLE_CLIENT_ID']
        return WebApplicationClient(client_id)
    
    @staticmethod
    def get_google_provider_cfg():
        """
        Obtém a configuração do provedor Google
        
        Returns:
            dict: Configuração do provedor Google
        """
        discovery_url = current_app.config['GOOGLE_DISCOVERY_URL']
        return requests.get(discovery_url).json()
    
    @staticmethod
    def get_auth_url():
        """
        Gera a URL para autenticação com Google
        
        Returns:
            str: URL para redirecionamento ao Google
        """
        # Obter configuração do Google
        google_provider_cfg = GoogleAuthService.get_google_provider_cfg()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        
        # Iniciar o cliente OAuth
        client = GoogleAuthService.get_client()
        
        # Construir a URL de requisição
        redirect_uri = url_for("auth.callback", _external=True)
        
        return client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=redirect_uri,
            scope=["openid", "email", "profile"],
        )
    
    @staticmethod
    def process_callback(request_url):
        """
        Processa o callback do Google e autentica o usuário
        
        Args:
            request_url: URL completa da requisição de callback
            
        Returns:
            Usuario: Usuário autenticado ou None em caso de falha
        """
        # Obter configuração do Google
        google_provider_cfg = GoogleAuthService.get_google_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        # Iniciar o cliente OAuth
        client = GoogleAuthService.get_client()
        
        # Obter código de autorização
        code = request.args.get("code")
        
        # Preparar token
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request_url,
            redirect_url=url_for("auth.callback", _external=True),
            code=code
        )
        
        # Obter token de acesso
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(
                current_app.config['GOOGLE_CLIENT_ID'], 
                current_app.config['GOOGLE_CLIENT_SECRET']
            ),
        )
        
        # Processar resposta
        client.parse_request_body_response(json.dumps(token_response.json()))
        
        # Obter informações do usuário
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
        
        # Validar email
        if userinfo_response.json().get("email_verified"):
            google_id = userinfo_response.json()["sub"]
            email = userinfo_response.json()["email"]
            nome_completo = userinfo_response.json().get("name", "")
            nome = userinfo_response.json().get("given_name", email.split("@")[0])
            foto = userinfo_response.json().get("picture", None)
        else:
            return None
        
        # Procurar usuário ou criar novo
        usuario = Usuario.query.filter_by(google_id=google_id).first()
        
        # Se não encontrou por Google ID, tenta pelo email
        if not usuario:
            usuario = Usuario.query.filter_by(email=email).first()
            
            # Se encontrou pelo email, atualiza o Google ID
            if usuario:
                usuario.google_id = google_id
                usuario.foto_url = foto
                db.session.commit()
        
        # Se não encontrou, cria um novo usuário
        if not usuario:
            usuario = Usuario(
                nome=nome,
                nome_completo=nome_completo,
                email=email,
                google_id=google_id,
                foto_url=foto,
                email_verificado=True
            )
            
            # Gerar uma senha aleatória para o usuário
            import secrets
            senha_temp = secrets.token_urlsafe(16)
            usuario.set_password(senha_temp)
            
            db.session.add(usuario)
            db.session.commit()
            
            # Criar categorias padrão para o novo usuário
            CategoriaService.criar_categorias_padrao(usuario.id)
            
            # Criar contas padrão para o novo usuário
            ContaService.criar_contas_padrao(usuario.id)
        
        # Autenticar usuário
        login_user(usuario)
        return usuario
