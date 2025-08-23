# Controle Financeiro com Traefik

## Configuração para Produção

Este projeto agora está configurado para funcionar com Traefik como proxy reverso. O Traefik gerencia automaticamente os certificados SSL e o roteamento para a aplicação.

### Pré-requisitos

1. Docker e Docker Compose instalados
2. Domínio configurado para apontar para o servidor onde a aplicação será executada
3. Rede Docker `app-network` criada

### Criar a rede Docker

Antes de iniciar os serviços, crie a rede Docker externa:

```bash
docker network create app-network
```

### Configuração do Traefik

O Traefik é configurado em um arquivo separado: `docker-compose-traefik-prod.yaml`. Você deve iniciar o Traefik antes de iniciar a aplicação:

```bash
docker-compose -f docker-compose-traefik-prod.yaml up -d
```

### Iniciando a Aplicação

Para iniciar a aplicação em produção:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

A aplicação estará disponível em: https://financeiro.bioneo.com.br

## Configuração para Desenvolvimento

Para desenvolvimento local, você pode usar o docker-compose padrão que irá ignorar as configurações do Traefik:

```bash
docker-compose up -d
```

Ou, se quiser testar com Traefik localmente:

```bash
docker-compose --profile traefik-dev up -d
```

Para desenvolvimento local, a aplicação estará disponível em: http://localhost:3000

## Alterando a Configuração

### Mudando o Domínio

Para alterar o domínio da aplicação, edite a label do Traefik no arquivo `docker-compose.prod.yml`:

```yaml
labels:
  - "traefik.http.routers.financeiro.rule=Host(`seu-novo-dominio.com`)"
```

### Configurações SSL

Os certificados SSL são gerenciados automaticamente pelo Traefik via Let's Encrypt. Para alterar o email usado para os certificados, edite o arquivo `docker-compose-traefik-prod.yaml`:

```yaml
- "--certificatesresolvers.myresolver.acme.email=seu-email@exemplo.com"
```
