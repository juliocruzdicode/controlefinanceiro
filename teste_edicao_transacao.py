#!/usr/bin/env python3
"""
Script para testar as funcionalidades de edição e exclusão de transações
"""

import requests
import json
from datetime import datetime, date

BASE_URL = "http://127.0.0.1:5001"

def test_get_transacoes():
    """Testa a listagem de transações"""
    print("🔍 Testando listagem de transações...")
    response = requests.get(f"{BASE_URL}/transacoes")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Listagem de transações funcionando")
        return True
    else:
        print("❌ Erro na listagem de transações")
        print(response.text)
        return False

def test_get_editar_transacao():
    """Testa se a página de edição de transação está acessível"""
    print("\n🔍 Testando página de edição de transação (ID 1)...")
    response = requests.get(f"{BASE_URL}/editar_transacao/1")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Página de edição acessível")
        return True
    elif response.status_code == 404:
        print("⚠️ Transação não encontrada (pode estar vazia)")
        return None
    else:
        print("❌ Erro ao acessar página de edição")
        print(response.text)
        return False

def test_delete_api():
    """Testa a API de exclusão de transação"""
    print("\n🔍 Testando API de exclusão (método verificação)...")
    # Primeiro vamos ver se a API responde (mesmo que seja 404)
    response = requests.delete(f"{BASE_URL}/api/transacao/999")  # ID que não existe
    print(f"Status para ID inexistente: {response.status_code}")
    
    if response.status_code == 404:
        try:
            data = response.json()
            print(f"Resposta JSON: {data}")
            if 'message' in data:
                print("✅ API de exclusão respondendo corretamente")
                return True
        except json.JSONDecodeError:
            print("❌ API não retorna JSON válido")
            return False
    elif response.status_code == 405:
        print("❌ Método DELETE não permitido")
        return False
    else:
        print(f"❌ Resposta inesperada: {response.status_code}")
        return False

def test_dashboard():
    """Testa se o dashboard está funcionando"""
    print("\n🔍 Testando dashboard...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Dashboard funcionando")
        return True
    else:
        print("❌ Erro no dashboard")
        return False

def main():
    print("🚀 Iniciando testes das funcionalidades de edição/exclusão\n")
    
    tests = [
        ("Dashboard", test_dashboard),
        ("Listagem de Transações", test_get_transacoes),
        ("Página de Edição", test_get_editar_transacao),
        ("API de Exclusão", test_delete_api),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except requests.exceptions.ConnectionError:
            print(f"❌ Erro de conexão ao testar {test_name}")
            print("Verifique se a aplicação está rodando em http://127.0.0.1:5001")
            results[test_name] = False
            break
        except Exception as e:
            print(f"❌ Erro inesperado em {test_name}: {e}")
            results[test_name] = False
    
    print("\n" + "="*50)
    print("📊 RESUMO DOS TESTES")
    print("="*50)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASSOU"
        elif result is False:
            status = "❌ FALHOU"
        else:
            status = "⚠️  AVISO"
        print(f"{test_name:<25} {status}")
    
    passed = sum(1 for r in results.values() if r is True)
    total = len(results)
    print(f"\nResultado: {passed}/{total} testes passaram")

if __name__ == "__main__":
    main()
