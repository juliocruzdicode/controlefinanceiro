"""
Serviço para gerenciamento de temas
"""
from app import db
from app.models.theme import Tema

class TemaService:
    """
    Serviço para gerenciamento de temas, seguindo o princípio de responsabilidade única (S de SOLID)
    """
    
    @staticmethod
    def criar_tema(nome, cor_primaria, cor_secundaria, cor_background, 
                  cor_texto, cor_card, modo_escuro=False, publico=True, user_id=None):
        """Cria um novo tema"""
        tema = Tema(
            nome=nome,
            cor_primaria=cor_primaria,
            cor_secundaria=cor_secundaria,
            cor_background=cor_background,
            cor_texto=cor_texto,
            cor_card=cor_card,
            modo_escuro=modo_escuro,
            publico=publico,
            user_id=user_id
        )
        
        db.session.add(tema)
        db.session.commit()
        return tema
    
    @staticmethod
    def obter_tema_por_id(tema_id):
        """Retorna um tema específico pelo ID"""
        return Tema.query.get(tema_id)
    
    @staticmethod
    def obter_temas_publicos():
        """Retorna todos os temas públicos"""
        return Tema.query.filter_by(publico=True).all()
    
    @staticmethod
    def obter_temas_usuario(user_id):
        """Retorna todos os temas criados por um usuário"""
        return Tema.query.filter_by(user_id=user_id).all()
    
    @staticmethod
    def obter_temas_disponiveis(user_id):
        """Retorna todos os temas disponíveis para um usuário (públicos + próprios)"""
        return Tema.query.filter(
            (Tema.publico == True) | (Tema.user_id == user_id)
        ).all()
    
    @staticmethod
    def atualizar_tema(tema_id, user_id=None, **kwargs):
        """
        Atualiza um tema existente
        Se user_id for fornecido, verifica se o usuário tem permissão para editar o tema
        """
        tema = TemaService.obter_tema_por_id(tema_id)
        if not tema:
            return None
        
        # Verifica permissão: deve ser público ou pertencer ao usuário
        if user_id is not None and tema.user_id != user_id and not tema.publico:
            return None
        
        # Campos que podem ser atualizados
        campos_permitidos = [
            'nome', 'cor_primaria', 'cor_secundaria', 'cor_background', 
            'cor_texto', 'cor_card', 'modo_escuro', 'publico'
        ]
        
        for campo, valor in kwargs.items():
            if campo in campos_permitidos:
                setattr(tema, campo, valor)
        
        db.session.commit()
        return tema
    
    @staticmethod
    def excluir_tema(tema_id, user_id=None):
        """
        Exclui um tema
        Se user_id for fornecido, verifica se o usuário tem permissão para excluir o tema
        """
        tema = TemaService.obter_tema_por_id(tema_id)
        if not tema:
            return False
        
        # Verifica permissão: deve pertencer ao usuário
        if user_id is not None and tema.user_id != user_id:
            return False
        
        # Verifica se há usuários usando este tema
        usuarios_com_tema = tema.usuarios
        if usuarios_com_tema:
            # Redefine o tema desses usuários para o padrão
            tema_padrao = Tema.query.filter_by(nome='Padrão').first()
            for usuario in usuarios_com_tema:
                usuario.tema_id = tema_padrao.id if tema_padrao else None
        
        db.session.delete(tema)
        db.session.commit()
        return True
    
    @staticmethod
    def criar_temas_padrao():
        """Cria temas padrão do sistema, se não existirem"""
        temas_padrao = [
            {
                'nome': 'Padrão',
                'cor_primaria': '#3498db',
                'cor_secundaria': '#2ecc71',
                'cor_background': '#f5f5f5',
                'cor_texto': '#333333',
                'cor_card': '#ffffff',
                'modo_escuro': False,
                'publico': True
            },
            {
                'nome': 'Modo Escuro',
                'cor_primaria': '#3498db',
                'cor_secundaria': '#2ecc71',
                'cor_background': '#121212',
                'cor_texto': '#f5f5f5',
                'cor_card': '#1e1e1e',
                'modo_escuro': True,
                'publico': True
            },
            {
                'nome': 'Monocromático',
                'cor_primaria': '#555555',
                'cor_secundaria': '#999999',
                'cor_background': '#f8f8f8',
                'cor_texto': '#333333',
                'cor_card': '#ffffff',
                'modo_escuro': False,
                'publico': True
            },
            {
                'nome': 'Natureza',
                'cor_primaria': '#27ae60',
                'cor_secundaria': '#f1c40f',
                'cor_background': '#f0f9f0',
                'cor_texto': '#2c3e50',
                'cor_card': '#ffffff',
                'modo_escuro': False,
                'publico': True
            }
        ]
        
        temas_criados = []
        for tema_info in temas_padrao:
            # Verifica se já existe
            tema_existente = Tema.query.filter_by(nome=tema_info['nome'], publico=True).first()
            if not tema_existente:
                tema = TemaService.criar_tema(**tema_info)
                temas_criados.append(tema)
        
        return temas_criados
