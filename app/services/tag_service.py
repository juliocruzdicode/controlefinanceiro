"""
Serviço para gerenciamento de tags
"""
from app import db
from app.models.tag import Tag

class TagService:
    """
    Serviço para gerenciamento de tags, seguindo o princípio de responsabilidade única (S de SOLID)
    """
    
    @staticmethod
    def criar_tag(nome, user_id, cor=None):
        """Cria uma nova tag ou retorna uma existente"""
        # Verificar se a tag já existe para o usuário (case insensitive)
        tag = Tag.query.filter(db.func.lower(Tag.nome) == nome.lower(), Tag.user_id == user_id).first()
        
        if tag:
            return tag
        
        # Criar nova tag
        tag = Tag(
            nome=nome,
            user_id=user_id,
            cor=cor or '#3498db'  # Cor padrão se não fornecida
        )
        
        db.session.add(tag)
        db.session.commit()
        return tag
    
    @staticmethod
    def obter_tag_por_id(tag_id, user_id):
        """Retorna uma tag específica pelo ID, verificando o user_id para segurança"""
        return Tag.query.filter_by(id=tag_id, user_id=user_id).first()
    
    @staticmethod
    def obter_tag_por_nome(nome, user_id):
        """Retorna uma tag pelo nome, verificando o user_id para segurança"""
        return Tag.query.filter(db.func.lower(Tag.nome) == nome.lower(), Tag.user_id == user_id).first()
    
    @staticmethod
    def obter_tags_usuario(user_id):
        """Retorna todas as tags de um usuário"""
        return Tag.query.filter_by(user_id=user_id).order_by(Tag.nome).all()
    
    @staticmethod
    def atualizar_tag(tag_id, user_id, nome=None, cor=None):
        """Atualiza uma tag existente"""
        tag = TagService.obter_tag_por_id(tag_id, user_id)
        if not tag:
            return None
        
        if nome is not None:
            # Verifica se já existe outra tag com este nome
            tag_existente = Tag.query.filter(
                db.func.lower(Tag.nome) == nome.lower(), 
                Tag.user_id == user_id, 
                Tag.id != tag_id
            ).first()
            
            if tag_existente:
                return None
            
            tag.nome = nome
            
        if cor is not None:
            tag.cor = cor
        
        db.session.commit()
        return tag
    
    @staticmethod
    def excluir_tag(tag_id, user_id):
        """Exclui uma tag e a remove de todas as transações relacionadas"""
        tag = TagService.obter_tag_por_id(tag_id, user_id)
        if not tag:
            return False
        
        # Desvincula a tag de todas as transações
        for transacao in tag.transacoes:
            transacao.tags.remove(tag)
        
        db.session.delete(tag)
        db.session.commit()
        return True
    
    @staticmethod
    def obter_tags_populares(user_id, limit=10):
        """Retorna as tags mais utilizadas pelo usuário"""
        # Consulta para contar o número de transações por tag
        resultado = db.session.query(
            Tag, 
            db.func.count(Tag.transacoes).label('total')
        ).join(
            Tag.transacoes
        ).filter(
            Tag.user_id == user_id
        ).group_by(
            Tag.id
        ).order_by(
            db.desc('total')
        ).limit(limit).all()
        
        return [{'tag': tag, 'total': total} for tag, total in resultado]
    
    @staticmethod
    def pesquisar_tags(user_id, termo_pesquisa):
        """Pesquisa tags pelo nome"""
        return Tag.query.filter(
            Tag.user_id == user_id,
            Tag.nome.ilike(f'%{termo_pesquisa}%')
        ).order_by(Tag.nome).all()
    
    @staticmethod
    def processar_string_tags(tags_string, user_id):
        """
        Processa uma string de tags separadas por vírgula e retorna os objetos Tag
        Cria novas tags conforme necessário
        """
        if not tags_string:
            return []
        
        # Divide a string e remove espaços em branco
        nomes_tags = [nome.strip() for nome in tags_string.split(',') if nome.strip()]
        
        # Processa cada tag
        tags = []
        for nome in nomes_tags:
            tag = TagService.criar_tag(nome, user_id)
            tags.append(tag)
            
        return tags
