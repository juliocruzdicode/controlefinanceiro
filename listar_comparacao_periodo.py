"""
Script de comparação: recria a lógica de `relatorios()` para um período e usuário
- Gera projeções (chamando gerar_transacoes_pendentes)
- Deduplica (prioriza transações reais)
- Calcula totais por mês e matriz categoria x mês

Uso:
    python3 listar_comparacao_periodo.py --start 2026-01-01 --end 2027-12-31 --user 1

Se nenhum argumento for passado, usa período 2026-01-01 .. 2027-12-31 e user 1.
"""
import argparse
import importlib.util
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Carregar app.py diretamente (evita conflito com pacote app/)
APP_PY = Path(__file__).resolve().parents[0] / 'app.py'
spec = importlib.util.spec_from_file_location('main_app', str(APP_PY))
main_app = importlib.util.module_from_spec(spec)
sys.modules['main_app'] = main_app
spec.loader.exec_module(main_app)
app = getattr(main_app, 'app')

from models import Transacao, TransacaoRecorrente, Categoria, TipoTransacao
from dateutil.relativedelta import relativedelta

parser = argparse.ArgumentParser()
parser.add_argument('--start', default='2026-01-01')
parser.add_argument('--end', default='2027-12-31')
parser.add_argument('--user', default=1, type=int)
args = parser.parse_args()

start_dt = datetime.strptime(args.start, '%Y-%m-%d')
end_dt = datetime.strptime(args.end, '%Y-%m-%d')
user_id = args.user

with app.app_context():
    print(f"Comparação para user_id={user_id} período {start_dt.date()} -> {end_dt.date()}")

    # Real: buscar transações reais do usuário no período
    reais = Transacao.query.filter(
        Transacao.user_id == user_id,
        Transacao.data_transacao >= start_dt,
        Transacao.data_transacao <= end_dt
    ).all()

    print(f"Transações reais encontradas: {len(reais)}")

    # Gerar projeções para recorrentes ativas do usuário
    recorrentes = TransacaoRecorrente.query.filter_by(user_id=user_id, status=None).all()
    # NOTE: se StatusRecorrencia usado, ajustar; como fallback, buscamos todas e filtramos manualmente
    if not recorrentes:
        try:
            from models import StatusRecorrencia
            recorrentes = TransacaoRecorrente.query.filter_by(user_id=user_id, status=StatusRecorrencia.ATIVA).all()
        except Exception:
            recorrentes = TransacaoRecorrente.query.filter_by(user_id=user_id).all()

    print(f"Recorrentes candidatas: {len(recorrentes)}")

    # Calcular meses_futuros: diferença entre hoje e end_dt
    agora = datetime.utcnow()
    meses_futuros = 0
    if end_dt > agora:
        meses_futuros = (end_dt.year - agora.year) * 12 + (end_dt.month - agora.month)

    projetadas = []
    for r in recorrentes:
        # ignorar se finalizada
        try:
            if hasattr(r, 'status') and r.status != None and str(r.status).lower().find('ativa') == -1:
                continue
        except Exception:
            pass
        # gerar apenas se data_fim for None ou > agora
        if not getattr(r, 'data_fim', None) or (getattr(r, 'data_fim', None) and r.data_fim > agora):
            try:
                p = r.gerar_transacoes_pendentes(meses_futuros=meses_futuros, apenas_projetar=True)
                for t in p:
                    t.is_projetada = True
                projetadas.extend(p)
            except Exception as e:
                print(f"Erro ao gerar projeções para recorrente {r.id}: {e}")

    print(f"Projeções geradas: {len(projetadas)}")

    # Deduplicar: priorizar reais sobre projetadas
    transacoes_unicas = {}
    for t in reais:
        if t.recorrencia_id:
            chave = (t.data_transacao.year, t.data_transacao.month, t.recorrencia_id)
        else:
            chave = (t.data_transacao.year, t.data_transacao.month, t.categoria_id, t.tipo)
        transacoes_unicas[chave] = t
    for p in projetadas:
        if p.recorrencia_id:
            chave = (p.data_transacao.year, p.data_transacao.month, p.recorrencia_id)
        else:
            chave = (p.data_transacao.year, p.data_transacao.month, p.categoria_id, p.tipo)
        if chave not in transacoes_unicas:
            transacoes_unicas[chave] = p

    transacoes = list(transacoes_unicas.values())
    # Filtrar para o período exato
    transacoes = [t for t in transacoes if t.data_transacao >= start_dt and t.data_transacao <= end_dt]

    # Montar meses do período
    months = []
    month_starts = []
    cur = start_dt.replace(day=1)
    while cur <= end_dt:
        month_starts.append(cur)
        months.append(cur.strftime('%b %Y'))
        # avançar um mês
        if cur.month == 12:
            cur = cur.replace(year=cur.year+1, month=1)
        else:
            cur = cur.replace(month=cur.month+1)

    # Totais por mês
    totais_mensais = []
    for ms in month_starts:
        receita = sum(t.valor for t in transacoes if t.tipo == TipoTransacao.RECEITA and t.data_transacao.year == ms.year and t.data_transacao.month == ms.month)
        despesa = sum(t.valor for t in transacoes if t.tipo == TipoTransacao.DESPESA and t.data_transacao.year == ms.year and t.data_transacao.month == ms.month)
        totais_mensais.append((ms.year, ms.month, float(receita), float(despesa)))

    print('\n==== TOTAIS CALCULADOS (por mês) ====')
    for (y,m,rec,des) in totais_mensais:
        print(f"{y}-{m:02d}: receita={rec:.2f} despesa={des:.2f}")

    # Matriz por categoria
    categorias = Categoria.query.filter_by(user_id=user_id).all()
    print('\n==== MATRIZ CATEGORIA x MÊS (valores) ====')
    for c in categorias:
        row = []
        for ms in month_starts:
            val = sum(t.valor for t in transacoes if t.categoria_id == c.id and t.data_transacao.year == ms.year and t.data_transacao.month == ms.month)
            row.append(float(val))
        if any(v != 0 for v in row):
            print(f"Categoria {c.id} - {c.nome_completo}: " + ', '.join([f"{ms.strftime('%Y-%m')}={v:.2f}" for ms,v in zip(month_starts,row)]))

    print('\n==== LISTA TRANSACOES UNICAS (para debug) ====')
    for t in sorted(transacoes, key=lambda x: (x.data_transacao, getattr(x,'id',0))):
        print(f"{t.data_transacao.date()} id={getattr(t,'id',None)} valor={t.valor} categoria={t.categoria_id} recorrencia_id={t.recorrencia_id} projetada={getattr(t,'is_projetada',False)} desc={getattr(t,'descricao',None)}")

    print('\n==== FIM DA COMPARAÇÃO ====')
