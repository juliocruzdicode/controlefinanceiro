from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from enum import Enum

db = SQLAlchemy()

class TipoTransacao(Enum):
    RECEITA = "receita"
    DESPESA = "despesa"

class TipoConta(Enum):
    CORRENTE = "corrente"
    POUPANCA = "poupanca"
    CARTAO_CREDITO = "cartao_credito"
    CARTAO_DEBITO = "cartao_debito"
    DINHEIRO = "dinheiro"
    INVESTIMENTO = "investimento"
    OUTROS = "outros"

class TipoRecorrencia(Enum):
    UNICA = "unica"           # Transação única (padrão)
    SEMANAL = "semanal"       # A cada 7 dias
    QUINZENAL = "quinzenal"   # A cada 15 dias
    MENSAL = "mensal"         # Mensalmente
    TRIMESTRAL = "trimestral" # A cada 3 meses
    SEMESTRAL = "semestral"   # A cada 6 meses
    ANUAL = "anual"           # Anualmente

class StatusRecorrencia(Enum):
    ATIVA = "ativa"           # Gerando transações
    PAUSADA = "pausada"       # Temporariamente pausada
    FINALIZADA = "finalizada" # Concluída ou cancelada

# Tabela de associação entre Transações e Tags (muitos-para-muitos)
transacao_tags = db.Table('transacao_tags',
    db.Column('transacao_id', db.Integer, db.ForeignKey('transacao.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Tag(db.Model):
    """Modelo para tags personalizadas das transações"""
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(200))
    cor = db.Column(db.String(7), default='#6c757d')  # Cor em hexadecimal (cinza por padrão)
    ativa = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Chave estrangeira para usuário
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Relacionamento com transações
    transacoes = db.relationship('Transacao', secondary=transacao_tags, back_populates='tags')
    
    def __repr__(self):
        return f'<Tag {self.nome}>'
    
    @property
    def total_transacoes(self):
        """Retorna o número total de transações com esta tag"""
        return len(self.transacoes)
    
    @property
    def total_valor(self):
        """Retorna o valor total das transações com esta tag"""
        return sum(t.valor for t in self.transacoes)
    
    @property
    def total_receitas(self):
        """Retorna o valor total das receitas com esta tag"""
        return sum(t.valor for t in self.transacoes if t.tipo == TipoTransacao.RECEITA)
    
    @property
    def total_despesas(self):
        """Retorna o valor total das despesas com esta tag"""
        return sum(t.valor for t in self.transacoes if t.tipo == TipoTransacao.DESPESA)
    
    @classmethod
    def get_tags_ativas(cls):
        """Retorna apenas as tags ativas"""
        return cls.query.filter_by(ativa=True).order_by(cls.nome).all()
    
    @classmethod
    def get_or_create(cls, nome):
        """Obtém uma tag existente ou cria uma nova"""
        nome = nome.strip().lower()
        tag = cls.query.filter(db.func.lower(cls.nome) == nome).first()
        if not tag:
            tag = cls(nome=nome.title())  # Primeira letra maiúscula
            db.session.add(tag)
            db.session.commit()
        return tag
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'cor': self.cor,
            'ativa': self.ativa,
            'total_transacoes': self.total_transacoes,
            'total_valor': self.total_valor,
            'total_receitas': self.total_receitas,
            'total_despesas': self.total_despesas,
            'data_criacao': self.data_criacao.strftime('%Y-%m-%d')
        }

class Conta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(200))
    tipo = db.Column(db.Enum(TipoConta), nullable=False, default=TipoConta.CORRENTE)
    saldo_inicial = db.Column(db.Float, default=0.0)
    cor = db.Column(db.String(7), default='#007bff')  # Cor em hexadecimal
    ativa = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Chave estrangeira para usuário
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Relacionamentos
    transacoes = db.relationship('Transacao', backref='conta', lazy=True)
    transacoes_recorrentes = db.relationship('TransacaoRecorrente', backref='conta', lazy=True)
    
    def __repr__(self):
        return f'<Conta {self.nome}>'
    
    @property
    def saldo_atual(self):
        """Calcula o saldo atual da conta"""
        total_receitas = sum(t.valor for t in self.transacoes if t.tipo == TipoTransacao.RECEITA)
        total_despesas = sum(t.valor for t in self.transacoes if t.tipo == TipoTransacao.DESPESA)
        return self.saldo_inicial + total_receitas - total_despesas
    
    @property
    def total_receitas(self):
        """Total de receitas da conta"""
        return sum(t.valor for t in self.transacoes if t.tipo == TipoTransacao.RECEITA)
    
    @property
    def total_despesas(self):
        """Total de despesas da conta"""
        return sum(t.valor for t in self.transacoes if t.tipo == TipoTransacao.DESPESA)
    
    @classmethod
    def get_contas_ativas(cls):
        """Retorna apenas as contas ativas"""
        return cls.query.filter_by(ativa=True).all()
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'tipo': self.tipo.value,
            'saldo_inicial': self.saldo_inicial,
            'saldo_atual': self.saldo_atual,
            'total_receitas': self.total_receitas,
            'total_despesas': self.total_despesas,
            'cor': self.cor,
            'ativa': self.ativa,
            'transacoes_count': len(self.transacoes)
        }

class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    descricao = db.Column(db.String(200))
    cor = db.Column(db.String(7), default='#007bff')  # Cor em hexadecimal
    
    # Relacionamento hierárquico - self-referencing
    parent_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=True)
    parent = db.relationship('Categoria', remote_side=[id], backref='subcategorias')
    
    # Chave estrangeira para usuário
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Relacionamento com transações
    transacoes = db.relationship('Transacao', backref='categoria', lazy=True)
    
    def __repr__(self):
        return f'<Categoria {self.nome}>'
    
    @property
    def nome_completo(self):
        """Retorna o nome completo da categoria com hierarquia"""
        if self.parent:
            return f"{self.parent.nome_completo} > {self.nome}"
        return self.nome
    
    @property
    def nivel(self):
        """Retorna o nível hierárquico da categoria (0 = raiz)"""
        if self.parent:
            return self.parent.nivel + 1
        return 0
    
    @property
    def is_parent(self):
        """Verifica se a categoria tem subcategorias"""
        return len(self.subcategorias) > 0
    
    def get_all_subcategorias(self, include_self=True):
        """Retorna todas as subcategorias recursivamente"""
        result = []
        if include_self:
            result.append(self)
        
        for subcategoria in self.subcategorias:
            result.extend(subcategoria.get_all_subcategorias(include_self=True))
        
        return result
    
    @classmethod
    def get_categorias_raiz(cls):
        """Retorna apenas as categorias raiz (sem parent)"""
        return cls.query.filter_by(parent_id=None).all()
    
    @classmethod
    def get_arvore_categorias(cls):
        """Retorna a árvore completa de categorias"""
        def build_tree(categoria):
            return {
                'id': categoria.id,
                'nome': categoria.nome,
                'descricao': categoria.descricao,
                'cor': categoria.cor,
                'nivel': categoria.nivel,
                'subcategorias': [build_tree(sub) for sub in categoria.subcategorias]
            }
        
        categorias_raiz = cls.get_categorias_raiz()
        return [build_tree(categoria) for categoria in categorias_raiz]
    
    def to_dict(self, include_hierarchy=False):
        data = {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'cor': self.cor,
            'parent_id': self.parent_id,
            'nivel': self.nivel,
            'is_parent': self.is_parent,
            'transacoes_count': len(self.transacoes)
        }
        
        if include_hierarchy:
            data['nome_completo'] = self.nome_completo
            data['subcategorias'] = [sub.to_dict() for sub in self.subcategorias]
            
        return data
    
    def to_dict_hierarquico(self):
        """Retorna um dicionário com estrutura hierárquica incluindo subcategorias"""
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'cor': self.cor,
            'parent_id': self.parent_id,
            'nivel': self.nivel,
            'is_parent': self.is_parent,
            'transacoes_count': len(self.transacoes),
            'nome_completo': self.nome_completo,
            'subcategorias': [sub.to_dict_hierarquico() for sub in self.subcategorias]
        }

class TransacaoRecorrente(db.Model):
    """Modelo para gerenciar transações recorrentes"""
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.Enum(TipoTransacao), nullable=False)
    
    # Configuração de recorrência
    tipo_recorrencia = db.Column(db.Enum(TipoRecorrencia), nullable=False, default=TipoRecorrencia.UNICA)
    status = db.Column(db.Enum(StatusRecorrencia), nullable=False, default=StatusRecorrencia.ATIVA)
    
    # Datas importantes
    data_inicio = db.Column(db.DateTime, nullable=False)
    data_fim = db.Column(db.DateTime, nullable=True)  # Null = sem fim definido
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Controle de parcelas (para transações parceladas)
    total_parcelas = db.Column(db.Integer, nullable=True)  # Null = contínua (sem fim)
    parcelas_geradas = db.Column(db.Integer, default=0)
    
    # Relacionamentos
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    categoria = db.relationship('Categoria', backref='transacoes_recorrentes')
    conta_id = db.Column(db.Integer, db.ForeignKey('conta.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    transacoes = db.relationship('Transacao', backref='recorrencia', lazy=True)
    
    def __repr__(self):
        return f'<TransacaoRecorrente {self.descricao}: R$ {self.valor} ({self.tipo_recorrencia.value})>'
    
    @property
    def is_parcelada(self):
        """Verifica se é uma transação parcelada (tem número definido de parcelas)"""
        return self.total_parcelas is not None
    
    @property
    def is_continua(self):
        """Verifica se é uma transação contínua (sem fim definido)"""
        return self.total_parcelas is None
    
    @property
    def parcelas_restantes(self):
        """Retorna quantas parcelas ainda faltam ser geradas"""
        if self.is_continua:
            return None
        return max(0, self.total_parcelas - self.parcelas_geradas)
    
    @property
    def is_finalizada(self):
        """Verifica se a recorrência foi finalizada"""
        return (self.status == StatusRecorrencia.FINALIZADA or 
                (self.is_parcelada and self.parcelas_geradas >= self.total_parcelas) or
                (self.data_fim and datetime.utcnow() > self.data_fim))
    
    def calcular_proxima_data(self, data_base=None):
        """Calcula a próxima data de geração baseada no tipo de recorrência"""
        if data_base is None:
            data_base = self.data_inicio
        
        if self.tipo_recorrencia == TipoRecorrencia.SEMANAL:
            return data_base + timedelta(weeks=1)
        elif self.tipo_recorrencia == TipoRecorrencia.QUINZENAL:
            # Quinzenal = a cada 15 dias exatos
            return data_base + timedelta(days=15)
        elif self.tipo_recorrencia == TipoRecorrencia.MENSAL:
            return data_base + relativedelta(months=1)
        elif self.tipo_recorrencia == TipoRecorrencia.TRIMESTRAL:
            return data_base + relativedelta(months=3)
        elif self.tipo_recorrencia == TipoRecorrencia.SEMESTRAL:
            return data_base + relativedelta(months=6)
        elif self.tipo_recorrencia == TipoRecorrencia.ANUAL:
            return data_base + relativedelta(years=1)
        else:
            return data_base
    
    def gerar_proxima_transacao(self):
        """Gera a próxima transação da recorrência"""
        if self.is_finalizada:
            return None
        
        # Calcular data da próxima transação
        if self.transacoes:
            # Usar a data da última transação gerada
            ultima_transacao = max(self.transacoes, key=lambda t: t.data_transacao)
            proxima_data = self.calcular_proxima_data(ultima_transacao.data_transacao)
        else:
            # Primeira transação usa a data de início
            proxima_data = self.data_inicio
        
        # Verificar se não passou do limite
        if self.data_fim and proxima_data > self.data_fim:
            self.status = StatusRecorrencia.FINALIZADA
            db.session.commit()
            return None
        
        # Criar nova transação
        nova_transacao = Transacao(
            descricao=f"{self.descricao}" + 
                      (f" - Parcela {self.parcelas_geradas + 1}/{self.total_parcelas}" if self.is_parcelada else ""),
            valor=self.valor,
            tipo=self.tipo,
            data_transacao=proxima_data,
            categoria_id=self.categoria_id,
            conta_id=self.conta_id,
            recorrencia_id=self.id,
            user_id=self.user_id  # Adicionando o user_id
        )
        
        db.session.add(nova_transacao)
        self.parcelas_geradas += 1
        
        # Verificar se finalizou as parcelas
        if self.is_parcelada and self.parcelas_geradas >= self.total_parcelas:
            self.status = StatusRecorrencia.FINALIZADA
        
        db.session.commit()
        return nova_transacao
    
    def gerar_transacoes_pendentes(self, meses_futuros=24):
        """
        Gera todas as transações pendentes até a data_fim, se definida,
        ou até o número de meses futuros especificado.
        
        Args:
            meses_futuros (int): Quantos meses para frente gerar (padrão: 24)
            
        Returns:
            Lista de transações geradas
        """
        transacoes_geradas = []
        hoje = datetime.utcnow()
        
        # Verificar se a recorrência já foi finalizada manualmente ou por parcelas
        if self.status == StatusRecorrencia.FINALIZADA or \
           (self.is_parcelada and self.parcelas_geradas >= self.total_parcelas):
            print(f"Recorrência {self.id} já finalizada - Status: {self.status.value}, Parcelas: {self.parcelas_geradas}/{self.total_parcelas if self.total_parcelas else 'Indefinido'}")
            return transacoes_geradas
            
        # Verificar explicitamente o status
        if self.status != StatusRecorrencia.ATIVA:
            print(f"AVISO: Recorrência {self.id} não está ativa. Status atual: {self.status.value}")
            return transacoes_geradas
        
        # Definir data limite de geração - SEMPRE usar a data atual + meses_futuros
        # independentemente de transações existentes
        if self.data_fim:
            # Se tem data_fim, gerar todas as transações até essa data
            data_limite = self.data_fim
        else:
            # Caso contrário, gerar para os próximos X meses a partir de HOJE
            # Isso é crítico: sempre usar a data atual como base, não a última transação
            data_limite = hoje + relativedelta(months=meses_futuros)
        
        # Log de debug
        print(f"Gerando transações para {self.descricao} (ID: {self.id})")
        print(f"Data início: {self.data_inicio}, Data fim: {self.data_fim}")
        print(f"Data limite de geração: {data_limite} (hoje + {meses_futuros} meses)")
        print(f"Tipo de recorrência: {self.tipo_recorrencia.value}")
        
        # CRUCIAL: Determinar a próxima data a partir da qual devemos gerar transações
        proxima_data = None
        
        if self.transacoes:
            try:
                # Obter a última transação gerada
                ultima_transacao = max(self.transacoes, key=lambda t: t.data_transacao)
                proxima_data = self.calcular_proxima_data(ultima_transacao.data_transacao)
                print(f"Última transação: {ultima_transacao.data_transacao}, Próxima data: {proxima_data}")
            except Exception as e:
                print(f"Erro ao calcular próxima data: {str(e)}")
                proxima_data = self.data_inicio
        else:
            proxima_data = self.data_inicio
            print(f"Primeira transação, usando data_inicio: {proxima_data}")
        
        # NUNCA verificar se já existem transações até a data_limite
        # Sempre gerar transações independentemente das existentes
        
        # Loop de geração de transações
        max_iteracoes = 1000  # Aumentado para garantir geração adequada
        iteracoes = 0
        
        # Continuamos enquanto:
        # 1. A recorrência não estiver finalizada
        # 2. Não atingirmos o limite máximo de iterações (segurança)
        while not self.is_finalizada and iteracoes < max_iteracoes:
            iteracoes += 1
            
            # Calcular data da próxima transação
            if iteracoes > 1 and self.transacoes:  # Já calculamos proxima_data para a primeira iteração
                try:
                    ultima_transacao = max(self.transacoes, key=lambda t: t.data_transacao)
                    proxima_data = self.calcular_proxima_data(ultima_transacao.data_transacao)
                    print(f"Iteração {iteracoes}: Próxima data calculada: {proxima_data}")
                except Exception as e:
                    print(f"Erro ao calcular próxima data: {str(e)}")
                    break
            
            # Verificar se estamos dentro do limite de geração (data_fim ou meses_futuros)
            if proxima_data > data_limite:
                print(f"Próxima data {proxima_data} excede data limite {data_limite}")
                break
            
            # CRÍTICO: SEMPRE tentar gerar a próxima transação independentemente de qualquer outra verificação
            print(f"Gerando transação para data {proxima_data}")
            nova_transacao = self.gerar_proxima_transacao()
            
            if nova_transacao:
                print(f"Nova transação gerada: {nova_transacao.descricao} - {nova_transacao.data_transacao}")
                transacoes_geradas.append(nova_transacao)
            else:
                # Se não conseguiu gerar mais transações, a recorrência foi finalizada
                print("Não foi possível gerar mais transações. Recorrência finalizada.")
                break
        
        if iteracoes >= max_iteracoes:
            print(f"ATENÇÃO: Limite máximo de iterações atingido para recorrência {self.id}")
        
        print(f"Total de transações geradas: {len(transacoes_geradas)}")
        return transacoes_geradas
    
    def to_dict(self):
        return {
            'id': self.id,
            'descricao': self.descricao,
            'valor': self.valor,
            'tipo': self.tipo.value,
            'tipo_recorrencia': self.tipo_recorrencia.value,
            'status': self.status.value,
            'data_inicio': self.data_inicio.strftime('%Y-%m-%d'),
            'data_fim': self.data_fim.strftime('%Y-%m-%d') if self.data_fim else None,
            'total_parcelas': self.total_parcelas,
            'parcelas_geradas': self.parcelas_geradas,
            'parcelas_restantes': self.parcelas_restantes,
            'is_parcelada': self.is_parcelada,
            'is_continua': self.is_continua,
            'is_finalizada': self.is_finalizada,
            'categoria': self.categoria.nome,
            'categoria_cor': self.categoria.cor,
            'conta': self.conta.nome,
            'conta_cor': self.conta.cor,
            'transacoes_count': len(self.transacoes)
        }

class Transacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.Enum(TipoTransacao), nullable=False)
    data_transacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Chaves estrangeiras
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    conta_id = db.Column(db.Integer, db.ForeignKey('conta.id'), nullable=False)
    recorrencia_id = db.Column(db.Integer, db.ForeignKey('transacao_recorrente.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Relacionamento com tags
    tags = db.relationship('Tag', secondary=transacao_tags, back_populates='transacoes')
    
    def __repr__(self):
        return f'<Transacao {self.descricao}: R$ {self.valor}>'
    
    @property
    def is_recorrente(self):
        """Verifica se a transação é parte de uma recorrência"""
        return self.recorrencia_id is not None
    
    @property
    def tags_nomes(self):
        """Retorna uma lista com os nomes das tags"""
        return [tag.nome for tag in self.tags]
    
    @property
    def tags_string(self):
        """Retorna as tags como string separada por vírgulas"""
        return ', '.join(self.tags_nomes)
    
    def add_tag(self, tag_nome):
        """Adiciona uma tag à transação"""
        tag = Tag.get_or_create(tag_nome)
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag_nome):
        """Remove uma tag da transação"""
        tag = Tag.query.filter(db.func.lower(Tag.nome) == tag_nome.lower()).first()
        if tag and tag in self.tags:
            self.tags.remove(tag)
    
    def set_tags_from_string(self, tags_string):
        """Define as tags a partir de uma string separada por vírgulas"""
        # Limpar tags existentes
        self.tags.clear()
        
        if tags_string:
            tags_nomes = [nome.strip() for nome in tags_string.split(',') if nome.strip()]
            for tag_nome in tags_nomes:
                self.add_tag(tag_nome)
    
    def to_dict(self):
        return {
            'id': self.id,
            'descricao': self.descricao,
            'valor': self.valor,
            'tipo': self.tipo.value,
            'data_transacao': self.data_transacao.strftime('%Y-%m-%d'),
            'categoria': self.categoria.nome,
            'categoria_cor': self.categoria.cor,
            'conta': self.conta.nome,
            'conta_cor': self.conta.cor,
            'is_recorrente': self.is_recorrente,
            'recorrencia_id': self.recorrencia_id,
            'tags': self.tags_nomes,
            'tags_string': self.tags_string
        }

# === MODELO DE USUÁRIO E AUTENTICAÇÃO ===

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp

class Usuario(UserMixin, db.Model):
    """Modelo de usuário com suporte a MFA"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)  # Nome de exibição
    email = db.Column(db.String(120), unique=True, nullable=False)  # Login por email
    password_hash = db.Column(db.String(512), nullable=False)
    
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
    
    # Autenticação via Google
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    
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
        import json
        self.password_reset_token = json.dumps(token_data)
        db.session.commit()
        
        return token
    
    def verify_password_reset_token(self, token):
        """Verifica se o token de redefinição de senha é válido"""
        if not self.password_reset_token:
            return False
        
        import json
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


class Tema(db.Model):
    """Modelo para armazenar temas/paletas de cores do sistema"""
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    descricao = db.Column(db.String(200))
    is_default = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Cores para modo claro
    cor_primaria = db.Column(db.String(7), default='#007bff')  # Azul
    cor_secundaria = db.Column(db.String(7), default='#6c757d')  # Cinza
    cor_sucesso = db.Column(db.String(7), default='#28a745')  # Verde
    cor_perigo = db.Column(db.String(7), default='#dc3545')  # Vermelho
    cor_alerta = db.Column(db.String(7), default='#ffc107')  # Amarelo
    cor_info = db.Column(db.String(7), default='#17a2b8')  # Azul claro
    cor_fundo = db.Column(db.String(7), default='#ffffff')  # Branco
    cor_texto = db.Column(db.String(7), default='#212529')  # Quase preto
    
    # Cores para modo escuro
    cor_primaria_dark = db.Column(db.String(7), default='#375a7f')  # Azul escuro
    cor_secundaria_dark = db.Column(db.String(7), default='#444444')  # Cinza escuro
    cor_sucesso_dark = db.Column(db.String(7), default='#00bc8c')  # Verde escuro
    cor_perigo_dark = db.Column(db.String(7), default='#e74c3c')  # Vermelho escuro
    cor_alerta_dark = db.Column(db.String(7), default='#f39c12')  # Amarelo escuro
    cor_info_dark = db.Column(db.String(7), default='#3498db')  # Azul escuro claro
    cor_fundo_dark = db.Column(db.String(7), default='#222222')  # Quase preto
    cor_texto_dark = db.Column(db.String(7), default='#ffffff')  # Branco
    
    def to_dict(self):
        """Converte o tema para dicionário"""
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'is_default': self.is_default,
            'light': {
                'primary': self.cor_primaria,
                'secondary': self.cor_secundaria,
                'success': self.cor_sucesso,
                'danger': self.cor_perigo,
                'warning': self.cor_alerta,
                'info': self.cor_info,
                'background': self.cor_fundo,
                'text': self.cor_texto
            },
            'dark': {
                'primary': self.cor_primaria_dark,
                'secondary': self.cor_secundaria_dark,
                'success': self.cor_sucesso_dark,
                'danger': self.cor_perigo_dark,
                'warning': self.cor_alerta_dark,
                'info': self.cor_info_dark,
                'background': self.cor_fundo_dark,
                'text': self.cor_texto_dark
            }
        }
    
    @classmethod
    def get_default(cls):
        """Retorna o tema padrão ou cria um se não existir"""
        tema_default = cls.query.filter_by(is_default=True).first()
        if not tema_default:
            tema_default = cls(
                nome="Padrão",
                descricao="Tema padrão do sistema",
                is_default=True
            )
            db.session.add(tema_default)
            db.session.commit()
        return tema_default
    
    def __repr__(self):
        return f'<Tema {self.nome}>'
