"""
Modelo de Transação Recorrente para registro financeiro
"""
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
from app import db
from app.models.enums import TipoTransacao, Periodicidade, StatusRecorrencia

class TransacaoRecorrente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.Enum(TipoTransacao), nullable=False)
    data_inicial = db.Column(db.DateTime, nullable=False)
    periodicidade = db.Column(db.Enum(Periodicidade), nullable=False)
    dia_cobranca = db.Column(db.Integer, nullable=True)  # Para mensal/anual
    dia_semana = db.Column(db.Integer, nullable=True)    # Para semanal
    parcelas_total = db.Column(db.Integer, nullable=True)  # Total de parcelas (opcional)
    parcelas_geradas = db.Column(db.Integer, default=0)    # Parcelas já geradas
    status = db.Column(db.Enum(StatusRecorrencia), default=StatusRecorrencia.ATIVA)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_modificacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags_lista = db.Column(db.Text, nullable=True)  # Tags como string JSON
    
    # Chaves estrangeiras
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    conta_id = db.Column(db.Integer, db.ForeignKey('conta.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Relacionamentos
    transacoes = db.relationship('Transacao', backref='recorrencia', lazy=True)
    
    def __repr__(self):
        return f'<TransacaoRecorrente {self.descricao}: R$ {self.valor} ({self.periodicidade.value})>'
    
    @property
    def proxima_data(self):
        """Calcula a próxima data de geração"""
        if self.status != StatusRecorrencia.ATIVA:
            return None
            
        if not self.transacoes:
            return self.data_inicial
            
        # Encontra a última transação gerada
        ultima_data = max(t.data_transacao for t in self.transacoes)
        
        # Calcula a próxima data baseada na periodicidade
        if self.periodicidade == Periodicidade.DIARIA:
            return ultima_data + timedelta(days=1)
        elif self.periodicidade == Periodicidade.SEMANAL:
            return ultima_data + timedelta(weeks=1)
        elif self.periodicidade == Periodicidade.QUINZENAL:
            return ultima_data + timedelta(days=15)
        elif self.periodicidade == Periodicidade.MENSAL:
            return ultima_data + relativedelta(months=1)
        elif self.periodicidade == Periodicidade.ANUAL:
            return ultima_data + relativedelta(years=1)
    
    @property
    def tags(self):
        """Retorna a lista de tags como array"""
        if self.tags_lista:
            return json.loads(self.tags_lista)
        return []
    
    @tags.setter
    def tags(self, tags_array):
        """Define as tags a partir de um array"""
        self.tags_lista = json.dumps(tags_array) if tags_array else None
    
    @property
    def tags_string(self):
        """Retorna as tags como string separada por vírgulas"""
        return ', '.join(self.tags)
    
    @tags_string.setter
    def tags_string(self, value):
        """Define as tags a partir de uma string separada por vírgulas"""
        if value:
            tags = [tag.strip() for tag in value.split(',') if tag.strip()]
            self.tags = tags
        else:
            self.tags = []
    
    def esta_finalizada(self):
        """Verifica se a recorrência está finalizada (todas as parcelas geradas)"""
        if self.parcelas_total is None:
            return False
        return self.parcelas_geradas >= self.parcelas_total
    
    def gerar_proxima_transacao(self):
        """Gera a próxima transação baseada na recorrência"""
        if self.status != StatusRecorrencia.ATIVA:
            return None
        
        if self.esta_finalizada():
            self.status = StatusRecorrencia.FINALIZADA
            db.session.commit()
            return None
        
        proxima_data = self.proxima_data
        if not proxima_data:
            return None
        
        # Criação da transação
        from app.models.transaction import Transacao
        
        transacao = Transacao(
            descricao=self.descricao,
            valor=self.valor,
            tipo=self.tipo,
            data_transacao=proxima_data,
            categoria_id=self.categoria_id,
            conta_id=self.conta_id,
            recorrencia_id=self.id,
            user_id=self.user_id
        )
        
        # Adiciona tags
        for tag_nome in self.tags:
            transacao.add_tag(tag_nome)
        
        db.session.add(transacao)
        
        # Atualiza o contador de parcelas
        self.parcelas_geradas += 1
        if self.esta_finalizada():
            self.status = StatusRecorrencia.FINALIZADA
        
        db.session.commit()
        return transacao
    
    def to_dict(self):
        """Retorna um dicionário com as informações da recorrência"""
        return {
            'id': self.id,
            'descricao': self.descricao,
            'valor': self.valor,
            'tipo': self.tipo.value,
            'data_inicial': self.data_inicial.strftime('%Y-%m-%d'),
            'periodicidade': self.periodicidade.value,
            'dia_cobranca': self.dia_cobranca,
            'dia_semana': self.dia_semana,
            'parcelas_total': self.parcelas_total,
            'parcelas_geradas': self.parcelas_geradas,
            'status': self.status.value,
            'categoria_id': self.categoria_id,
            'conta_id': self.conta_id,
            'tags': self.tags,
            'proxima_data': self.proxima_data.strftime('%Y-%m-%d') if self.proxima_data else None
        }
