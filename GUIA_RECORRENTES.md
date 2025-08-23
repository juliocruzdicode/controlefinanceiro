# Guia de Transações Recorrentes 📅

## Visão Geral
O sistema agora suporta **transações recorrentes**, permitindo que você automatize suas receitas e despesas regulares. 

## Tipos de Recorrência Disponíveis

### 1. **Frequências Suportadas**
- **Semanal** - A cada 7 dias
- **Mensal** - Todo mês na mesma data
- **Trimestral** - A cada 3 meses
- **Semestral** - A cada 6 meses  
- **Anual** - Todo ano na mesma data

### 2. **Modalidades de Transação**

#### 🔄 **Transações Contínuas**
- Sem fim definido
- Geram transações indefinidamente
- Ideal para: salário, aluguel, contas fixas
- Exemplo: "Salário Mensal" que se repete todo mês

#### 📊 **Transações Parceladas**
- Número específico de parcelas
- Finalizam automaticamente após todas as parcelas
- Ideal para: financiamentos, parcelamentos
- Exemplo: "Notebook em 12x" que gera 12 parcelas mensais

## Como Usar

### 1. **Criar Nova Transação Recorrente**
1. Acesse "Recorrentes" no menu
2. Clique em "Nova Transação Recorrente"
3. Preencha os dados básicos:
   - Descrição
   - Valor
   - Tipo (Receita/Despesa)
   - Categoria
4. Configure a recorrência:
   - Escolha a frequência
   - Defina data de início
   - Opcionalmente: data de fim
5. Para parceladas: marque a opção e informe o número de parcelas

### 2. **Gerenciar Transações Recorrentes**
- **▶️ Gerar**: Cria transações pendentes manualmente
- **⏸️ Pausar**: Interrompe temporariamente a geração
- **▶️ Reativar**: Volta a gerar transações
- **⏹️ Finalizar**: Encerra definitivamente
- **✏️ Editar**: Modifica configurações

### 3. **Status das Recorrências**
- **🟢 Ativa**: Gerando transações normalmente
- **🟡 Pausada**: Temporariamente suspensa
- **🔴 Finalizada**: Não gera mais transações

## Funcionalidades Avançadas

### 1. **Geração Automática**
- O sistema gera automaticamente as transações pendentes
- Ao acessar a página, transações em atraso são criadas
- Use "Gerar Pendentes" para forçar a atualização

### 2. **Visualização de Progresso**
- Para transações parceladas: barra de progresso
- Mostra parcelas pagas vs. restantes
- Para contínuas: contador de transações geradas

### 3. **APIs Disponíveis**
- `GET /api/transacoes-recorrentes` - Listar todas
- `GET /api/transacao-recorrente/{id}/gerar` - Gerar pendentes
- `POST /api/transacao-recorrente/{id}/pausar` - Pausar/Reativar  
- `POST /api/transacao-recorrente/{id}/finalizar` - Finalizar
- `GET /api/gerar-todas-transacoes-pendentes` - Gerar todas pendentes

## Exemplos Práticos

### Exemplo 1: Salário Mensal
```
Descrição: Salário Mensal
Valor: R$ 5.000,00
Tipo: Receita
Frequência: Mensal
Data início: 05/01/2024
Modalidade: Contínua
```

### Exemplo 2: Financiamento Parcelado
```
Descrição: Financiamento do Carro
Valor: R$ 800,00
Tipo: Despesa  
Frequência: Mensal
Data início: 15/01/2024
Modalidade: Parcelada (48 parcelas)
```

### Exemplo 3: Compras Semanais
```
Descrição: Supermercado
Valor: R$ 200,00
Tipo: Despesa
Frequência: Semanal
Data início: Todo sábado
Modalidade: Contínua
```

## Integração com o Sistema

### Dashboard
- As transações geradas aparecem no dashboard
- Contribuem para os gráficos e estatísticas
- São contabilizadas nos totais

### Relatórios
- Transações recorrentes são incluídas nos relatórios
- Marcadas como "recorrentes" para identificação
- Podem ser filtradas se necessário

### Categorias
- Herdam a categoria da recorrência
- Contribuem para análises por categoria
- Seguem a hierarquia de categorias

## Dicas de Uso

1. **Configure suas receitas fixas primeiro** (salário, aluguéis recebidos)
2. **Adicione despesas fixas** (aluguel, financiamentos, contas)
3. **Use datas de fim** para transações temporárias
4. **Monitore regularmente** o status das recorrências
5. **Pause ao invés de excluir** para interrupções temporárias

## Próximos Passos Sugeridos

- 🔔 Notificações de vencimento
- 📱 App mobile para gerenciamento
- 📊 Relatórios específicos de recorrências
- 🏦 Integração bancária para confirmação
- 📅 Calendário de vencimentos

---

**🎉 Agora suas finanças estão automatizadas!**

Acesse: http://localhost:5001/transacoes-recorrentes
