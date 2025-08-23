#!/bin/bash

echo "🚀 Testando funcionalidades de edição e exclusão de transações"
echo "============================================================="

# Função para testar uma URL
test_url() {
    local url=$1
    local description=$2
    
    echo "🔍 Testando: $description"
    
    response=$(curl -s -w "%{http_code}" -o /tmp/response.html "$url" 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        echo "✅ Sucesso: $description"
        return 0
    elif [ "$response" = "404" ]; then
        echo "⚠️  Não encontrado: $description (pode ser normal se não há dados)"
        return 1
    else
        echo "❌ Erro ($response): $description"
        return 2
    fi
}

# Iniciar aplicação se não estiver rodando
echo "📡 Verificando se a aplicação está rodando..."
if ! curl -s http://127.0.0.1:5001/ > /dev/null 2>&1; then
    echo "🚀 Iniciando aplicação Flask..."
    nohup python app.py > app.log 2>&1 &
    sleep 3  # Aguardar a aplicação iniciar
fi

echo ""
echo "🧪 Iniciando testes..."
echo "----------------------"

# Testes
test_url "http://127.0.0.1:5001/" "Dashboard"
test_url "http://127.0.0.1:5001/transacoes" "Lista de Transações"
test_url "http://127.0.0.1:5001/editar_transacao/1" "Edição de Transação (ID 1)"
test_url "http://127.0.0.1:5001/nova_transacao" "Nova Transação"

# Teste da API DELETE
echo ""
echo "🔍 Testando API de exclusão..."
delete_response=$(curl -s -w "%{http_code}" -X DELETE "http://127.0.0.1:5001/api/transacao/999" 2>/dev/null)

if [ "$delete_response" = "404" ] || [ "$delete_response" = "200" ]; then
    echo "✅ API DELETE funcionando (retornou $delete_response)"
else
    echo "❌ Problema na API DELETE (retornou $delete_response)"
fi

echo ""
echo "📊 Teste concluído!"
echo "Verifique o navegador em: http://127.0.0.1:5001/"
