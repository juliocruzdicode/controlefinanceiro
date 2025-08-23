#!/usr/bin/env python3
"""
Teste rápido para verificar se o erro de validação foi corrigido
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def testar_formulario():
    """Testa se o formulário está funcionando sem erro"""
    try:
        from app import app
        from forms import TransacaoForm
        
        with app.test_client() as client:
            with app.app_context():
                # Simular um POST para testar a validação
                data = {
                    'descricao': 'Teste',
                    'valor': 100.00,
                    'tipo': 'receita',
                    'categoria_id': 1,
                    'data_transacao': '2024-01-15',
                    'is_recorrente': True,
                    'tipo_recorrencia': 'mensal',
                    'is_parcelada': False
                }
                
                response = client.post('/nova-transacao', data=data, follow_redirects=True)
                
                if response.status_code == 200:
                    print("✅ Formulário funcionando sem erros!")
                    return True
                else:
                    print(f"❌ Erro no formulário: Status {response.status_code}")
                    print(response.data.decode()[:500] + "...")
                    return False
                    
    except Exception as e:
        print(f"❌ Erro durante teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    testar_formulario()
