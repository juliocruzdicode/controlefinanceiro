"""
Teste rápido e simples para verificar se a correção no models.py foi aplicada
"""
import inspect
from models import TransacaoRecorrente

# Obter o código fonte do método
codigo = inspect.getsource(TransacaoRecorrente.gerar_proxima_transacao)

# Verificar se há referências a user_id
if "user_id=self.user_id" in codigo:
    print("\n✅ A correção foi aplicada! O método gerar_proxima_transacao agora inclui user_id!")
    for i, linha in enumerate(codigo.split('\n')):
        if "user_id=self.user_id" in linha:
            print(f"  Linha encontrada: {linha.strip()}")
else:
    print("\n❌ A correção NÃO foi aplicada. O método não contém a atribuição de user_id!")
