"""
Modelo de tema para personalização visual
"""
from datetime import datetime
from app import db

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
    cor_fundo_escuro = db.Column(db.String(7), default='#343a40')  # Cinza escuro
    cor_texto_escuro = db.Column(db.String(7), default='#f8f9fa')  # Branco suave
    
    def __repr__(self):
        return f'<Tema {self.nome}>'
    
    @classmethod
    def get_default(cls):
        """Retorna o tema padrão"""
        default_tema = cls.query.filter_by(is_default=True).first()
        if not default_tema:
            default_tema = cls.query.first()  # Qualquer tema se não houver padrão
        if not default_tema:
            # Criar tema padrão se não existir nenhum
            default_tema = cls(
                nome="Padrão",
                descricao="Tema padrão do sistema",
                is_default=True
            )
            db.session.add(default_tema)
            db.session.commit()
        return default_tema
    
    def to_dict(self):
        """Retorna o tema como dicionário"""
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'is_default': self.is_default,
            'cor_primaria': self.cor_primaria,
            'cor_secundaria': self.cor_secundaria,
            'cor_sucesso': self.cor_sucesso,
            'cor_perigo': self.cor_perigo,
            'cor_alerta': self.cor_alerta,
            'cor_info': self.cor_info,
            'cor_fundo': self.cor_fundo,
            'cor_texto': self.cor_texto,
            'cor_fundo_escuro': self.cor_fundo_escuro,
            'cor_texto_escuro': self.cor_texto_escuro
        }
