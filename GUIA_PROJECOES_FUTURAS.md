# Guia: Sistema de Projeções Futuras para Transações Recorrentes

## Visão Geral

Este novo sistema permite que transações recorrentes futuras sejam **projetadas** sem serem gravadas no banco de dados, melhorando drasticamente a performance do sistema. As transações só são efetivamente gravadas quando o usuário escolhe "consolidá-las".

## Benefícios

1. **Performance Aprimorada**: O banco de dados armazena apenas transações passadas, presentes e as futuras que o usuário explicitamente decidiu consolidar
2. **Menor Consumo de Recursos**: Redução significativa no tamanho do banco de dados
3. **Maior Controle do Usuário**: Os usuários podem revisar e ajustar projeções antes de consolidá-las
4. **Melhor Visualização Futura**: Interface dedicada para ver e gerenciar projeções futuras

## Como Funciona

### Para Usuários

1. Na tela de Transações Recorrentes, utilize os botões "Projetar X Meses" para visualizar transações futuras
2. Um modal será exibido mostrando todas as projeções futuras
3. Transações existentes (já gravadas no banco) aparecem como "Consolidadas"
4. Transações projetadas (apenas calculadas, não gravadas) aparecem como "Projetadas"
5. Para gravar uma projeção no banco de dados:
   - Selecione uma ou mais projeções marcando suas caixas de seleção
   - Clique no botão "Consolidar Selecionadas"
   - Ou clique no ícone de confirmação em uma linha individual

### Para Desenvolvedores

#### Arquitetura

O sistema de projeções funciona assim:

1. **Projetar Futuro**: Calcula transações futuras baseadas nas regras de recorrência, mas não as grava no banco
2. **Exibir Projeções**: Mostra as transações calculadas junto com as já gravadas no banco
3. **Consolidar Selecionadas**: Apenas quando solicitado pelo usuário, grava as projeções no banco de dados

#### API

Duas novas rotas foram adicionadas:

1. **GET `/api/projetar-transacoes-futuras?meses={meses}`**
   - Projeta transações futuras para todas as recorrências ativas
   - Retorna tanto as projeções quanto as transações já consolidadas
   - Parâmetro: `meses` (1-60) - Horizonte de projeção

2. **POST `/api/consolidar-projecoes`**
   - Consolida (salva no banco) as projeções selecionadas
   - Requer IDs e dados das projeções a serem consolidadas

#### Fluxo de Dados

```
[Cálculo de Projeções]
    ↓
[Exibição no Frontend] → IDs negativos para projeções temporárias
    ↓
[Seleção pelo Usuário]
    ↓
[Consolidação] → Gravação no banco com IDs reais
```

#### IDs Temporários

Projeções usam IDs negativos para distingui-las de transações reais (que têm IDs positivos do banco de dados).

## Considerações sobre Performance

- As projeções são calculadas sob demanda, não sobrecarregando o banco
- Apenas transações relevantes são armazenadas
- Interface adaptada para manipular grandes conjuntos de projeções eficientemente

## Futuras Melhorias

1. Permitir edição de projeções antes da consolidação
2. Adicionar filtros mais avançados na visualização de projeções
3. Implementar projeções automáticas no dashboard com gráficos de tendência futura
4. Adicionar agendamento de consolidações (ex: consolidar automaticamente no início do mês)
