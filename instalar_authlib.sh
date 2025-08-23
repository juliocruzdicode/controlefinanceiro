#!/bin/bash

# Verificar se estamos no diretório correto
if [ ! -f "requirements.txt" ]; then
  echo "Erro: Este script deve ser executado na raiz do projeto."
  exit 1
fi

# Instalar a biblioteca authlib diretamente no container em execução
echo "Instalando Authlib no container em execução..."
docker exec -it controle_financeiro_app pip install Authlib>=1.2.0

echo "A biblioteca Authlib foi instalada no container."
echo "Para uma solução permanente, o requirements.txt foi atualizado."
echo ""
echo "Quando quiser reconstruir a imagem com a Authlib incluída permanentemente, execute:"
echo "docker compose -f docker-compose.prod.yml down"
echo "docker compose -f docker-compose.prod.yml up -d --build"
