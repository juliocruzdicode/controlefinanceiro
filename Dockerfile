FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY . .

# Criar diretório para arquivos estáticos se necessário
RUN mkdir -p instance

# Definir variáveis de ambiente
ENV FLASK_APP=app.py
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expor a porta
EXPOSE 5000

# Criar um usuário não-root para rodar a aplicação
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Script de inicialização para aguardar o banco e executar migrações
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
USER root
RUN chmod +x /app/docker-entrypoint.sh
USER app

# Comando para iniciar a aplicação
CMD ["/app/docker-entrypoint.sh"]
