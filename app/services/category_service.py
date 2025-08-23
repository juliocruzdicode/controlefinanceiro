"""
Criação de serviços para separar a lógica de negócios da camada de apresentação
"""
from app import db
from app.models.category import Categoria

class CategoriaService:
    """
    Serviço para gerenciamento de categorias, seguindo o princípio de responsabilidade única (S de SOLID)
    """
    
    @staticmethod
    def criar_categoria(nome, cor, user_id, categoria_pai_id=None):
        """Cria uma nova categoria"""
        categoria = Categoria(
            nome=nome,
            cor=cor,
            categoria_pai_id=categoria_pai_id,
            user_id=user_id
        )
        db.session.add(categoria)
        db.session.commit()
        return categoria
    
    @staticmethod
    def obter_categorias_usuario(user_id):
        """Retorna todas as categorias de um usuário"""
        return Categoria.query.filter_by(user_id=user_id).all()
    
    @staticmethod
    def obter_categorias_raiz(user_id):
        """Retorna as categorias de nível raiz (sem pai) de um usuário"""
        return Categoria.query.filter_by(user_id=user_id, categoria_pai_id=None).all()
    
    @staticmethod
    def obter_categoria_por_id(categoria_id, user_id):
        """Retorna uma categoria específica pelo ID, verificando o user_id para segurança"""
        return Categoria.query.filter_by(id=categoria_id, user_id=user_id).first()
    
    @staticmethod
    def atualizar_categoria(categoria_id, user_id, nome=None, cor=None, categoria_pai_id=None):
        """Atualiza uma categoria existente"""
        categoria = CategoriaService.obter_categoria_por_id(categoria_id, user_id)
        if not categoria:
            return None
        
        if nome is not None:
            categoria.nome = nome
        if cor is not None:
            categoria.cor = cor
        
        # Evita ciclos na hierarquia
        if categoria_pai_id is not None and CategoriaService._verifica_ciclo(categoria, categoria_pai_id):
            categoria.categoria_pai_id = categoria_pai_id
        
        db.session.commit()
        return categoria
    
    @staticmethod
    def excluir_categoria(categoria_id, user_id):
        """Exclui uma categoria, movendo as transações para a categoria padrão"""
        categoria = CategoriaService.obter_categoria_por_id(categoria_id, user_id)
        if not categoria:
            return False
        
        # Move as transações para a categoria padrão se houver uma
        categoria_padrao = Categoria.query.filter_by(user_id=user_id, nome='Outros').first()
        if not categoria_padrao:
            categoria_padrao = CategoriaService.criar_categoria('Outros', '#777777', user_id)
        
        for transacao in categoria.transacoes:
            transacao.categoria_id = categoria_padrao.id
        
        # Move as subcategorias para a categoria pai ou para raiz
        for subcategoria in categoria.subcategorias:
            subcategoria.categoria_pai_id = categoria.categoria_pai_id
        
        db.session.delete(categoria)
        db.session.commit()
        return True
    
    @staticmethod
    def _verifica_ciclo(categoria, novo_pai_id):
        """Verifica se a mudança de pai causaria um ciclo na hierarquia"""
        # Não pode ser seu próprio pai
        if categoria.id == novo_pai_id:
            return False
        
        # Verifica se o novo pai seria um dos descendentes
        pai_atual = Categoria.query.get(novo_pai_id)
        while pai_atual:
            if pai_atual.id == categoria.id:
                return False
            pai_atual = pai_atual.categoria_pai
        
        return True
    
    @staticmethod
    def criar_categorias_padrao(user_id):
        """Cria categorias padrão para um novo usuário"""
        # Categorias de Despesa
        despesas = CategoriaService.criar_categoria('Despesas', '#e74c3c', user_id)
        
        # Subcategorias de Despesas
        CategoriaService.criar_categoria('Alimentação', '#e67e22', user_id, despesas.id)
        CategoriaService.criar_categoria('Moradia', '#f1c40f', user_id, despesas.id)
        CategoriaService.criar_categoria('Transporte', '#2ecc71', user_id, despesas.id)
        CategoriaService.criar_categoria('Saúde', '#3498db', user_id, despesas.id)
        CategoriaService.criar_categoria('Educação', '#9b59b6', user_id, despesas.id)
        CategoriaService.criar_categoria('Lazer', '#1abc9c', user_id, despesas.id)
        CategoriaService.criar_categoria('Serviços', '#34495e', user_id, despesas.id)
        
        # Categorias de Receita
        receitas = CategoriaService.criar_categoria('Receitas', '#2ecc71', user_id)
        
        # Subcategorias de Receitas
        CategoriaService.criar_categoria('Salário', '#27ae60', user_id, receitas.id)
        CategoriaService.criar_categoria('Investimentos', '#16a085', user_id, receitas.id)
        CategoriaService.criar_categoria('Vendas', '#2980b9', user_id, receitas.id)
        CategoriaService.criar_categoria('Presentes', '#8e44ad', user_id, receitas.id)
        
        # Categoria para itens não categorizados
        CategoriaService.criar_categoria('Outros', '#95a5a6', user_id)
        
        return True
    
    @staticmethod
    def aplicar_categorias_padrao_para_usuario(user_id):
        """Aplica categorias padrão para um usuário existente, evitando duplicatas"""
        # Verifica se o usuário já tem categorias
        categorias_existentes = CategoriaService.obter_categorias_usuario(user_id)
        nomes_existentes = {c.nome.lower() for c in categorias_existentes}
        
        # Categorias de Despesa
        if 'despesas' not in nomes_existentes:
            despesas = CategoriaService.criar_categoria('Despesas', '#e74c3c', user_id)
        else:
            despesas = next(c for c in categorias_existentes if c.nome.lower() == 'despesas')
        
        # Subcategorias de Despesas
        subcategorias_despesas = [
            ('Alimentação', '#e67e22'),
            ('Moradia', '#f1c40f'),
            ('Transporte', '#2ecc71'),
            ('Saúde', '#3498db'),
            ('Educação', '#9b59b6'),
            ('Lazer', '#1abc9c'),
            ('Serviços', '#34495e')
        ]
        
        for nome, cor in subcategorias_despesas:
            if nome.lower() not in nomes_existentes:
                CategoriaService.criar_categoria(nome, cor, user_id, despesas.id)
        
        # Categorias de Receita
        if 'receitas' not in nomes_existentes:
            receitas = CategoriaService.criar_categoria('Receitas', '#2ecc71', user_id)
        else:
            receitas = next(c for c in categorias_existentes if c.nome.lower() == 'receitas')
        
        # Subcategorias de Receitas
        subcategorias_receitas = [
            ('Salário', '#27ae60'),
            ('Investimentos', '#16a085'),
            ('Vendas', '#2980b9'),
            ('Presentes', '#8e44ad')
        ]
        
        for nome, cor in subcategorias_receitas:
            if nome.lower() not in nomes_existentes:
                CategoriaService.criar_categoria(nome, cor, user_id, receitas.id)
        
        # Categoria para itens não categorizados
        if 'outros' not in nomes_existentes:
            CategoriaService.criar_categoria('Outros', '#95a5a6', user_id)
        
        return True
