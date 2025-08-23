"""
Serviço para gerenciamento de contas bancárias
"""
from app import db
from app.models.account import Conta
from app.models.enums import TipoConta

class ContaService:
    """
    Serviço para gerenciamento de contas, seguindo o princípio de responsabilidade única (S de SOLID)
    """
    
    @staticmethod
    def criar_conta(nome, tipo, saldo_inicial, cor, user_id, instituicao=None, descricao=None):
        """Cria uma nova conta bancária"""
        # Validação de tipo
        if not isinstance(tipo, TipoConta):
            tipo = TipoConta(tipo)
            
        conta = Conta(
            nome=nome,
            tipo=tipo,
            saldo=saldo_inicial,
            saldo_inicial=saldo_inicial,
            cor=cor,
            user_id=user_id,
            instituicao=instituicao,
            descricao=descricao
        )
        
        db.session.add(conta)
        db.session.commit()
        return conta
    
    @staticmethod
    def obter_contas_usuario(user_id):
        """Retorna todas as contas de um usuário"""
        return Conta.query.filter_by(user_id=user_id).order_by(Conta.nome).all()
    
    @staticmethod
    def obter_conta_por_id(conta_id, user_id):
        """Retorna uma conta específica pelo ID, verificando o user_id para segurança"""
        return Conta.query.filter_by(id=conta_id, user_id=user_id).first()
    
    @staticmethod
    def atualizar_conta(conta_id, user_id, **kwargs):
        """Atualiza uma conta existente"""
        conta = ContaService.obter_conta_por_id(conta_id, user_id)
        if not conta:
            return None
        
        # Campos que podem ser atualizados
        campos_permitidos = ['nome', 'tipo', 'saldo', 'saldo_inicial', 'cor', 'instituicao', 'descricao']
        
        for campo, valor in kwargs.items():
            if campo in campos_permitidos:
                if campo == 'tipo' and not isinstance(valor, TipoConta):
                    valor = TipoConta(valor)
                setattr(conta, campo, valor)
        
        db.session.commit()
        return conta
    
    @staticmethod
    def excluir_conta(conta_id, user_id):
        """
        Exclui uma conta se não tiver transações associadas.
        Retorna True se a exclusão for bem-sucedida, False se a conta tiver transações.
        """
        conta = ContaService.obter_conta_por_id(conta_id, user_id)
        if not conta:
            return False
        
        # Verifica se há transações vinculadas
        if conta.transacoes:
            return False
        
        db.session.delete(conta)
        db.session.commit()
        return True
    
    @staticmethod
    def criar_contas_padrao(user_id):
        """Cria contas padrão para um novo usuário"""
        contas = [
            ('Carteira', TipoConta.DINHEIRO, 0, '#2ecc71'),
            ('Conta Corrente', TipoConta.CONTA_CORRENTE, 0, '#3498db'),
            ('Poupança', TipoConta.POUPANCA, 0, '#9b59b6')
        ]
        
        for nome, tipo, saldo, cor in contas:
            ContaService.criar_conta(nome, tipo, saldo, cor, user_id)
        
        return True
    
    @staticmethod
    def obter_saldo_total(user_id):
        """Retorna o saldo total de todas as contas do usuário"""
        resultado = db.session.query(db.func.sum(Conta.saldo)).filter(Conta.user_id == user_id).scalar()
        return resultado or 0
    
    @staticmethod
    def recalcular_saldo(conta_id, user_id):
        """
        Recalcula o saldo de uma conta com base nas transações
        Útil para corrigir inconsistências
        """
        from app.models.transaction import Transacao
        from app.models.enums import TipoTransacao
        
        conta = ContaService.obter_conta_por_id(conta_id, user_id)
        if not conta:
            return False
        
        # Reinicia o saldo para o valor inicial
        novo_saldo = conta.saldo_inicial
        
        # Soma todas as receitas
        receitas = db.session.query(db.func.sum(Transacao.valor)).filter(
            Transacao.conta_id == conta_id,
            Transacao.tipo == TipoTransacao.RECEITA
        ).scalar() or 0
        
        # Subtrai todas as despesas
        despesas = db.session.query(db.func.sum(Transacao.valor)).filter(
            Transacao.conta_id == conta_id,
            Transacao.tipo == TipoTransacao.DESPESA
        ).scalar() or 0
        
        # Atualiza o saldo
        conta.saldo = novo_saldo + receitas - despesas
        db.session.commit()
        
        return conta
