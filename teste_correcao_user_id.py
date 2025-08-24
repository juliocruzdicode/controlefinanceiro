#!/usr/bin/env python3
"""
Teste rápido para verificar se a correção do user_id foi aplicada
"""
import sys
import os
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, TransacaoRecorrente, TipoRecorrencia, StatusRecorrencia, TipoTransacao

def inspecionar_metodo():
    """Inspeciona o método gerar_proxima_transacao da classe TransacaoRecorrente"""
    with app.app_context():
        # Obter o código fonte do método
        codigo = TransacaoRecorrente.gerar_proxima_transacao.__code__
        
        # Verificar as variáveis locais
        print("📝 Variáveis locais do método:")
        for var in codigo.co_varnames:
            print(f"  - {var}")
        
        # Verificar o código fonte
        import inspect
        codigo_fonte = inspect.getsource(TransacaoRecorrente.gerar_proxima_transacao)
        
        print("\n📝 Código fonte do método:")
        for linha in codigo_fonte.split('\n'):
            print(f"  {linha}")
        
        # Verificar se há referências a user_id
        if "user_id" in codigo_fonte:
            print("\n✅ O código contém referências a user_id!")
            for i, linha in enumerate(codigo_fonte.split('\n')):
                if "user_id" in linha:
                    print(f"  Linha {i+1}: {linha.strip()}")
        else:
            print("\n❌ O código não contém referências a user_id!")

if __name__ == '__main__':
    inspecionar_metodo()
