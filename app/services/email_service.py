"""
Serviço para envio de emails
"""
from flask import current_app, url_for, render_template
from threading import Thread
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

class EmailService:
    """
    Serviço para envio de emails, seguindo o princípio de responsabilidade única (S de SOLID)
    """
    
    @staticmethod
    def enviar_email_async(app, mensagem):
        """Função para enviar email de forma assíncrona"""
        with app.app_context():
            try:
                servidor = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
                if app.config['MAIL_USE_TLS']:
                    servidor.starttls()
                
                if app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
                    servidor.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
                
                servidor.send_message(mensagem)
                servidor.quit()
            except Exception as e:
                app.logger.error(f"Erro ao enviar email: {str(e)}")
    
    @staticmethod
    def enviar_email(destinatario, assunto, corpo_html, corpo_texto=None):
        """
        Envia um email
        
        Parâmetros:
        - destinatario: Email do destinatário
        - assunto: Assunto do email
        - corpo_html: Corpo do email em formato HTML
        - corpo_texto: Corpo do email em formato texto (opcional)
        """
        app = current_app._get_current_object()
        
        mensagem = MIMEMultipart('alternative')
        mensagem['Subject'] = assunto
        mensagem['From'] = app.config['MAIL_DEFAULT_SENDER']
        mensagem['To'] = destinatario
        
        # Adiciona a versão em texto plano se fornecida
        if corpo_texto:
            parte_texto = MIMEText(corpo_texto, 'plain')
            mensagem.attach(parte_texto)
        
        # Adiciona a versão HTML
        parte_html = MIMEText(corpo_html, 'html')
        mensagem.attach(parte_html)
        
        # Envia o email de forma assíncrona
        Thread(
            target=EmailService.enviar_email_async,
            args=(app, mensagem)
        ).start()
    
    @staticmethod
    def enviar_email_verificacao(email, nome, token):
        """
        Envia email de verificação de conta
        
        Parâmetros:
        - email: Email do destinatário
        - nome: Nome do usuário
        - token: Token de verificação
        """
        link_verificacao = url_for('auth.verify_email', token=token, _external=True)
        
        # Versão HTML
        html = render_template(
            'email/verify_email.html',
            nome=nome,
            link_verificacao=link_verificacao
        )
        
        # Versão texto
        texto = f"""
        Olá {nome},

        Obrigado por se registrar em nosso sistema de controle financeiro!
        
        Para verificar seu endereço de email, por favor clique no link abaixo:
        {link_verificacao}
        
        Este link é válido por 7 dias.
        
        Se você não solicitou esta verificação, por favor ignore este email.
        
        Atenciosamente,
        Equipe de Controle Financeiro
        """
        
        EmailService.enviar_email(
            destinatario=email,
            assunto="Verificação de Email - Controle Financeiro",
            corpo_html=html,
            corpo_texto=texto
        )
    
    @staticmethod
    def enviar_email_redefinicao_senha(email, nome, token):
        """
        Envia email de redefinição de senha
        
        Parâmetros:
        - email: Email do destinatário
        - nome: Nome do usuário
        - token: Token de redefinição
        """
        link_redefinicao = url_for('auth.reset_password', token=token, _external=True)
        
        # Versão HTML
        html = render_template(
            'email/reset_password.html',
            nome=nome,
            link_redefinicao=link_redefinicao
        )
        
        # Versão texto
        texto = f"""
        Olá {nome},

        Você solicitou a redefinição da sua senha no nosso sistema de controle financeiro.
        
        Para redefinir sua senha, por favor clique no link abaixo:
        {link_redefinicao}
        
        Este link é válido por 24 horas.
        
        Se você não solicitou esta redefinição, por favor ignore este email.
        
        Atenciosamente,
        Equipe de Controle Financeiro
        """
        
        EmailService.enviar_email(
            destinatario=email,
            assunto="Redefinição de Senha - Controle Financeiro",
            corpo_html=html,
            corpo_texto=texto
        )
    
    @staticmethod
    def enviar_alerta_orcamento(email, nome, categoria, valor_atual, limite):
        """
        Envia alerta de orçamento excedido
        
        Parâmetros:
        - email: Email do destinatário
        - nome: Nome do usuário
        - categoria: Nome da categoria
        - valor_atual: Valor atual gasto
        - limite: Limite do orçamento
        """
        # Versão HTML
        html = render_template(
            'email/budget_alert.html',
            nome=nome,
            categoria=categoria,
            valor_atual=valor_atual,
            limite=limite
        )
        
        # Versão texto
        texto = f"""
        Olá {nome},

        Este é um alerta referente ao seu orçamento no sistema de controle financeiro.
        
        O limite de gastos da categoria "{categoria}" foi atingido:
        - Limite: R$ {limite:.2f}
        - Valor atual: R$ {valor_atual:.2f}
        
        Acesse o sistema para mais detalhes.
        
        Atenciosamente,
        Equipe de Controle Financeiro
        """
        
        EmailService.enviar_email(
            destinatario=email,
            assunto=f"Alerta de Orçamento - {categoria} - Controle Financeiro",
            corpo_html=html,
            corpo_texto=texto
        )
