#!/bin/bash

echo "🚀 Configuração do Sistema de Controle Financeiro"
echo "================================================="

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale o Python 3.8+ primeiro."
    exit 1
fi

# Criar ambiente virtual se não existir
if [ ! -d ".venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv .venv
fi

# Ativar ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source .venv/bin/activate

# Instalar dependências essenciais
echo "📥 Instalando dependências essenciais..."
pip install --upgrade pip

# Tentar instalar dependências completas primeiro
echo "📊 Tentando instalar dependências completas..."
if pip install -r requirements.txt; then
    echo "✅ Todas as dependências instaladas com sucesso!"
else
    echo "⚠️  Erro nas dependências completas. Instalando versão mínima..."
    pip install -r requirements-minimal.txt
    echo "✅ Dependências mínimas instaladas!"
    echo "ℹ️  Algumas funcionalidades de análise estarão limitadas."
fi

echo ""
echo "🎉 Configuração concluída!"
echo "Para executar a aplicação:"
echo "  source .venv/bin/activate"
echo "  python run.py"
echo ""
echo "Acesse: http://localhost:5001"
