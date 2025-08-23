#!/bin/bash

# Criar um backup do arquivo original
echo "Fazendo backup do docker-compose.prod.yml..."
cp docker-compose.prod.yml docker-compose.prod.yml.bak

# Adicionar volume para o arquivo .env
echo "Adicionando volume para o arquivo .env..."
sed -i '' 's/      - app_data:\/app\/instance/      - app_data:\/app\/instance\n      - .\/\.env:\/app\/\.env:ro/g' docker-compose.prod.yml

echo "Pronto! Arquivo docker-compose.prod.yml atualizado."
echo "Agora execute:"
echo "git commit -am 'Adicionado volume para .env'"
echo "git push"
echo "E no servidor:"
echo "cd ~/.ssh/controle-financeiro/bin/controlefinanceiro"
echo "git pull"
echo "docker compose -f docker-compose.prod.yml down"
echo "docker compose -f docker-compose.prod.yml up -d --build"
