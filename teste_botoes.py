#!/usr/bin/env python3
"""
Teste rápido para verificar se os botões de exclusão aparecem
"""

import requests
from bs4 import BeautifulSoup

def test_buttons_visibility():
    """Testa se os botões de ação aparecem na página de transações"""
    print("🔍 Verificando visibilidade dos botões na página de transações...")
    
    try:
        response = requests.get("http://127.0.0.1:5001/transacoes")
        
        if response.status_code != 200:
            print(f"❌ Erro ao acessar página: {response.status_code}")
            return False
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Procurar por botões de editar
        edit_buttons = soup.find_all('a', {'class': 'btn btn-outline-primary'})
        print(f"🔍 Botões de editar encontrados: {len(edit_buttons)}")
        
        # Procurar por botões de excluir
        delete_buttons = soup.find_all('button', {'class': 'btn btn-outline-danger'})
        print(f"🔍 Botões de excluir encontrados: {len(delete_buttons)}")
        
        # Procurar por função JavaScript
        if 'excluirTransacao' in response.text:
            print("✅ Função JavaScript excluirTransacao encontrada")
        else:
            print("❌ Função JavaScript excluirTransacao NÃO encontrada")
            
        # Procurar por tabela de transações
        table = soup.find('table', {'class': 'table'})
        if table:
            rows = table.find_all('tr')[1:]  # Pular cabeçalho
            print(f"🔍 Linhas de transação na tabela: {len(rows)}")
            
            if len(rows) > 0:
                print("✅ Há transações na lista")
                
                # Verificar se há coluna de ações
                header_row = table.find('tr')
                if header_row and 'Ações' in header_row.get_text():
                    print("✅ Coluna 'Ações' encontrada no cabeçalho")
                else:
                    print("❌ Coluna 'Ações' NÃO encontrada no cabeçalho")
                    
            else:
                print("⚠️ Não há transações na lista")
        else:
            print("❌ Tabela de transações NÃO encontrada")
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão - verifique se a aplicação está rodando")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Teste de Visibilidade dos Botões")
    print("=" * 40)
    test_buttons_visibility()
