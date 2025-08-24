#!/usr/bin/env python
# filepath: /Users/juliocruzd/repo/controlefinanceiro/reset_db.py
"""
Script para resetar completamente o banco de dados.
Útil quando você precisa limpar tudo e começar novamente.
"""
import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Importa a função de reset
from utils import reset_database

# Caminho do banco de dados
DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'controle_financeiro.db')

if __name__ == "__main__":
    print("🔄 Iniciando reset do banco de dados...")
    
    # Tenta resetar o banco
    if reset_database(DB_PATH):
        print("✅ Banco de dados resetado com sucesso!")
        print("🚀 Agora você pode executar 'python app.py' para iniciar com um banco limpo.")
    else:
        print("❌ Falha ao resetar o banco de dados.")
        print("💡 Dica: Certifique-se de que nenhuma aplicação esteja usando o banco.")
        print("   Tente fechar todas as instâncias do Flask/Python e tente novamente.")