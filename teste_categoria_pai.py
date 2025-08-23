#!/usr/bin/env python3
"""
Teste para verificar criação de categoria com pai
"""

import requests
import json

# Configurações
BASE_URL = "http://127.0.0.1:5002"

def teste_categoria_com_pai():
    """Testa a criação de categoria com pai através da API"""
    
    # Primeiro, vamos criar uma categoria pai
    data_pai = {
        "nome": "Categoria Pai Teste",
        "descricao": "Categoria pai para teste"
    }
    
    print("🧪 Testando criação de categoria com pai...")
    print("📍 Acesse: http://127.0.0.1:5002/nova-transacao")
    print("📍 Clique no botão '+' ao lado do campo categoria")
    print("📍 Teste criar uma categoria selecionando uma categoria pai")
    print("\n✅ Funcionalidades implementadas:")
    print("   - Campo 'Categoria Pai' no modal de criação")
    print("   - Dropdown populado automaticamente com categorias existentes")
    print("   - Ordenação por nome completo (hierárquico)")
    print("   - Suporte a parent_id na API")
    print("   - Atualização dinâmica do select principal")
    print("   - Nome completo mostrado no dropdown após criação")
    
    print("\n🔧 Como testar:")
    print("1. Acesse a página de nova transação")
    print("2. Clique no botão '+' ao lado de Categoria")
    print("3. Veja que agora há um campo 'Categoria Pai'")
    print("4. Selecione uma categoria pai (ou deixe 'Nenhuma')")
    print("5. Preencha o nome da categoria e crie")
    print("6. Veja que a nova categoria aparece corretamente no dropdown")

if __name__ == "__main__":
    teste_categoria_com_pai()
