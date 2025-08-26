"""
Simple migration helper to add forma_pagamento enum columns to Transacao and TransacaoRecorrente.
Run manually in your development environment after backing up the DB.
This script uses SQLAlchemy metadata to emit ALTER TABLE statements for SQLite/Postgres.

Note: adapt for your production DB and backup first. The project does not use Alembic here; apply carefully.
"""
from sqlalchemy import MetaData, Table, Column, Enum
from models import db, TipoFormaPagamento


def upgrade():
    # Get SQLAlchemy engine from the app-bound db instance
    engine = getattr(db, 'engine', None)
    if engine is None:
        # Fallback to get_engine() if present
        try:
            engine = db.get_engine()
        except Exception:
            raise RuntimeError('Could not obtain a SQLAlchemy engine from db')

    meta = MetaData()
    meta.reflect(bind=engine)

    # Add column to transacao
    if 'transacao' in meta.tables:
        transacao = meta.tables['transacao']
        if 'forma_pagamento' not in transacao.c:
            # Build enum values
            enum_vals = ','.join([f"'{m.value}'" for m in TipoFormaPagamento])
            engine_name = engine.dialect.name
            if engine_name == 'sqlite':
                # SQLite: ALTER TABLE ADD COLUMN with TEXT
                from sqlalchemy import text
                sql = text(f"ALTER TABLE transacao ADD COLUMN forma_pagamento TEXT")
                with engine.connect() as conn:
                    conn.execute(sql)
            else:
                # Postgres/MySQL: create enum type if needed (Postgres)
                if engine_name == 'postgresql':
                    # create type if not exists
                    sql_type = f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipoformapagamento') THEN CREATE TYPE tipoformapagamento AS ENUM ({enum_vals}); END IF; END$$;"
                    from sqlalchemy import text
                    with engine.connect() as conn:
                        conn.execute(text(sql_type))
                        sql = text(f"ALTER TABLE transacao ADD COLUMN forma_pagamento tipoformapagamento")
                        conn.execute(sql)
                else:
                    # Fallback: add as VARCHAR
                    from sqlalchemy import text
                    sql = text(f"ALTER TABLE transacao ADD COLUMN forma_pagamento VARCHAR(50)")
                    with engine.connect() as conn:
                        conn.execute(sql)
            print('Column forma_pagamento added to transacao')

    # Add column to transacao_recorrente
    if 'transacao_recorrente' in meta.tables:
        recorrente = meta.tables['transacao_recorrente']
        if 'forma_pagamento' not in recorrente.c:
            enum_vals = ','.join([f"'{m.value}'" for m in TipoFormaPagamento])
            engine_name = engine.dialect.name
            if engine_name == 'sqlite':
                from sqlalchemy import text
                sql = text(f"ALTER TABLE transacao_recorrente ADD COLUMN forma_pagamento TEXT")
                with engine.connect() as conn:
                    conn.execute(sql)
            else:
                if engine_name == 'postgresql':
                    sql_type = f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipoformapagamento') THEN CREATE TYPE tipoformapagamento AS ENUM ({enum_vals}); END IF; END$$;"
                    from sqlalchemy import text
                    with engine.connect() as conn:
                        conn.execute(text(sql_type))
                        sql = text(f"ALTER TABLE transacao_recorrente ADD COLUMN forma_pagamento tipoformapagamento")
                        conn.execute(sql)
                else:
                    from sqlalchemy import text
                    sql = text(f"ALTER TABLE transacao_recorrente ADD COLUMN forma_pagamento VARCHAR(50)")
                    with engine.connect() as conn:
                        conn.execute(sql)
            print('Column forma_pagamento added to transacao_recorrente')


if __name__ == '__main__':
    print('This is a helper script. Import and run upgrade() inside your application context to apply changes.')
