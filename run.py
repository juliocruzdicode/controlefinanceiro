#!/usr/bin/env python3
"""
Script de inicialização do sistema de controle financeiro
"""
import sys
import os

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("🚀 Iniciando Sistema de Controle Financeiro...")
    print("📊 Acesse: http://localhost:5001")
    print("🔧 Modo de desenvolvimento ativado")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5001)
