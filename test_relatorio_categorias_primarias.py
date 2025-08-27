#!/usr/bin/env python3
"""
Teste que valida a agregação por categorias primárias (raiz) no relatório
"""
from datetime import datetime

from app import app
from models import db, Usuario, Categoria, Transacao, TipoTransacao


def test_aggregacao_por_categoria_raiz():
    with app.app_context():
        # Criar usuário de teste
        usuario = Usuario(username=f'test_user_rel_{int(datetime.utcnow().timestamp())}', email=None)
        db.session.add(usuario)
        db.session.commit()

        try:
            # Criar hierarquia de categorias: Raiz -> Filha -> Neta
            raiz = Categoria(nome='RaizTeste', user_id=usuario.id)
            db.session.add(raiz)
            db.session.commit()

            filha = Categoria(nome='FilhaTeste', user_id=usuario.id, parent_id=raiz.id)
            db.session.add(filha)
            db.session.commit()

            neta = Categoria(nome='NetaTeste', user_id=usuario.id, parent_id=filha.id)
            db.session.add(neta)
            db.session.commit()

            # Criar transações em cada nível
            t1 = Transacao(descricao='t_raiz', valor=10.0, tipo=TipoTransacao.DESPESA, data_transacao=datetime.utcnow(), categoria_id=raiz.id, conta_id=None, user_id=usuario.id)
            t2 = Transacao(descricao='t_filha', valor=20.0, tipo=TipoTransacao.DESPESA, data_transacao=datetime.utcnow(), categoria_id=filha.id, conta_id=None, user_id=usuario.id)
            t3 = Transacao(descricao='t_neta', valor=30.0, tipo=TipoTransacao.DESPESA, data_transacao=datetime.utcnow(), categoria_id=neta.id, conta_id=None, user_id=usuario.id)

            db.session.add_all([t1, t2, t3])
            db.session.commit()

            # Lógica de agregação por raiz (mesma ideia usada no relatório)
            categorias_raiz = Categoria.query.filter_by(parent_id=None, user_id=usuario.id).all()
            assert len(categorias_raiz) >= 1, 'Deve existir pelo menos uma categoria raiz para o usuário de teste'

            encontrado = False
            for cat_raiz in categorias_raiz:
                descendentes = cat_raiz.get_all_subcategorias(include_self=True)
                ids = {c.id for c in descendentes}

                total_despesa = db.session.query(db.func.coalesce(db.func.sum(Transacao.valor), 0)).filter(
                    Transacao.categoria_id.in_(ids),
                    Transacao.user_id == usuario.id,
                    Transacao.tipo == TipoTransacao.DESPESA
                ).scalar()

                if cat_raiz.id == raiz.id:
                    encontrado = True
                    # Esperamos soma 10 + 20 + 30 = 60
                    assert float(total_despesa) == 60.0, f'Soma agregada esperada 60.0, obtida {total_despesa}'

            assert encontrado, 'Categoria raiz criada não encontrada na query de categorias_raiz'

            print('✅ Teste de agregação por categoria raiz passou (60.0 = 10 + 20 + 30)')

        finally:
            # Limpeza dos dados criados
            try:
                Transacao.query.filter(Transacao.user_id == usuario.id).delete()
                Categoria.query.filter(Categoria.user_id == usuario.id).delete()
                Usuario.query.filter(Usuario.id == usuario.id).delete()
                db.session.commit()
            except Exception:
                db.session.rollback()


if __name__ == '__main__':
    test_aggregacao_por_categoria_raiz()
