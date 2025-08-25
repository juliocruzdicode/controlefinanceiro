"""Script para baixar a lista completa de municípios do Brasil e gerar data/cidades.json

Uso:
    # ativar venv do projeto
    ./.venv/bin/python scripts/update_cidades.py

O script tenta usar 'requests' e cai para urllib se não estiver instalado.
Fonte: API do IBGE - https://servicodados.ibge.gov.br/api/v1/localidades/municipios
"""

import json
import sys

IBGE_URL = 'https://servicodados.ibge.gov.br/api/v1/localidades/municipios'
OUT_PATH = 'data/cidades.json'


def fetch_with_requests(url):
    import requests
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch_with_urllib(url):
    from urllib.request import urlopen
    import ssl
    ctx = ssl.create_default_context()
    with urlopen(url, context=ctx, timeout=30) as resp:
        data = resp.read()
        return json.loads(data.decode('utf-8'))


def main():
    print('Baixando lista de municípios do IBGE...')
    try:
        try:
            data = fetch_with_requests(IBGE_URL)
        except Exception:
            data = fetch_with_urllib(IBGE_URL)
    except Exception as e:
        print('Erro ao baixar dados do IBGE:', e)
        sys.exit(1)

    cidades = []
    for item in data:
        nome = item.get('nome')
        uf = None
        # Estrutura: item['microrregiao']['mesorregiao']['UF']['sigla'] ou item['municipio']['microrregiao']...
        # Na resposta do endpoint /municipios cada item tem 'microrregiao' -> 'mesorregiao' -> 'UF'
        try:
            uf = item.get('microrregiao', {}).get('mesorregiao', {}).get('UF', {}).get('sigla')
        except Exception:
            uf = None
        if not uf:
            # tentar estrutura alternativa
            try:
                uf = item.get('municipio', {}).get('uf', {}).get('sigla')
            except Exception:
                uf = None
        if uf:
            cidades.append(f"{nome} - {uf}")
        else:
            cidades.append(nome)

    # Ordenar e remover duplicatas
    cidades = sorted(list(dict.fromkeys(cidades)))

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(cidades, f, ensure_ascii=False, indent=2)

    print(f'Gerado {OUT_PATH} com {len(cidades)} cidades.')


if __name__ == '__main__':
    main()
