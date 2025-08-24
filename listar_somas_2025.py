import importlib.util
import sys
from pathlib import Path
from datetime import datetime

# Carrega app.py diretamente para evitar conflito com package app/
APP_PY = Path(__file__).resolve().parents[0] / 'app.py'
spec = importlib.util.spec_from_file_location('main_app', str(APP_PY))
main_app = importlib.util.module_from_spec(spec)
sys.modules['main_app'] = main_app
spec.loader.exec_module(main_app)
app = getattr(main_app, 'app')

from models import Transacao, Categoria, TipoTransacao
from sqlalchemy import func

YEAR = 2025

with app.app_context():
    print(f"==== SOMAS POR MÊS - {YEAR} ====")
    meses = []
    for m in range(1, 13):
        inicio = datetime(YEAR, m, 1)
        if m == 12:
            fim = datetime(YEAR + 1, 1, 1)
        else:
            fim = datetime(YEAR, m + 1, 1)
        total_receita = Transacao.query.filter(Transacao.data_transacao >= inicio, Transacao.data_transacao < fim, Transacao.tipo == TipoTransacao.RECEITA).with_entities(func.sum(Transacao.valor)).scalar() or 0
        total_despesa = Transacao.query.filter(Transacao.data_transacao >= inicio, Transacao.data_transacao < fim, Transacao.tipo == TipoTransacao.DESPESA).with_entities(func.sum(Transacao.valor)).scalar() or 0
        print(f"{m:02d}/{YEAR}: receita={float(total_receita):.2f} despesa={float(total_despesa):.2f}")
        meses.append((m, float(total_receita), float(total_despesa)))

    print('\n==== SOMAS POR CATEGORIA (TOTAL ANUAL) ====')
    categorias = Categoria.query.all()
    for c in categorias:
        total = Transacao.query.filter(Transacao.categoria_id == c.id, func.strftime('%Y', Transacao.data_transacao) == str(YEAR)).with_entities(func.sum(Transacao.valor)).scalar() or 0
        if float(total) != 0:
            print(f"Categoria {c.id} - {c.nome_completo}: {float(total):.2f}")

    print('\n==== DETALHE POR CATEGORIA E MÊS ====')
    for c in categorias:
        rows = []
        for m in range(1, 13):
            inicio = datetime(YEAR, m, 1)
            if m == 12:
                fim = datetime(YEAR + 1, 1, 1)
            else:
                fim = datetime(YEAR, m + 1, 1)
            total = Transacao.query.filter(Transacao.categoria_id == c.id, Transacao.data_transacao >= inicio, Transacao.data_transacao < fim).with_entities(func.sum(Transacao.valor)).scalar() or 0
            rows.append(float(total))
        if any(v != 0 for v in rows):
            print(f"Categoria {c.id} - {c.nome_completo}: " + ", ".join([f"{m:02d}: {v:.2f}" for m, v in zip(range(1,13), rows)]))

    print('\n==== FIM ====')
