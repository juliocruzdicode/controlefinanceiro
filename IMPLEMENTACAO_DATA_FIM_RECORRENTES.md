# Implementação de Transações Recorrentes com Data Fim

Esta implementação atualiza o sistema para gerar corretamente todas as transações recorrentes até a data de fim quando esta estiver definida, garantindo que o planejamento financeiro seja preciso e completo.

## Principais Alterações Realizadas

1. **Modificação do método `gerar_transacoes_pendentes` no modelo `TransacaoRecorrente`**:
   - Agora o método aceita um parâmetro `meses_futuros` (padrão: 12) para definir o horizonte de previsão
   - Quando a transação tem `data_fim` definida, todas as transações são geradas até essa data, independentemente do horizonte
   - Quando não há `data_fim`, as transações são geradas para os próximos `meses_futuros` meses

2. **Atualização do Agendador de Tarefas (`scheduler_service.py`)**:
   - O serviço agora passa o parâmetro `meses_futuros` ao chamar `gerar_transacoes_pendentes`
   - Logs aprimorados para mostrar quando as transações são geradas até a data_fim ou para um número de meses

3. **Melhoria nas Mensagens aos Usuários**:
   - Feedback personalizado quando transações são geradas até a data_fim
   - Indicação clara do horizonte de planejamento quando não há data_fim

4. **Atualizações nas APIs**:
   - A API `/api/transacao-recorrente/<id>/gerar` agora retorna informações sobre data_fim
   - A API `/api/gerar-todas-transacoes-pendentes` mostra quantas recorrências usam data_fim e quantas usam horizonte futuro

## Como Funciona

### Com Data Fim Definida

1. **Comportamento**: Quando uma transação recorrente tem `data_fim` definida, todas as transações serão geradas de uma vez até esta data.
2. **Finalização Automática**: Após gerar todas as transações até a data_fim, a recorrência é automaticamente marcada como FINALIZADA.
3. **Mensagens ao Usuário**: Ao criar ou gerar transações para uma recorrência com data_fim, a mensagem mostrará "transações geradas até DD/MM/AAAA".

### Sem Data Fim Definida

1. **Comportamento**: Sem `data_fim`, o sistema gera transações para os próximos 12 meses (ou outro valor especificado).
2. **Geração Contínua**: A cada execução do agendador ou solicitação manual, novas transações são geradas para manter o horizonte de previsão.
3. **Mensagens ao Usuário**: Ao criar ou gerar transações, a mensagem mostrará "transações geradas para os próximos X meses".

## Cenários de Uso

### Transações com Fim Definido (Parceladas)

- **Exemplo**: Um financiamento de 24 parcelas começando em 01/01/2023 e terminando em 01/12/2024.
- **Comportamento**: Todas as 24 parcelas serão geradas de uma vez, mesmo que o horizonte padrão seja de 12 meses.
- **Finalização**: Após gerar todas as parcelas, a recorrência é marcada como FINALIZADA automaticamente.

### Transações Contínuas (Sem Fim Definido)

- **Exemplo**: Uma assinatura mensal de streaming sem data de término.
- **Comportamento**: Serão geradas transações para os próximos 12 meses a partir da data atual.
- **Extensão**: Quando o usuário visualizar transações próximas ao fim do período atual, o sistema automaticamente gerará mais transações.

## Recomendações de Uso

1. **Para contas parceladas**: Sempre defina a `data_fim` ou o `total_parcelas` para que o sistema gere todas as parcelas corretamente.
2. **Para despesas fixas contínuas**: Deixe a `data_fim` em branco para que o sistema mantenha um horizonte de planejamento constante.
3. **Para planejamento de longo prazo**: Ao visualizar transações futuras na página de previsão, você pode manualmente gerar transações para um horizonte maior (até 36 meses).

Esta implementação permite um planejamento financeiro mais preciso, garantindo que todas as transações recorrentes sejam corretamente geradas até sua data de término, quando definida.
