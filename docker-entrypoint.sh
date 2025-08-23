#!/bin/bash
set -e

echo "Aguardando PostgreSQL iniciar..."

# Função para testar a conexão com PostgreSQL
until python3 -c "
import psycopg2
import os
import sys
try:
    conn = psycopg2.connect(
        host=os.environ.get('POSTGRES_HOST', 'postgres'),
        database=os.environ.get('POSTGRES_DB', 'controle_financeiro'),
        user=os.environ.get('POSTGRES_USER', 'controle_financeiro'),
        password=os.environ.get('POSTGRES_PASSWORD', 'senha_segura_aqui'),
        port=os.environ.get('POSTGRES_PORT', '5432')
    )
    conn.close()
    print('PostgreSQL está pronto!')
except psycopg2.OperationalError as e:
    print(f'PostgreSQL não está pronto ainda: {e}')
    sys.exit(1)
"; do
  echo "PostgreSQL não está pronto ainda. Aguardando..."
  sleep 2
done

echo "PostgreSQL está pronto!"

# Executar migrações/criação de tabelas se necessário
echo "Verificando e criando tabelas..."
python3 -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Tabelas criadas/verificadas com sucesso!')
"

echo "Iniciando aplicação..."

# Iniciar a aplicação com Gunicorn em produção
if [ "$DEBUG" = "true" ] || [ "$DEBUG" = "True" ]; then
    echo "Modo desenvolvimento - usando Flask dev server"
    exec python3 app.py
else
    echo "Modo produção - usando Gunicorn"
    exec gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 app:app
fi
