"""
Formulários relacionados à autenticação
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models.user import Usuario

class LoginForm(FlaskForm):
    """Formulário para login de usuários"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    lembrar = BooleanField('Lembrar de mim')
    submit = SubmitField('Entrar')

class RegistrationForm(FlaskForm):
    """Formulário para registro de novos usuários"""
    nome = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=64)])
    nome_completo = StringField('Nome Completo', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired(), Length(min=8)])
    confirmar_senha = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('senha')])
    submit = SubmitField('Registrar')
    
    def validate_email(self, email):
        """Valida se o email já está em uso"""
        usuario = Usuario.query.filter_by(email=email.data).first()
        if usuario:
            raise ValidationError('Este email já está em uso. Por favor, use outro.')
    
    def validate_nome(self, nome):
        """Valida se o nome de usuário já está em uso"""
        usuario = Usuario.query.filter_by(nome=nome.data).first()
        if usuario:
            raise ValidationError('Este nome de usuário já está em uso. Por favor, escolha outro.')

class PasswordResetRequestForm(FlaskForm):
    """Formulário para solicitar redefinição de senha"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Solicitar Redefinição de Senha')

class PasswordResetForm(FlaskForm):
    """Formulário para redefinir a senha"""
    senha = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=8)])
    confirmar_senha = PasswordField('Confirmar Nova Senha', validators=[DataRequired(), EqualTo('senha')])
    submit = SubmitField('Redefinir Senha')

class ChangePasswordForm(FlaskForm):
    """Formulário para alterar a senha"""
    senha_atual = PasswordField('Senha Atual', validators=[DataRequired()])
    nova_senha = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=8)])
    confirmar_senha = PasswordField('Confirmar Nova Senha', validators=[DataRequired(), EqualTo('nova_senha')])
    submit = SubmitField('Alterar Senha')
