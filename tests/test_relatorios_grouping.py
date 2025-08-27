import importlib.util
import os
import sys
from datetime import date


def load_app_module():
    repo = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, repo)
    spec = importlib.util.spec_from_file_location('top_app', os.path.join(repo, 'app.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_relatorios_grouping_shows_single_row_per_description():
    mod = load_app_module()
    app = mod.app
    db = mod.db
    Usuario = mod.Usuario
    Conta = mod.Conta
    Categoria = mod.Categoria
    Transacao = mod.Transacao

    with app.app_context():
        # Reset DB
        db.drop_all()
        db.create_all()

        # Criar usuário e dados base
        u = Usuario(username='testuser', email='test@example.com')
        u.set_password('test123')
        db.session.add(u)
        db.session.commit()

        c = Conta(nome='Conta Test', user_id=u.id)
        db.session.add(c)
        cat_root = Categoria(nome='Saude', user_id=u.id)
        db.session.add(cat_root)
        db.session.commit()
        sub = Categoria(nome='Academia', user_id=u.id, parent_id=cat_root.id)
        db.session.add(sub)
        db.session.commit()

        # Duas transações com mesma descrição em meses diferentes
        t1 = Transacao(descricao='Gym Pass', valor=50.0, tipo=mod.TipoTransacao.DESPESA, data_transacao=date(2025,8,1), conta_id=c.id, categoria_id=sub.id, user_id=u.id)
        t2 = Transacao(descricao='Gym Pass', valor=50.0, tipo=mod.TipoTransacao.DESPESA, data_transacao=date(2025,9,1), conta_id=c.id, categoria_id=sub.id, user_id=u.id)
        db.session.add_all([t1, t2])
        db.session.commit()

        client = app.test_client()
        # Simular usuário logado
        with client.session_transaction() as sess:
            sess['_user_id'] = str(u.id)

        rv = client.get('/relatorios')
        assert rv.status_code == 200
        data = rv.get_data(as_text=True)

        # Deve aparecer apenas uma linha com a descrição agrupada
        assert data.count('Gym Pass') == 1
        # Categoria e subcategoria visíveis
        assert 'Saude' in data
        assert 'Academia' in data
    # Total agregado (50 + 50 = 100) deve aparecer na página
    assert 'R$ 100.00' in data
    # Devem existir pelo menos duas células R$ 50.00 (um por mês)
    assert data.count('R$ 50.00') >= 2
