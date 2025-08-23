"""
Modelo de categorias para classificação de transações
"""
from app import db
from sqlalchemy import func

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
    def get_categorias_raiz(cls, user_id):
        """Retorna apenas as categorias raiz (sem parent) de um usuário"""
        return cls.query.filter_by(parent_id=None, user_id=user_id).all()
    
    @classmethod
    def get_arvore_categorias(cls, user_id):
        """Retorna a árvore completa de categorias de um usuário"""
        def build_tree(categoria):
            return {
                'id': categoria.id,
                'nome': categoria.nome,
                'descricao': categoria.descricao,
                'cor': categoria.cor,
                'nivel': categoria.nivel,
                'subcategorias': [build_tree(sub) for sub in categoria.subcategorias]
            }
        
        categorias_raiz = cls.get_categorias_raiz(user_id)
        return [build_tree(categoria) for categoria in categorias_raiz]
    
    def to_dict(self, include_hierarchy=False):
        """Retorna um dicionário com as informações da categoria"""
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
