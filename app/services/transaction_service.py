"""
Serviço para gerenciamento de transações
"""
from datetime import datetime, date
from sqlalchemy import extract, func
from app import db
from app.models.transaction import Transacao
from app.models.category import Categoria
from app.models.account import Conta
from app.models.tag import Tag
from app.models.enums import TipoTransacao

class TransacaoService:
    """
    Serviço para gerenciamento de transações, seguindo o princípio de responsabilidade única (S de SOLID)
    """
    
    @staticmethod
    def criar_transacao(descricao, valor, tipo, data_transacao, categoria_id, conta_id, user_id, tags_string=None, recorrencia_id=None):
        """Cria uma nova transação"""
        # Validação de tipo
        if not isinstance(tipo, TipoTransacao):
            tipo = TipoTransacao(tipo)
        
        # Conversão de data se necessário
        if isinstance(data_transacao, str):
            data_transacao = datetime.strptime(data_transacao, '%Y-%m-%d')
        elif isinstance(data_transacao, date):
            data_transacao = datetime.combine(data_transacao, datetime.min.time())
        
        transacao = Transacao(
            descricao=descricao,
            valor=valor,
            tipo=tipo,
            data_transacao=data_transacao,
            categoria_id=categoria_id,
            conta_id=conta_id,
            user_id=user_id,
            recorrencia_id=recorrencia_id
        )
        
        db.session.add(transacao)
        
        # Adiciona tags se fornecidas
        if tags_string:
            transacao.set_tags_from_string(tags_string)
            
        # Atualiza o saldo da conta
        conta = Conta.query.get(conta_id)
        if tipo == TipoTransacao.RECEITA:
            conta.saldo += valor
        else:
            conta.saldo -= valor
            
        db.session.commit()
        return transacao
    
    @staticmethod
    def obter_transacao_por_id(transacao_id, user_id):
        """Retorna uma transação específica pelo ID, verificando o user_id para segurança"""
        return Transacao.query.filter_by(id=transacao_id, user_id=user_id).first()
    
    @staticmethod
    def obter_transacoes_usuario(user_id, limit=None, offset=None, filtros=None):
        """
        Retorna transações de um usuário com opções de filtro
        
        Parâmetros:
        - user_id: ID do usuário
        - limit: Limite de resultados
        - offset: Deslocamento para paginação
        - filtros: Dicionário com filtros opcionais (data_inicio, data_fim, tipo, categoria_id, conta_id, tag)
        """
        query = Transacao.query.filter_by(user_id=user_id)
        
        if filtros:
            if 'data_inicio' in filtros and filtros['data_inicio']:
                data_inicio = filtros['data_inicio']
                if isinstance(data_inicio, str):
                    data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
                query = query.filter(Transacao.data_transacao >= data_inicio)
            
            if 'data_fim' in filtros and filtros['data_fim']:
                data_fim = filtros['data_fim']
                if isinstance(data_fim, str):
                    data_fim = datetime.strptime(data_fim, '%Y-%m-%d')
                query = query.filter(Transacao.data_transacao <= data_fim)
            
            if 'tipo' in filtros and filtros['tipo']:
                tipo = filtros['tipo']
                if not isinstance(tipo, TipoTransacao):
                    tipo = TipoTransacao(tipo)
                query = query.filter(Transacao.tipo == tipo)
            
            if 'categoria_id' in filtros and filtros['categoria_id']:
                # Inclui subcategorias se uma categoria pai for selecionada
                categoria_ids = [filtros['categoria_id']]
                categoria = Categoria.query.get(filtros['categoria_id'])
                if categoria and categoria.subcategorias:
                    categoria_ids.extend([c.id for c in categoria.subcategorias])
                query = query.filter(Transacao.categoria_id.in_(categoria_ids))
            
            if 'conta_id' in filtros and filtros['conta_id']:
                query = query.filter(Transacao.conta_id == filtros['conta_id'])
            
            if 'tag' in filtros and filtros['tag']:
                tag = filtros['tag']
                # Filtra por tag
                query = query.join(Transacao.tags).filter(Tag.nome.ilike(f'%{tag}%'), Tag.user_id == user_id)
        
        # Ordena por data_transacao, mais recente primeiro
        query = query.order_by(Transacao.data_transacao.desc())
        
        # Aplica limit e offset se fornecidos
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def atualizar_transacao(transacao_id, user_id, **kwargs):
        """Atualiza uma transação existente"""
        transacao = TransacaoService.obter_transacao_por_id(transacao_id, user_id)
        if not transacao:
            return None
        
        # Salva o valor e tipo originais para ajustar o saldo da conta
        valor_original = transacao.valor
        tipo_original = transacao.tipo
        conta_original_id = transacao.conta_id
        
        # Atualiza os campos
        campos_permitidos = ['descricao', 'valor', 'tipo', 'data_transacao', 'categoria_id', 'conta_id', 'tags_string']
        for campo, valor in kwargs.items():
            if campo in campos_permitidos:
                if campo == 'tipo' and not isinstance(valor, TipoTransacao):
                    valor = TipoTransacao(valor)
                elif campo == 'data_transacao' and isinstance(valor, str):
                    valor = datetime.strptime(valor, '%Y-%m-%d')
                elif campo == 'tags_string':
                    transacao.set_tags_from_string(valor)
                    continue
                
                setattr(transacao, campo, valor)
        
        # Ajusta os saldos das contas
        if 'valor' in kwargs or 'tipo' in kwargs or 'conta_id' in kwargs:
            # Restaura o saldo original da conta
            conta_original = Conta.query.get(conta_original_id)
            if tipo_original == TipoTransacao.RECEITA:
                conta_original.saldo -= valor_original
            else:
                conta_original.saldo += valor_original
            
            # Aplica o novo valor na conta atual
            conta_atual = Conta.query.get(transacao.conta_id)
            if transacao.tipo == TipoTransacao.RECEITA:
                conta_atual.saldo += transacao.valor
            else:
                conta_atual.saldo -= transacao.valor
        
        db.session.commit()
        return transacao
    
    @staticmethod
    def excluir_transacao(transacao_id, user_id):
        """Exclui uma transação e ajusta o saldo da conta"""
        transacao = TransacaoService.obter_transacao_por_id(transacao_id, user_id)
        if not transacao:
            return False
        
        # Ajusta o saldo da conta
        conta = Conta.query.get(transacao.conta_id)
        if transacao.tipo == TipoTransacao.RECEITA:
            conta.saldo -= transacao.valor
        else:
            conta.saldo += transacao.valor
        
        db.session.delete(transacao)
        db.session.commit()
        return True
    
    @staticmethod
    def obter_resumo_mensal(user_id, ano, mes):
        """Obtém um resumo das transações de um mês específico"""
        # Total de receitas
        receitas = db.session.query(func.sum(Transacao.valor)).filter(
            Transacao.user_id == user_id,
            Transacao.tipo == TipoTransacao.RECEITA,
            extract('year', Transacao.data_transacao) == ano,
            extract('month', Transacao.data_transacao) == mes
        ).scalar() or 0
        
        # Total de despesas
        despesas = db.session.query(func.sum(Transacao.valor)).filter(
            Transacao.user_id == user_id,
            Transacao.tipo == TipoTransacao.DESPESA,
            extract('year', Transacao.data_transacao) == ano,
            extract('month', Transacao.data_transacao) == mes
        ).scalar() or 0
        
        # Transações por categoria (para gráficos)
        categorias_receitas = db.session.query(
            Categoria.nome,
            Categoria.cor,
            func.sum(Transacao.valor).label('total')
        ).join(
            Transacao, Transacao.categoria_id == Categoria.id
        ).filter(
            Transacao.user_id == user_id,
            Transacao.tipo == TipoTransacao.RECEITA,
            extract('year', Transacao.data_transacao) == ano,
            extract('month', Transacao.data_transacao) == mes
        ).group_by(
            Categoria.nome, Categoria.cor
        ).all()
        
        categorias_despesas = db.session.query(
            Categoria.nome,
            Categoria.cor,
            func.sum(Transacao.valor).label('total')
        ).join(
            Transacao, Transacao.categoria_id == Categoria.id
        ).filter(
            Transacao.user_id == user_id,
            Transacao.tipo == TipoTransacao.DESPESA,
            extract('year', Transacao.data_transacao) == ano,
            extract('month', Transacao.data_transacao) == mes
        ).group_by(
            Categoria.nome, Categoria.cor
        ).all()
        
        # Resumo diário para gráficos de linha
        dias_receitas = db.session.query(
            extract('day', Transacao.data_transacao).label('dia'),
            func.sum(Transacao.valor).label('total')
        ).filter(
            Transacao.user_id == user_id,
            Transacao.tipo == TipoTransacao.RECEITA,
            extract('year', Transacao.data_transacao) == ano,
            extract('month', Transacao.data_transacao) == mes
        ).group_by(
            'dia'
        ).all()
        
        dias_despesas = db.session.query(
            extract('day', Transacao.data_transacao).label('dia'),
            func.sum(Transacao.valor).label('total')
        ).filter(
            Transacao.user_id == user_id,
            Transacao.tipo == TipoTransacao.DESPESA,
            extract('year', Transacao.data_transacao) == ano,
            extract('month', Transacao.data_transacao) == mes
        ).group_by(
            'dia'
        ).all()
        
        return {
            'receitas': receitas,
            'despesas': despesas,
            'saldo': receitas - despesas,
            'categorias_receitas': [{'nome': c.nome, 'cor': c.cor, 'total': c.total} for c in categorias_receitas],
            'categorias_despesas': [{'nome': c.nome, 'cor': c.cor, 'total': c.total} for c in categorias_despesas],
            'dias_receitas': {int(d.dia): float(d.total) for d in dias_receitas},
            'dias_despesas': {int(d.dia): float(d.total) for d in dias_despesas}
        }
