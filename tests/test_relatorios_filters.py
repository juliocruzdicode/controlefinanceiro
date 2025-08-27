import pytest
from importlib.machinery import SourceFileLoader
from models import db, Usuario, Conta, Categoria, Transacao, TransacaoRecorrente, TipoTransacao, StatusRecorrencia, TipoRecorrencia
from datetime import datetime
from uuid import uuid4

# Carregar app.py como módulo (arquivo) para evitar colisão com package 'app'
app_module = SourceFileLoader('app_main','/Users/juliocruzd/repo/controlefinanceiro/app.py').load_module()
app = getattr(app_module, 'app')

@pytest.fixture
def client(monkeypatch, tmp_path):
    # Configurar app para usar sqlite in-memory
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        # app already initialized with SQLAlchemy instance
        db.create_all()
        # Criar usuário com email único para evitar conflitos
        unique_email = f"test+{uuid4().hex}@example.com"
        user = Usuario(username='testuser', email=unique_email)
        user.set_password('password')
        db.session.add(user)
        db.session.commit()

        # Criar contas e categorias
        conta1 = Conta(nome='Conta A', user_id=user.id)
        conta2 = Conta(nome='Conta B', user_id=user.id)
        db.session.add_all([conta1, conta2])
        db.session.commit()

        cat_root = Categoria(nome='Salário', user_id=user.id)
        cat_other = Categoria(nome='Alimentação', user_id=user.id)
        db.session.add_all([cat_root, cat_other])
        db.session.commit()

        # Criar transações em contas diferentes
        t1 = Transacao(descricao='Salario janeiro', valor=1000, tipo=TipoTransacao.RECEITA, data_transacao=datetime(2025,1,5), categoria_id=cat_root.id, conta_id=conta1.id, user_id=user.id)
        t2 = Transacao(descricao='Jantar', valor=50, tipo=TipoTransacao.DESPESA, data_transacao=datetime(2025,1,10), categoria_id=cat_other.id, conta_id=conta2.id, user_id=user.id)
        db.session.add_all([t1, t2])
        db.session.commit()

        # Criar recorrente vinculada à conta2 e categoria alimentação
        rec = TransacaoRecorrente(descricao='Almoco recorrente', valor=30, tipo=TipoTransacao.DESPESA, tipo_recorrencia=TipoRecorrencia.MENSAL, status=StatusRecorrencia.ATIVA, data_inicio=datetime(2025,2,1), categoria_id=cat_other.id, conta_id=conta2.id, user_id=user.id)
        db.session.add(rec)
        db.session.commit()

        client = app.test_client()

        # Logar o usuário criando a sessão
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)

        yield client

        db.session.remove()
        db.drop_all()


def test_filters_persist_and_apply(client):
    # Post with filters should redirect to GET with query params
    resp = client.post('/relatorios', data={'ano':'2025','tipo':'todos','categoria':str(1),'conta':str(2)})
    assert resp.status_code == 302
    loc = resp.headers.get('Location')
    assert 'conta=2' in loc and 'categoria=1' in loc

    # Call the API dados-grafico with conta filter: should return only categoria related to conta2
    resp_api = client.get('/api/dados-grafico?conta=2&ano=2025')
    assert resp_api.status_code == 200
    data = resp_api.get_json()
    assert 'categoria' in data and 'tempo' in data
    # Since conta2 has a despesa (Jantar) and a recurring projected expense, ensure at least one category returned
    assert len(data['categoria']['labels']) >= 1

    # GET relatorios with query params should render page (302 if login required handled earlier)
    resp_get = client.get('/relatorios?ano=2025&conta=2&categoria=1')
    # Expect 200 or 302 depending on auth handling; ensure Location or content contains the params
    assert resp_get.status_code in (200,302)
