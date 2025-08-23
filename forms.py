from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, DateField, TextAreaField, IntegerField, BooleanField, PasswordField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional, Email, EqualTo, Length, ValidationError
import re
from datetime import datetime

class TransacaoForm(FlaskForm):
    descricao = StringField('Descrição', validators=[DataRequired()])
    valor = FloatField('Valor', validators=[DataRequired(), NumberRange(min=0.01)])
    tipo = SelectField('Tipo', choices=[
        ('receita', 'Receita'),
        ('despesa', 'Despesa')
    ], validators=[DataRequired()])
    categoria_id = SelectField('Categoria', coerce=int, validators=[DataRequired()])
    conta_id = SelectField('Conta', coerce=int, validators=[DataRequired()])
    data_transacao = DateField('Data', default=datetime.today, validators=[DataRequired()])
    
    # Campo de tags
    tags = StringField('Tags', validators=[Optional()], 
                      render_kw={
                          'placeholder': 'Digite as tags separadas por vírgulas (ex: pessoal, trabalho, viagem)', 
                          'class': 'form-control'
                      })
    
    # Campos de recorrência
    is_recorrente = BooleanField('Transação Recorrente')
    tipo_recorrencia = SelectField('Frequência', choices=[
        ('semanal', 'Semanal'),
        ('quinzenal', 'Quinzenal'),
        ('mensal', 'Mensal'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('anual', 'Anual')
    ], validators=[Optional()])
    
    data_fim = DateField('Data de Fim (opcional)', validators=[Optional()])
    
    # Controle de parcelas
    is_parcelada = BooleanField('Transação Parcelada')
    total_parcelas = IntegerField('Número de Parcelas', validators=[Optional(), NumberRange(min=1)])
    
    def __init__(self, *args, **kwargs):
        super(TransacaoForm, self).__init__(*args, **kwargs)
        # Carregar categorias hierárquicas
        self.categoria_id.choices = []
        
        # Importar aqui para evitar import circular
        from models import Categoria, Conta
        
        def add_categoria_choices(categoria, prefix=""):
            """Adiciona categoria e suas subcategorias com indentação visual"""
            display_name = f"{prefix}{categoria.nome}"
            # Só adicionar se não for uma categoria pai (ou se quiser permitir transações em categorias pai)
            self.categoria_id.choices.append((categoria.id, display_name))
            
            for subcategoria in categoria.subcategorias:
                add_categoria_choices(subcategoria, f"{prefix}└─ ")
        
        # Adicionar todas as categorias
        categorias_raiz = Categoria.get_categorias_raiz()
        for categoria in categorias_raiz:
            add_categoria_choices(categoria)
            
        # Carregar contas ativas
        contas_ativas = Conta.get_contas_ativas()
        self.conta_id.choices = [(conta.id, conta.nome) for conta in contas_ativas]
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Validação para transações recorrentes
        if self.is_recorrente.data:
            if not self.tipo_recorrencia.data:
                self.tipo_recorrencia.errors.append('Frequência é obrigatória para transações recorrentes.')
                return False
        
        # Validação para transações parceladas
        if self.is_parcelada.data:
            if not self.total_parcelas.data:
                self.total_parcelas.errors.append('Número de parcelas é obrigatório para transações parceladas.')
                return False
            
            if not self.is_recorrente.data:
                self.is_recorrente.errors.append('Transações parceladas devem ser recorrentes.')
                return False
        
        # Validação de datas
        if self.data_fim.data and self.data_fim.data <= self.data_transacao.data:
            self.data_fim.errors.append('Data de fim deve ser posterior à data da transação.')
            return False
        
        return True

class CategoriaForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    descricao = TextAreaField('Descrição')
    cor = StringField('Cor', default='#007bff')
    parent_id = SelectField('Categoria Pai', coerce=int, validators=[])
    
    def __init__(self, *args, **kwargs):
        super(CategoriaForm, self).__init__(*args, **kwargs)
        # Carregar categorias para o campo parent_id
        self.parent_id.choices = [(0, 'Nenhuma (Categoria Raiz)')]
        
        # Importar aqui para evitar import circular
        from models import Categoria
        
        def add_categoria_choices(categoria, prefix=""):
            """Adiciona categoria e suas subcategorias recursivamente"""
            display_name = f"{prefix}{categoria.nome}"
            self.parent_id.choices.append((categoria.id, display_name))
            
            for subcategoria in categoria.subcategorias:
                add_categoria_choices(subcategoria, f"{prefix}└─ ")
        
        # Adicionar todas as categorias raiz e suas subcategorias
        categorias_raiz = Categoria.get_categorias_raiz()
        for categoria in categorias_raiz:
            add_categoria_choices(categoria)

class TransacaoRecorrenteForm(FlaskForm):
    descricao = StringField('Descrição', validators=[DataRequired()])
    valor = FloatField('Valor', validators=[DataRequired(), NumberRange(min=0.01)])
    tipo = SelectField('Tipo', choices=[
        ('receita', 'Receita'),
        ('despesa', 'Despesa')
    ], validators=[DataRequired()])
    categoria_id = SelectField('Categoria', coerce=int, validators=[DataRequired()])
    conta_id = SelectField('Conta', coerce=int, validators=[DataRequired()])
    
    # Campos de recorrência
    tipo_recorrencia = SelectField('Frequência', choices=[
        ('unica', 'Única (não recorrente)'),
        ('semanal', 'Semanal'),
        ('quinzenal', 'Quinzenal'),
        ('mensal', 'Mensal'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('anual', 'Anual')
    ], validators=[DataRequired()])
    
    data_inicio = DateField('Data de Início', default=datetime.today, validators=[DataRequired()])
    data_fim = DateField('Data de Fim', validators=[Optional()])
    
    # Controle de parcelas
    is_parcelada = BooleanField('Transação Parcelada')
    total_parcelas = IntegerField('Total de Parcelas', validators=[Optional(), NumberRange(min=1)])
    
    def __init__(self, *args, **kwargs):
        super(TransacaoRecorrenteForm, self).__init__(*args, **kwargs)
        # Carregar categorias hierárquicas
        self.categoria_id.choices = []
        
        # Importar aqui para evitar import circular
        from models import Categoria, Conta
        
        def add_categoria_choices(categoria, prefix=""):
            """Adiciona categoria e suas subcategorias com indentação visual"""
            display_name = f"{prefix}{categoria.nome}"
            self.categoria_id.choices.append((categoria.id, display_name))
            
            for subcategoria in categoria.subcategorias:
                add_categoria_choices(subcategoria, f"{prefix}└─ ")
        
        # Adicionar todas as categorias
        categorias_raiz = Categoria.get_categorias_raiz()
        for categoria in categorias_raiz:
            add_categoria_choices(categoria)
            
        # Carregar contas ativas
        contas_ativas = Conta.get_contas_ativas()
        self.conta_id.choices = [(conta.id, conta.nome) for conta in contas_ativas]
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        
        # Validação customizada: se é parcelada, deve ter total_parcelas
        if self.is_parcelada.data and not self.total_parcelas.data:
            self.total_parcelas.errors.append('Número de parcelas é obrigatório para transações parceladas.')
            return False
        
        # Se não é parcelada, não deve ter total_parcelas
        if not self.is_parcelada.data and self.total_parcelas.data:
            self.total_parcelas.data = None
        
        # Validação de datas
        if self.data_fim.data and self.data_fim.data <= self.data_inicio.data:
            self.data_fim.errors.append('Data de fim deve ser posterior à data de início.')
            return False
        
        return True

class TagForm(FlaskForm):
    """Formulário para criar/editar tags"""
    nome = StringField('Nome da Tag', validators=[DataRequired()], 
                      render_kw={'placeholder': 'Ex: pessoal, trabalho, viagem'})
    descricao = TextAreaField('Descrição', validators=[Optional()],
                             render_kw={'placeholder': 'Descrição opcional da tag'})
    cor = StringField('Cor', validators=[Optional()], 
                     render_kw={'type': 'color', 'value': '#6c757d'})
    ativa = BooleanField('Tag Ativa', default=True)

class ContaForm(FlaskForm):
    nome = StringField('Nome da Conta', validators=[DataRequired()])
    descricao = TextAreaField('Descrição')
    tipo = SelectField('Tipo da Conta', choices=[
        ('corrente', 'Conta Corrente'),
        ('poupanca', 'Conta Poupança'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('cartao_debito', 'Cartão de Débito'),
        ('dinheiro', 'Dinheiro'),
        ('investimento', 'Investimento'),
        ('outros', 'Outros')
    ], validators=[DataRequired()])
    saldo_inicial = FloatField('Saldo Inicial', default=0.0)
    cor = StringField('Cor', default='#007bff')
    ativa = BooleanField('Conta Ativa', default=True)

# === FORMULÁRIOS DE AUTENTICAÇÃO E MFA ===

class CompletarCadastroForm(FlaskForm):
    """Formulário para completar cadastro (após login com Google)"""
    username = StringField('Nome completo', validators=[DataRequired('Nome é obrigatório'), 
                                                       Length(min=3, max=80, message='Nome deve ter entre 3 e 80 caracteres')])
    telefone = StringField('Telefone', validators=[Optional(), 
                                                  Length(min=10, max=20, message='Telefone inválido')])
    data_nascimento = DateField('Data de nascimento', format='%Y-%m-%d', validators=[Optional()])
    sexo = SelectField('Sexo', choices=[('', 'Selecione...'), ('M', 'Masculino'), ('F', 'Feminino'), ('O', 'Outro')],
                      validators=[Optional()])
    cidade = StringField('Cidade', validators=[Optional(), 
                                             Length(max=100, message='Cidade deve ter no máximo 100 caracteres')])
    submit = SubmitField('Completar cadastro')

class LoginForm(FlaskForm):
    """Formulário de login com email"""
    email = StringField('Email', validators=[DataRequired(), Email()], 
                       render_kw={'placeholder': 'Digite seu email'})
    password = PasswordField('Senha', validators=[DataRequired()],
                           render_kw={'placeholder': 'Digite sua senha'})
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')

class MFAForm(FlaskForm):
    """Formulário para verificação MFA"""
    mfa_code = StringField('Código de Verificação', validators=[DataRequired()],
                          render_kw={'placeholder': '000000', 'maxlength': '6', 'class': 'text-center'})
    submit = SubmitField('Verificar')

class BackupCodeForm(FlaskForm):
    """Formulário para código de backup"""
    backup_code = StringField('Código de Backup', validators=[DataRequired()],
                             render_kw={'placeholder': 'Digite o código de backup'})
    submit = SubmitField('Usar Código')

class SetupMFAForm(FlaskForm):
    """Formulário para configurar MFA"""
    mfa_code = StringField('Código de Verificação', validators=[DataRequired()],
                          render_kw={'placeholder': '000000', 'maxlength': '6', 'class': 'text-center'})
    submit = SubmitField('Ativar MFA')

class RegisterForm(FlaskForm):
    """Formulário de registro"""
    username = StringField('Nome Completo', validators=[
        DataRequired()
    ], render_kw={'placeholder': 'Digite seu nome completo'})
    
    email = StringField('Email', validators=[DataRequired(), Email()],
                       render_kw={'placeholder': 'seu@email.com'})
    
    # Novos campos de perfil
    telefone = StringField('Telefone', validators=[Optional()],
                         render_kw={'placeholder': '(XX) XXXXX-XXXX', 'data-mask': '(00) 00000-0000'})
    
    data_nascimento = DateField('Data de Nascimento', validators=[Optional()],
                              format='%Y-%m-%d',
                              render_kw={'type': 'date', 'placeholder': 'DD/MM/AAAA'})
    
    sexo = SelectField('Sexo', choices=[
        ('', 'Selecione...'),
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outro/Prefiro não informar')
    ], validators=[Optional()])
    
    cidade = StringField('Cidade onde mora', validators=[Optional(), Length(max=100)],
                        render_kw={'placeholder': 'Digite sua cidade'})
    
    password = PasswordField('Senha', validators=[
        DataRequired(),
        Length(min=8, message='Senha deve ter pelo menos 8 caracteres')
    ], render_kw={'placeholder': 'Digite uma senha forte'})
    
    password2 = PasswordField('Confirmar Senha', validators=[
        DataRequired(), 
        EqualTo('password', message='Senhas não coincidem')
    ], render_kw={'placeholder': 'Confirme sua senha'})
    
    submit = SubmitField('Registrar')
    
    def validate_telefone(self, telefone):
        """Validação e limpeza do número de telefone"""
        if telefone.data:
            # Remove todos os caracteres não numéricos
            telefone.data = re.sub(r'\D', '', telefone.data)
            
            # Verificar se o número tem o tamanho correto
            if len(telefone.data) not in [10, 11]:
                raise ValidationError('Número de telefone inválido. Deve ter 10 ou 11 dígitos.')
    
    def validate_password(self, password):
        """Validação customizada para senha forte"""
        pwd = password.data
        
        if len(pwd) < 8:
            raise ValidationError('Senha deve ter pelo menos 8 caracteres.')
        
        # Pelo menos uma letra minúscula
        if not re.search(r'[a-z]', pwd):
            raise ValidationError('Senha deve conter pelo menos uma letra minúscula.')
        
        # Pelo menos uma letra maiúscula
        if not re.search(r'[A-Z]', pwd):
            raise ValidationError('Senha deve conter pelo menos uma letra maiúscula.')
        
        # Pelo menos um número
        if not re.search(r'\d', pwd):
            raise ValidationError('Senha deve conter pelo menos um número.')
        
        # Pelo menos um caractere especial
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', pwd):
            raise ValidationError('Senha deve conter pelo menos um caractere especial.')
        
        # Não pode ser uma senha muito comum
        common_passwords = [
            '12345678', 'password', 'qwerty123', 'admin123', 
            '123456789', 'password123', 'admin1234'
        ]
        if pwd.lower() in common_passwords:
            raise ValidationError('Senha muito comum. Escolha uma senha mais segura.')

class ChangePasswordForm(FlaskForm):
    """Formulário para alterar senha"""
    current_password = PasswordField('Senha Atual', validators=[DataRequired()],
                                   render_kw={'placeholder': 'Digite sua senha atual'})
    new_password = PasswordField('Nova Senha', validators=[DataRequired()],
                               render_kw={'placeholder': 'Digite sua nova senha'})
    new_password2 = PasswordField('Confirmar Nova Senha', validators=[DataRequired(), EqualTo('new_password')],
                                render_kw={'placeholder': 'Confirme sua nova senha'})
    submit = SubmitField('Alterar Senha')

class TemaForm(FlaskForm):
    """Formulário para criar/editar temas"""
    nome = StringField('Nome do Tema', validators=[DataRequired(), Length(max=50)])
    descricao = TextAreaField('Descrição', validators=[Optional(), Length(max=200)])
    is_default = BooleanField('Definir como Tema Padrão')
    
    # Cores para modo claro
    cor_primaria = StringField('Cor Primária', 
                              render_kw={'type': 'color'}, 
                              validators=[DataRequired()])
    cor_secundaria = StringField('Cor Secundária', 
                                render_kw={'type': 'color'}, 
                                validators=[DataRequired()])
    cor_sucesso = StringField('Cor de Sucesso', 
                             render_kw={'type': 'color'}, 
                             validators=[DataRequired()])
    cor_perigo = StringField('Cor de Perigo', 
                            render_kw={'type': 'color'}, 
                            validators=[DataRequired()])
    cor_alerta = StringField('Cor de Alerta', 
                           render_kw={'type': 'color'}, 
                           validators=[DataRequired()])
    cor_info = StringField('Cor de Informação', 
                          render_kw={'type': 'color'}, 
                          validators=[DataRequired()])
    cor_fundo = StringField('Cor de Fundo', 
                           render_kw={'type': 'color'}, 
                           validators=[DataRequired()])
    cor_texto = StringField('Cor de Texto', 
                           render_kw={'type': 'color'}, 
                           validators=[DataRequired()])
    
    # Cores para modo escuro
    cor_primaria_dark = StringField('Cor Primária (Dark)', 
                                   render_kw={'type': 'color'}, 
                                   validators=[DataRequired()])
    cor_secundaria_dark = StringField('Cor Secundária (Dark)', 
                                     render_kw={'type': 'color'}, 
                                     validators=[DataRequired()])
    cor_sucesso_dark = StringField('Cor de Sucesso (Dark)', 
                                  render_kw={'type': 'color'}, 
                                  validators=[DataRequired()])
    cor_perigo_dark = StringField('Cor de Perigo (Dark)', 
                                 render_kw={'type': 'color'}, 
                                 validators=[DataRequired()])
    cor_alerta_dark = StringField('Cor de Alerta (Dark)', 
                                render_kw={'type': 'color'}, 
                                validators=[DataRequired()])
    cor_info_dark = StringField('Cor de Informação (Dark)', 
                               render_kw={'type': 'color'}, 
                               validators=[DataRequired()])
    cor_fundo_dark = StringField('Cor de Fundo (Dark)', 
                                render_kw={'type': 'color'}, 
                                validators=[DataRequired()])
    cor_texto_dark = StringField('Cor de Texto (Dark)', 
                                render_kw={'type': 'color'}, 
                                validators=[DataRequired()])
    
    submit = SubmitField('Salvar Tema')

class UserThemeForm(FlaskForm):
    """Formulário para usuário selecionar tema e modo"""
    tema_id = SelectField('Tema', coerce=int)
    dark_mode = BooleanField('Modo Escuro')
    submit = SubmitField('Salvar Preferências')

class ForgotPasswordForm(FlaskForm):
    """Formulário para solicitar redefinição de senha"""
    email = StringField('Email', validators=[DataRequired(), Email()],
                       render_kw={'placeholder': 'Digite seu email cadastrado'})
    submit = SubmitField('Enviar Link de Recuperação')

class ResetPasswordForm(FlaskForm):
    """Formulário para redefinir a senha"""
    password = PasswordField('Nova Senha', validators=[
        DataRequired(),
        Length(min=8, message='Senha deve ter pelo menos 8 caracteres')
    ], render_kw={'placeholder': 'Digite uma senha forte'})
    
    password2 = PasswordField('Confirmar Senha', validators=[
        DataRequired(), 
        EqualTo('password', message='Senhas não coincidem')
    ], render_kw={'placeholder': 'Confirme sua senha'})
    
    submit = SubmitField('Redefinir Senha')
    
    def validate_password(self, password):
        """Validação customizada para senha forte"""
        pwd = password.data
        
        if len(pwd) < 8:
            raise ValidationError('Senha deve ter pelo menos 8 caracteres.')
        
        # Pelo menos uma letra minúscula
        if not re.search(r'[a-z]', pwd):
            raise ValidationError('Senha deve conter pelo menos uma letra minúscula.')
        
        # Pelo menos uma letra maiúscula
        if not re.search(r'[A-Z]', pwd):
            raise ValidationError('Senha deve conter pelo menos uma letra maiúscula.')
        
        # Pelo menos um número
        if not re.search(r'\d', pwd):
            raise ValidationError('Senha deve conter pelo menos um número.')
        
        # Pelo menos um caractere especial
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', pwd):
            raise ValidationError('Senha deve conter pelo menos um caractere especial.')
