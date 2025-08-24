import importlib.util
import sys
from pathlib import Path
from datetime import datetime

# Carrega o módulo app.py diretamente (evita conflito com pacote app/)
APP_PY = Path(__file__).resolve().parents[0] / 'app.py'
spec = importlib.util.spec_from_file_location('main_app', str(APP_PY))
main_app = importlib.util.module_from_spec(spec)
sys.modules['main_app'] = main_app
spec.loader.exec_module(main_app)
app = getattr(main_app, 'app')

from models import Transacao

def listar_transacoes_agosto_2025():
    with app.app_context():
        transacoes = Transacao.query.filter(
            Transacao.data_transacao >= datetime(2025, 8, 1),
            Transacao.data_transacao < datetime(2025, 9, 1)
        ).all()
        print("==== TRANSACOES AGOSTO 2025 ====")
        for t in transacoes:
            print(f"ID={t.id} valor={t.valor} recorrencia_id={t.recorrencia_id} tipo={t.tipo} categoria_id={t.categoria_id} data={t.data_transacao} descricao={getattr(t, 'descricao', '')}")
        print(f"Total: {len(transacoes)} transações")


if __name__ == "__main__":
    listar_transacoes_agosto_2025()
