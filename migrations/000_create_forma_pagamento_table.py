"""
Create table forma_pagamento and add forma_pagamento_id foreign keys to transacao and transacao_recorrente.
Run inside application context similar to run_add_forma_pagamento.py
"""
from sqlalchemy import MetaData, Table, text
from models import db


def upgrade():
    engine = getattr(db, 'engine', None)
    if engine is None:
        try:
            engine = db.get_engine()
        except Exception:
            raise RuntimeError('Could not obtain engine')

    meta = MetaData()
    meta.reflect(bind=engine)

    # Create table if not exists (simple SQL)
    if 'forma_pagamento' not in meta.tables:
        sql = text('''CREATE TABLE forma_pagamento (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            slug VARCHAR(100) NOT NULL UNIQUE,
            user_id INTEGER REFERENCES usuario(id),
            ativa BOOLEAN DEFAULT TRUE,
            criado_em TIMESTAMP DEFAULT now()
        );''')
        with engine.connect() as conn:
            conn.execute(sql)
        print('Created table forma_pagamento')

    # Refresh metadata
    meta = MetaData()
    meta.reflect(bind=engine)

    # Add columns to transacao
    if 'transacao' in meta.tables:
        trans = meta.tables['transacao']
        if 'forma_pagamento_id' not in trans.c:
            sql = text('ALTER TABLE transacao ADD COLUMN forma_pagamento_id INTEGER REFERENCES forma_pagamento(id);')
            with engine.connect() as conn:
                conn.execute(sql)
            print('Added forma_pagamento_id to transacao')

    # Add columns to transacao_recorrente
    if 'transacao_recorrente' in meta.tables:
        rec = meta.tables['transacao_recorrente']
        if 'forma_pagamento_id' not in rec.c:
            sql = text('ALTER TABLE transacao_recorrente ADD COLUMN forma_pagamento_id INTEGER REFERENCES forma_pagamento(id);')
            with engine.connect() as conn:
                conn.execute(sql)
            print('Added forma_pagamento_id to transacao_recorrente')


if __name__ == '__main__':
    print('Run inside app context')
