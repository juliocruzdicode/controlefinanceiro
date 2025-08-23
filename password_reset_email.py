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
        print(f"❌ Erro ao enviar email de redefinição: {e}")
        # Em caso de erro, mostrar link no console como fallback
        try:
            token = user.generate_password_reset_token()
            db.session.commit()
            reset_url = url_for('reset_password', token=token, _external=True)
            print(f"\n📧 FALLBACK - Link de redefinição para {user.email}:")
            print(f"{reset_url}\n")
            return True
        except Exception as fallback_error:
            print(f"❌ Erro no fallback: {fallback_error}")
            return False
