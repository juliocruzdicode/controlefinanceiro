#!/usr/bin/env python3
"""
Script para testar as rotas e identificar erros
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def testar_rotas():
    """Testa as rotas básicas para identificar erros"""
    try:
        from app import app
        from models import db, TransacaoRecorrente, Categoria
        
        with app.test_client() as client:
            with app.app_context():
                # Teste 1: Verificar se existem transações recorrentes
                recorrentes = TransacaoRecorrente.query.all()
                print(f"✅ {len(recorrentes)} transações recorrentes encontradas")
                
                # Teste 2: Testar rota de transações recorrentes
                response = client.get('/transacoes-recorrentes')
                print(f"✅ Rota /transacoes-recorrentes: Status {response.status_code}")
                if response.status_code != 200:
                    print(f"❌ Erro: {response.data.decode()}")
                
                # Teste 3: Testar rota de nova transação
                response = client.get('/nova-transacao')
                print(f"✅ Rota /nova-transacao: Status {response.status_code}")
                if response.status_code != 200:
                    print(f"❌ Erro: {response.data.decode()}")
                
                # Teste 4: Verificar se categorias existem
                categorias = Categoria.query.all()
                print(f"✅ {len(categorias)} categorias encontradas")
                
                return True
                
    except Exception as e:
        print(f"❌ Erro durante teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    testar_rotas()
