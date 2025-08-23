"""
Serviço para gerenciamento do dashboard e relatórios
"""
from datetime import datetime, date, timedelta
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from sqlalchemy import extract, func, and_, or_
from app import db
from app.models.transaction import Transacao
from app.models.category import Categoria
from app.models.account import Conta
from app.models.tag import Tag
from app.models.enums import TipoTransacao

class DashboardService:
    """
    Serviço para geração de dados de dashboard e relatórios, seguindo o princípio de responsabilidade única (S de SOLID)
    """
    
    @staticmethod
    def obter_resumo_dashboard(user_id, ano=None, mes=None):
        """
        Obtém um resumo completo para o dashboard
        
        Parâmetros:
        - user_id: ID do usuário
        - ano: Ano para filtrar (padrão: ano atual)
        - mes: Mês para filtrar (padrão: mês atual)
        
        Retorna um dicionário com:
        - saldo_total: Saldo total de todas as contas
        - receitas_mes: Total de receitas do mês
        - despesas_mes: Total de despesas do mês
        - saldo_mes: Saldo do mês (receitas - despesas)
        - contas: Lista de contas com saldos
        - grafico_categorias: Dados para gráfico de categorias
        - grafico_evolucao: Dados para gráfico de evolução diária
        - ultimas_transacoes: Últimas transações registradas
        """
        hoje = datetime.utcnow().date()
        
        # Define o período de análise
        if ano is None:
            ano = hoje.year
        if mes is None:
            mes = hoje.month
            
        primeiro_dia = date(ano, mes, 1)
        ultimo_dia = date(ano, mes, monthrange(ano, mes)[1])
        
        # Converte para datetime
        inicio_mes = datetime.combine(primeiro_dia, datetime.min.time())
        fim_mes = datetime.combine(ultimo_dia, datetime.max.time())
        
        # Saldo total em todas as contas
        saldo_total = db.session.query(func.sum(Conta.saldo)).filter(Conta.user_id == user_id).scalar() or 0
        
        # Total de receitas e despesas do mês
        receitas_mes = db.session.query(func.sum(Transacao.valor)).filter(
            Transacao.user_id == user_id,
            Transacao.tipo == TipoTransacao.RECEITA,
            Transacao.data_transacao >= inicio_mes,
            Transacao.data_transacao <= fim_mes
        ).scalar() or 0
        
        despesas_mes = db.session.query(func.sum(Transacao.valor)).filter(
            Transacao.user_id == user_id,
            Transacao.tipo == TipoTransacao.DESPESA,
            Transacao.data_transacao >= inicio_mes,
            Transacao.data_transacao <= fim_mes
        ).scalar() or 0
        
        # Lista de contas com saldos
        contas = Conta.query.filter_by(user_id=user_id).all()
        
        # Dados para gráfico de categorias (top 5 despesas)
        categorias_despesas = db.session.query(
            Categoria.nome,
            Categoria.cor,
            func.sum(Transacao.valor).label('total')
        ).join(
            Transacao, Transacao.categoria_id == Categoria.id
        ).filter(
            Transacao.user_id == user_id,
            Transacao.tipo == TipoTransacao.DESPESA,
            Transacao.data_transacao >= inicio_mes,
            Transacao.data_transacao <= fim_mes
        ).group_by(
            Categoria.id
        ).order_by(
            func.sum(Transacao.valor).desc()
        ).limit(5).all()
        
        # Dados para gráfico de evolução diária
        dias_mes = []
        for dia in range(1, ultimo_dia.day + 1):
            data = date(ano, mes, dia)
            if data <= hoje:  # Só considera até a data atual
                dias_mes.append(data)
        
        # Receitas diárias
        receitas_diarias = db.session.query(
            extract('day', Transacao.data_transacao).label('dia'),
            func.sum(Transacao.valor).label('total')
        ).filter(
            Transacao.user_id == user_id,
            Transacao.tipo == TipoTransacao.RECEITA,
            Transacao.data_transacao >= inicio_mes,
            Transacao.data_transacao <= fim_mes
        ).group_by(
            'dia'
        ).all()
        
        receitas_por_dia = {int(d.dia): float(d.total) for d in receitas_diarias}
        
        # Despesas diárias
        despesas_diarias = db.session.query(
            extract('day', Transacao.data_transacao).label('dia'),
            func.sum(Transacao.valor).label('total')
        ).filter(
            Transacao.user_id == user_id,
            Transacao.tipo == TipoTransacao.DESPESA,
            Transacao.data_transacao >= inicio_mes,
            Transacao.data_transacao <= fim_mes
        ).group_by(
            'dia'
        ).all()
        
        despesas_por_dia = {int(d.dia): float(d.total) for d in despesas_diarias}
        
        # Monta dados do gráfico de evolução
        evolucao_diaria = []
        for dia in range(1, ultimo_dia.day + 1):
            if date(ano, mes, dia) <= hoje:  # Só considera até a data atual
                receita_dia = receitas_por_dia.get(dia, 0)
                despesa_dia = despesas_por_dia.get(dia, 0)
                evolucao_diaria.append({
                    'dia': dia,
                    'receitas': receita_dia,
                    'despesas': despesa_dia,
                    'saldo': receita_dia - despesa_dia
                })
        
        # Últimas transações
        ultimas_transacoes = Transacao.query.filter_by(
            user_id=user_id
        ).order_by(
            Transacao.data_transacao.desc()
        ).limit(5).all()
        
        return {
            'saldo_total': saldo_total,
            'receitas_mes': receitas_mes,
            'despesas_mes': despesas_mes,
            'saldo_mes': receitas_mes - despesas_mes,
            'contas': contas,
            'grafico_categorias': [
                {'nome': c.nome, 'cor': c.cor, 'total': float(c.total)}
                for c in categorias_despesas
            ],
            'grafico_evolucao': evolucao_diaria,
            'ultimas_transacoes': ultimas_transacoes
        }
    
    @staticmethod
    def obter_comparacao_mensal(user_id, meses=6):
        """
        Obtém dados de comparação entre os últimos meses
        
        Parâmetros:
        - user_id: ID do usuário
        - meses: Número de meses para comparar (padrão: 6)
        
        Retorna um dicionário com:
        - labels: Lista de rótulos dos meses (ex: "Jan/2023")
        - receitas: Lista com valores totais de receitas por mês
        - despesas: Lista com valores totais de despesas por mês
        - saldos: Lista com saldos mensais (receitas - despesas)
        """
        hoje = datetime.utcnow().date()
        dados_meses = []
        
        # Gera a lista de meses para análise, do mais antigo para o mais recente
        for i in range(meses-1, -1, -1):
            data_mes = hoje.replace(day=1) - relativedelta(months=i)
            
            # Primeiro e último dia do mês
            primeiro_dia = date(data_mes.year, data_mes.month, 1)
            ultimo_dia = date(data_mes.year, data_mes.month, monthrange(data_mes.year, data_mes.month)[1])
            
            # Converte para datetime
            inicio_mes = datetime.combine(primeiro_dia, datetime.min.time())
            fim_mes = datetime.combine(ultimo_dia, datetime.max.time())
            
            # Total de receitas do mês
            receitas = db.session.query(func.sum(Transacao.valor)).filter(
                Transacao.user_id == user_id,
                Transacao.tipo == TipoTransacao.RECEITA,
                Transacao.data_transacao >= inicio_mes,
                Transacao.data_transacao <= fim_mes
            ).scalar() or 0
            
            # Total de despesas do mês
            despesas = db.session.query(func.sum(Transacao.valor)).filter(
                Transacao.user_id == user_id,
                Transacao.tipo == TipoTransacao.DESPESA,
                Transacao.data_transacao >= inicio_mes,
                Transacao.data_transacao <= fim_mes
            ).scalar() or 0
            
            # Adiciona aos dados
            dados_meses.append({
                'mes': data_mes.strftime('%b/%Y'),
                'receitas': float(receitas),
                'despesas': float(despesas),
                'saldo': float(receitas - despesas)
            })
        
        # Formata os dados para retorno
        return {
            'labels': [d['mes'] for d in dados_meses],
            'receitas': [d['receitas'] for d in dados_meses],
            'despesas': [d['despesas'] for d in dados_meses],
            'saldos': [d['saldo'] for d in dados_meses],
            'dados_meses': dados_meses
        }
    
    @staticmethod
    def obter_distribuicao_categorias(user_id, ano=None, mes=None, tipo=TipoTransacao.DESPESA):
        """
        Obtém a distribuição de valores por categoria
        
        Parâmetros:
        - user_id: ID do usuário
        - ano: Ano para filtrar (padrão: ano atual)
        - mes: Mês para filtrar (padrão: mês atual)
        - tipo: Tipo de transação (padrão: DESPESA)
        
        Retorna uma lista de dicionários com:
        - categoria: Nome da categoria
        - cor: Cor da categoria
        - total: Valor total
        - porcentagem: Porcentagem em relação ao total
        """
        hoje = datetime.utcnow().date()
        
        # Define o período de análise
        if ano is None:
            ano = hoje.year
        if mes is None:
            mes = hoje.month
            
        primeiro_dia = date(ano, mes, 1)
        ultimo_dia = date(ano, mes, monthrange(ano, mes)[1])
        
        # Converte para datetime
        inicio_mes = datetime.combine(primeiro_dia, datetime.min.time())
        fim_mes = datetime.combine(ultimo_dia, datetime.max.time())
        
        # Total por categoria
        categorias = db.session.query(
            Categoria.id,
            Categoria.nome,
            Categoria.cor,
            func.sum(Transacao.valor).label('total')
        ).join(
            Transacao, Transacao.categoria_id == Categoria.id
        ).filter(
            Transacao.user_id == user_id,
            Transacao.tipo == tipo,
            Transacao.data_transacao >= inicio_mes,
            Transacao.data_transacao <= fim_mes
        ).group_by(
            Categoria.id
        ).order_by(
            func.sum(Transacao.valor).desc()
        ).all()
        
        # Calcula o total geral
        total_geral = sum(float(c.total) for c in categorias)
        
        # Formata os dados para retorno
        resultado = []
        for c in categorias:
            porcentagem = 0 if total_geral == 0 else (float(c.total) / total_geral * 100)
            resultado.append({
                'id': c.id,
                'categoria': c.nome,
                'cor': c.cor,
                'total': float(c.total),
                'porcentagem': porcentagem
            })
        
        return resultado
    
    @staticmethod
    def obter_relatorio_tags(user_id, data_inicio=None, data_fim=None):
        """
        Obtém um relatório de gastos por tag
        
        Parâmetros:
        - user_id: ID do usuário
        - data_inicio: Data inicial para filtro (padrão: início do mês atual)
        - data_fim: Data final para filtro (padrão: fim do mês atual)
        
        Retorna uma lista de dicionários com:
        - tag: Nome da tag
        - cor: Cor da tag
        - total: Valor total
        - transacoes: Número de transações com a tag
        """
        hoje = datetime.utcnow().date()
        
        # Define o período de análise
        if data_inicio is None:
            data_inicio = date(hoje.year, hoje.month, 1)
        if data_fim is None:
            data_fim = date(hoje.year, hoje.month, monthrange(hoje.year, hoje.month)[1])
        
        # Converte para datetime se necessário
        if isinstance(data_inicio, date):
            data_inicio = datetime.combine(data_inicio, datetime.min.time())
        if isinstance(data_fim, date):
            data_fim = datetime.combine(data_fim, datetime.max.time())
        
        # Consulta para obter totais por tag
        tags = db.session.query(
            Tag.id,
            Tag.nome,
            Tag.cor,
            func.sum(Transacao.valor).label('total'),
            func.count(Transacao.id).label('transacoes')
        ).join(
            Tag.transacoes
        ).filter(
            Tag.user_id == user_id,
            Transacao.data_transacao >= data_inicio,
            Transacao.data_transacao <= data_fim
        ).group_by(
            Tag.id
        ).order_by(
            func.sum(Transacao.valor).desc()
        ).all()
        
        # Formata os dados para retorno
        resultado = []
        for t in tags:
            resultado.append({
                'id': t.id,
                'tag': t.nome,
                'cor': t.cor,
                'total': float(t.total),
                'transacoes': int(t.transacoes)
            })
        
        return resultado
