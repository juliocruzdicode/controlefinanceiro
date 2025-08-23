"""
Modelo de Tag para classificação de transações
"""
from datetime import datetime
from app import db
from app.models.enums import TipoTransacao

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
    def get_tags_ativas(cls, user_id):
        """Retorna apenas as tags ativas de um usuário"""
        return cls.query.filter_by(ativa=True, user_id=user_id).order_by(cls.nome).all()
    
    @classmethod
    def get_or_create(cls, nome, user_id):
        """Obtém uma tag existente ou cria uma nova"""
        nome = nome.strip().lower()
        tag = cls.query.filter(db.func.lower(cls.nome) == nome, cls.user_id == user_id).first()
        if not tag:
            tag = cls(nome=nome.title(), user_id=user_id)  # Primeira letra maiúscula
            db.session.add(tag)
            db.session.commit()
        return tag
    
    def to_dict(self):
        """Retorna um dicionário com as informações da tag"""
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
