"""
Modelo de Transação para registro financeiro
"""
from datetime import datetime
from app import db
from app.models.enums import TipoTransacao
from app.models.tag import transacao_tags

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
        from app.models.tag import Tag
        tag = Tag.get_or_create(tag_nome, self.user_id)
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag_nome):
        """Remove uma tag da transação"""
        from app.models.tag import Tag
        tag = Tag.query.filter(db.func.lower(Tag.nome) == tag_nome.lower(), Tag.user_id == self.user_id).first()
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
        """Retorna um dicionário com as informações da transação"""
        return {
            'id': self.id,
            'descricao': self.descricao,
            'valor': self.valor,
            'tipo': self.tipo.value,
            'data_transacao': self.data_transacao.strftime('%Y-%m-%d'),
            'categoria': self.categoria.nome if self.categoria else None,
            'categoria_cor': self.categoria.cor if self.categoria else None,
            'conta': self.conta.nome if self.conta else None,
            'conta_cor': self.conta.cor if self.conta else None,
            'is_recorrente': self.is_recorrente,
            'recorrencia_id': self.recorrencia_id,
            'tags': self.tags_nomes,
            'tags_string': self.tags_string
        }
