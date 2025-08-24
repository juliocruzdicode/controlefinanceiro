# Navegação Mensal na Página de Transações

## Funcionalidade

A página de transações agora possui botões para navegar facilmente entre os meses, permitindo visualizar rapidamente as transações de cada período sem precisar configurar manualmente os filtros de data.

## Como Usar

1. **Botões de Navegação**: Na parte superior da página de transações, você encontrará três botões:
   - **Mês Anterior**: Navega para o mês anterior ao atual
   - **Mês Atual**: Mostra o mês e ano sendo visualizados
   - **Próximo Mês**: Navega para o mês seguinte ao atual

2. **Filtros Automáticos**: Ao navegar entre os meses, o sistema automaticamente:
   - Define a data de início como o primeiro dia do mês selecionado
   - Define a data de fim como o último dia do mês selecionado
   - Aplica esses filtros à consulta de transações

3. **Visualização dos Filtros**: Os campos de filtro de data mostrarão as datas correspondentes ao mês selecionado.

4. **Personalização**: Você ainda pode:
   - Modificar manualmente as datas para consultas personalizadas
   - Usar o botão "Limpar" para remover todos os filtros e ver todas as transações

## Comportamento

- Ao acessar a página pela primeira vez, são mostradas as transações do mês atual
- A navegação pelos botões preserva outros filtros aplicados (categoria, conta, tipo)
- O sistema sempre mostra o nome do mês e ano atuais no botão central
- Ao limpar os filtros, todos os filtros são removidos, inclusive o filtro mensal

## Geração Automática de Transações Recorrentes (MELHORADA)

Uma funcionalidade adicional foi implementada para garantir uma experiência de navegação perfeita:

- **Geração Automática Contínua**: O sistema agora gera transações recorrentes continuamente, sem limite de 60 transações e com horizonte de geração dinâmico.

- **Melhorias Implementadas**:
  - **Horizonte de Geração Dinâmico**: Se você navegar para períodos muito futuros, o sistema automaticamente aumenta o período de geração
  - **Sem Limite de Quantidade**: Removida a restrição de 60 transações, permitindo visualização ilimitada de transações futuras
  - **Verificação Otimizada**: Processamento mais eficiente para evitar geração desnecessária
  - **Tratamento Robusto de Erros**: Sistema mais estável durante a geração de muitas transações
  - **Logs Detalhados**: Informações completas sobre o processo de geração para facilitar a depuração

- **Comportamento Avançado**:
  - Padrão: gera 12 meses à frente da data atual
  - Navegação distante: expande automaticamente o horizonte, gerando 6 meses além do mês visualizado
  - Exemplo: se você navegar para 24 meses à frente, o sistema gerará transações para 30 meses no futuro

- **Condições para Geração**:
  - Quando a última transação gerada está dentro de um período de 3 meses à frente
  - Quando há menos de 60 transações geradas para uma recorrência específica
  - Quando a data da última transação é anterior à data limite de visualização

- **Comportamento**:
  - O sistema gera automaticamente as próximas 12 transações recorrentes
  - Você receberá uma notificação informando quantas transações foram geradas e quais recorrências
  - A lista de transações é atualizada para incluir as novas transações geradas

- **Correções na Implementação**:
  - Uso de `relativedelta` em vez de `timedelta` para cálculos de meses mais precisos
  - Verificação melhorada para comparar datas do mesmo tipo (date vs datetime)
  - Reconstrução completa da consulta após gerar novas transações

## Dicas

- Use esta funcionalidade para analisar rapidamente seu fluxo de caixa mês a mês
- Combine com outros filtros para análises específicas (ex: despesas de alimentação por mês)
- Ao clicar em "Limpar", você verá todas as suas transações sem restrições de data
- Para visualizar transações futuras, simplesmente continue navegando com o botão "Próximo Mês" - o sistema gerará automaticamente as transações recorrentes conforme necessário

## Solução de Problemas

Se a geração automática de transações não funcionar:

1. Verifique se as transações recorrentes estão com status "Ativa"
2. Verifique os logs da aplicação para ver os detalhes do processo de geração
3. Certifique-se de que as transações recorrentes têm datas de início válidas
4. Se uma transação recorrente tem data fim definida, verifique se ela não está no passado
