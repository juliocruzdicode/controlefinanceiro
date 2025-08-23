"""
Serviço para gerenciamento de transações recorrentes
"""
from datetime import datetime, date, timedelta
from app import db
from app.models.recurring_transaction import TransacaoRecorrente
from app.models.enums import TipoTransacao, Periodicidade, StatusRecorrencia
from app.services.transaction_service import TransacaoService

class TransacaoRecorrenteService:
    """
    Serviço para gerenciamento de transações recorrentes, seguindo o princípio de responsabilidade única (S de SOLID)
    """
    
    @staticmethod
    def criar_transacao_recorrente(descricao, valor, tipo, data_inicial, periodicidade, 
                                   categoria_id, conta_id, user_id, parcelas_total=None, 
                                   dia_cobranca=None, dia_semana=None, tags_string=None):
        """Cria uma nova transação recorrente"""
        # Validação de tipo e periodicidade
        if not isinstance(tipo, TipoTransacao):
            tipo = TipoTransacao(tipo)
        
        if not isinstance(periodicidade, Periodicidade):
            periodicidade = Periodicidade(periodicidade)
        
        # Conversão de data se necessário
        if isinstance(data_inicial, str):
            data_inicial = datetime.strptime(data_inicial, '%Y-%m-%d')
        elif isinstance(data_inicial, date):
            data_inicial = datetime.combine(data_inicial, datetime.min.time())
        
        transacao_recorrente = TransacaoRecorrente(
            descricao=descricao,
            valor=valor,
            tipo=tipo,
            data_inicial=data_inicial,
            periodicidade=periodicidade,
            categoria_id=categoria_id,
            conta_id=conta_id,
            user_id=user_id,
            parcelas_total=parcelas_total,
            dia_cobranca=dia_cobranca,
            dia_semana=dia_semana,
            status=StatusRecorrencia.ATIVA
        )
        
        # Adiciona tags se fornecidas
        if tags_string:
            transacao_recorrente.tags_string = tags_string
            
        db.session.add(transacao_recorrente)
        db.session.commit()
        
        return transacao_recorrente
    
    @staticmethod
    def obter_recorrencia_por_id(recorrencia_id, user_id):
        """Retorna uma transação recorrente específica pelo ID, verificando o user_id para segurança"""
        return TransacaoRecorrente.query.filter_by(id=recorrencia_id, user_id=user_id).first()
    
    @staticmethod
    def obter_recorrencias_usuario(user_id, incluir_inativas=False, incluir_finalizadas=False):
        """Retorna transações recorrentes de um usuário"""
        query = TransacaoRecorrente.query.filter_by(user_id=user_id)
        
        if not incluir_inativas:
            query = query.filter(TransacaoRecorrente.status != StatusRecorrencia.INATIVA)
            
        if not incluir_finalizadas:
            query = query.filter(TransacaoRecorrente.status != StatusRecorrencia.FINALIZADA)
        
        return query.order_by(TransacaoRecorrente.data_inicial).all()
    
    @staticmethod
    def atualizar_recorrencia(recorrencia_id, user_id, **kwargs):
        """Atualiza uma transação recorrente existente"""
        recorrencia = TransacaoRecorrenteService.obter_recorrencia_por_id(recorrencia_id, user_id)
        if not recorrencia:
            return None
        
        # Campos que podem ser atualizados
        campos_permitidos = ['descricao', 'valor', 'tipo', 'data_inicial', 'periodicidade', 
                            'categoria_id', 'conta_id', 'parcelas_total', 'dia_cobranca', 
                            'dia_semana', 'status', 'tags_string']
        
        for campo, valor in kwargs.items():
            if campo in campos_permitidos:
                if campo == 'tipo' and not isinstance(valor, TipoTransacao):
                    valor = TipoTransacao(valor)
                elif campo == 'periodicidade' and not isinstance(valor, Periodicidade):
                    valor = Periodicidade(valor)
                elif campo == 'status' and not isinstance(valor, StatusRecorrencia):
                    valor = StatusRecorrencia(valor)
                elif campo == 'data_inicial' and isinstance(valor, str):
                    valor = datetime.strptime(valor, '%Y-%m-%d')
                elif campo == 'tags_string':
                    recorrencia.tags_string = valor
                    continue
                
                setattr(recorrencia, campo, valor)
        
        db.session.commit()
        return recorrencia
    
    @staticmethod
    def cancelar_recorrencia(recorrencia_id, user_id):
        """Marca uma recorrência como inativa"""
        recorrencia = TransacaoRecorrenteService.obter_recorrencia_por_id(recorrencia_id, user_id)
        if not recorrencia:
            return False
        
        recorrencia.status = StatusRecorrencia.INATIVA
        db.session.commit()
        return True
    
    @staticmethod
    def excluir_recorrencia(recorrencia_id, user_id, excluir_transacoes=False):
        """
        Exclui uma recorrência e opcionalmente suas transações.
        Se excluir_transacoes=False, apenas desvincula as transações.
        """
        recorrencia = TransacaoRecorrenteService.obter_recorrencia_por_id(recorrencia_id, user_id)
        if not recorrencia:
            return False
        
        if excluir_transacoes:
            # Exclui todas as transações vinculadas
            for transacao in recorrencia.transacoes:
                TransacaoService.excluir_transacao(transacao.id, user_id)
        else:
            # Apenas desvincula as transações
            for transacao in recorrencia.transacoes:
                transacao.recorrencia_id = None
        
        db.session.delete(recorrencia)
        db.session.commit()
        return True
    
    @staticmethod
    def gerar_proximas_transacoes(user_id=None, dias_futuro=7):
        """
        Gera as próximas transações recorrentes que deveriam ocorrer.
        Verifica todas as recorrências ativas e gera as transações pendentes.
        
        Parâmetros:
        - user_id: se fornecido, gera apenas para esse usuário
        - dias_futuro: gera transações para até X dias no futuro
        """
        hoje = datetime.utcnow().date()
        data_limite = hoje + timedelta(days=dias_futuro)
        
        # Filtra por usuário ou todas as recorrências ativas
        if user_id:
            recorrencias = TransacaoRecorrente.query.filter_by(
                user_id=user_id, 
                status=StatusRecorrencia.ATIVA
            ).all()
        else:
            recorrencias = TransacaoRecorrente.query.filter_by(
                status=StatusRecorrencia.ATIVA
            ).all()
        
        transacoes_geradas = []
        
        for recorrencia in recorrencias:
            # Verifica se a recorrência está em dia
            proxima_data = recorrencia.proxima_data
            if not proxima_data or proxima_data.date() > data_limite:
                continue
            
            # Gera a próxima transação
            transacao = recorrencia.gerar_proxima_transacao()
            if transacao:
                transacoes_geradas.append(transacao)
                
                # Verifica se há mais transações a gerar dentro do período
                while True:
                    proxima_data = recorrencia.proxima_data
                    if not proxima_data or proxima_data.date() > data_limite:
                        break
                    
                    transacao = recorrencia.gerar_proxima_transacao()
                    if transacao:
                        transacoes_geradas.append(transacao)
                    else:
                        break
        
        return transacoes_geradas
