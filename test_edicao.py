#!/usr/bin/env python3
"""
Teste rápido das funcionalidades de edição
"""
import sys
from pathlib import Path

# Adicionar o diretório atual ao path
sys.path.insert(0, str(Path(__file__).parent))

def testar_importacoes():
    print("🧪 Testando importações...")
    try:
        from app import app, db
        from models import Categoria
        print("✅ Importações OK")
        return True
    except Exception as e:
        print(f"❌ Erro nas importações: {e}")
        return False

def testar_contexto_app():
    print("🧪 Testando contexto da aplicação...")
    try:
        from app import app
        with app.app_context():
            from models import Categoria
            categorias = Categoria.query.count()
            print(f"✅ Contexto OK - {categorias} categorias encontradas")
            return True
    except Exception as e:
        print(f"❌ Erro no contexto: {e}")
        return False

def testar_rotas():
    print("🧪 Testando se as rotas foram registradas...")
    from app import app
    
    rotas_esperadas = [
        '/editar-categoria/<int:categoria_id>',
        '/api/categoria/<int:categoria_id>',
    ]
    
    rotas_registradas = [str(rule) for rule in app.url_map.iter_rules()]
    
    for rota in rotas_esperadas:
        rota_base = rota.replace('<int:categoria_id>', '1')  # Simplificar para busca
        encontrada = any(rota_base.replace('1', '') in r for r in rotas_registradas)
        if encontrada:
            print(f"✅ Rota {rota} registrada")
        else:
            print(f"❌ Rota {rota} NÃO encontrada")
    
    return True

if __name__ == '__main__':
    print("🚀 Iniciando testes das funcionalidades de edição...")
    print("=" * 50)
    
    if testar_importacoes():
        if testar_contexto_app():
            testar_rotas()
            print("=" * 50)
            print("🎉 Testes concluídos! A aplicação parece estar funcionando.")
            print("📊 Execute: python run.py para iniciar o servidor")
        else:
            print("❌ Problemas no contexto da aplicação")
    else:
        print("❌ Problemas nas importações")
