# Controle Financeiro

Sistema completo de controle financeiro desenvolvido em Python com Flask.

## 🎯 Funcionalidades

- ✅ **Dashboard interativo** com resumo das finanças
- ✅ **Controle de receitas e despesas** com categorização
- ✅ **Sistema de categorias hierárquico infinito** - organize suas categorias em níveis
- ✅ **Relatórios visuais** com gráficos dinâmicos
- ✅ **Categorias personalizáveis** com cores
- ✅ **Interface responsiva** para desktop e mobile
- ✅ **Análise de dados** com pandas e matplotlib

### 🏷️ Sistema de Categorias Hierárquico

Organize suas transações com estrutura infinita de categorias e subcategorias:

```
📁 Alimentação
  ├── 🍽️ Restaurantes
  │   ├── 🍔 Fast Food
  │   ├── 🍣 Comida Japonesa
  │   └── 🍕 Pizzaria
  ├── 🛒 Supermercado
  └── 🚚 Delivery
  
📁 Transporte  
  ├── ⛽ Combustível
  ├── 🚌 Transporte Público
  └── 🚗 Uber/Taxi
```

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python 3.8+, Flask, SQLAlchemy
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5
- **Gráficos:** Chart.js
- **Banco de Dados:** SQLite (desenvolvimento)
- **Análise de Dados:** Pandas, Matplotlib, Plotly

## 🚀 Como Executar

### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd controle-financeiro
```

### 2. Crie um ambiente virtual
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

**Se houver erro na instalação, use uma das alternativas:**

**🔧 Script automatizado:**
```bash
./setup.sh
```

**📦 Instalação individual:**
```bash
pip install Flask Flask-SQLAlchemy Flask-WTF python-dotenv
pip install pandas matplotlib plotly  # opcional - para análise avançada
```

**⚡ Instalação mínima (apenas web):**
```bash
pip install -r requirements-minimal.txt
```

### 4. Configure as variáveis de ambiente
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

### 5. Execute a aplicação
```bash
python run.py
# ou
python app.py
```

**Para recriar o banco com categorias hierárquicas:**
```bash
python migrate.py  # Recria banco com estrutura hierárquica completa
```

A aplicação estará disponível em: http://localhost:5001

## 📁 Estrutura do Projeto

```
controle-financeiro/
├── app.py                 # Aplicação Flask principal
├── run.py                 # Script de inicialização
├── config.py              # Configurações da aplicação  
├── models.py              # Modelos do banco de dados
├── forms.py               # Formulários WTForms
├── requirements.txt       # Dependências Python
├── templates/             # Templates HTML
│   ├── base.html         # Template base
│   ├── dashboard.html    # Dashboard principal
│   ├── transacoes.html   # Lista de transações
│   ├── nova_transacao.html # Formulário de transação
│   ├── categorias.html   # Lista de categorias
│   ├── nova_categoria.html # Formulário de categoria
│   └── relatorios.html   # Página de relatórios
├── static/               # Arquivos estáticos
│   └── css/
│       └── style.css     # Estilos personalizados
└── instance/             # Banco de dados (auto-gerado)
```

## 🎨 Screenshots

### Dashboard
- Visão geral das finanças
- Gráficos de receitas vs despesas
- Últimas transações

### Transações
- Lista completa de transações
- Filtros por categoria e tipo
- Adição rápida de novas transações

### Relatórios
- Gráficos detalhados por categoria
- Análise temporal de gastos
- Exportação de dados

## 🔧 Desenvolvimento

### Estrutura do código
- **Models**: Definição das tabelas do banco de dados
- **Forms**: Validação de formulários com WTForms
- **Routes**: Endpoints da API REST
- **Templates**: Interface HTML com Jinja2

### Banco de dados
O sistema usa SQLite por padrão, mas pode ser facilmente configurado para PostgreSQL ou MySQL alterando a variável `DATABASE_URL` no arquivo `.env`.

### Categorias padrão
O sistema cria automaticamente uma estrutura hierárquica completa:

**Categorias Raiz:**
- 🍽️ Alimentação → Restaurantes, Supermercado, Delivery
  - Fast Food, Comida Japonesa, Pizzaria (subcategorias de Restaurantes)
- 🚗 Transporte → Combustível, Transporte Público, Uber/Taxi  
- 🏠 Moradia → Aluguel, Contas, Manutenção
- 💰 Trabalho → Salário, Freelance, Investimentos
- 🏥 Saúde, 📚 Educação, 🎮 Lazer

**Estrutura Infinita:** Você pode criar quantos níveis quiser!

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## � Troubleshooting

### Problemas na instalação das dependências

**Erro com matplotlib/pandas:**
```bash
# Use apenas as dependências essenciais
pip install -r requirements-minimal.txt
```

**Erro "pip subprocess":**
```bash
# Atualize o pip e tente novamente
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**Porta 5000 em uso (macOS):**
- A aplicação usa a porta 5001 por padrão
- Ou desative o AirPlay Receiver: Configurações > Geral > AirDrop

### Problemas com banco de dados

**Erro SQLite:**
```bash
# Remova o banco e deixe recriar
rm instance/controle_financeiro.db
python run.py
```

### Performance

**Aplicação lenta:**
- Use SQLite apenas para desenvolvimento
- Para produção, configure PostgreSQL no `.env`

## �📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 📧 Contato

Para dúvidas ou sugestões, abra uma issue no repositório.
