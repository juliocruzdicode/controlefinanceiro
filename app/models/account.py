"""
Modelo de Conta para gerenciamento financeiro
"""
from datetime import datetime
from app import db
from app.models.enums import TipoConta, TipoTransacao

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
    def get_contas_ativas(cls, user_id):
        """Retorna apenas as contas ativas de um usuário"""
        return cls.query.filter_by(ativa=True, user_id=user_id).all()
    
    def to_dict(self):
        """Retorna um dicionário com as informações da conta"""
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
