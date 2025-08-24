# Documentação: Consolidação de Transações Projetadas

## Visão Geral

A funcionalidade de consolidação de transações projetadas permite ao usuário:

1. Visualizar transações futuras projetadas diretamente na tela de transações
2. Marcar individualmente ou em lote as transações que deseja consolidar (gravar no banco)
3. Manter o banco de dados mais leve ao armazenar apenas o que é realmente necessário

## Funcionamento 

### Na Tela de Transações

1. **Visualização**: Transações futuras aparecem com uma etiqueta "Projetada" e um checkbox
2. **Consolidação Individual**: Cada transação projetada tem um botão verde para consolidação rápida
3. **Consolidação em Lote**: Marque várias transações e use o botão "Consolidar Selecionadas"
4. **Filtragem**: A opção "Mostrar Projeções" pode ser desativada para ver apenas transações reais

### Comportamento Técnico

1. As transações projetadas são calculadas com base nas recorrências ativas
2. São exibidas apenas para meses futuros (a partir do mês atual)
3. IDs negativos são usados para diferenciar projeções de transações reais
4. Após consolidação, as transações são gravadas no banco e recebem IDs positivos reais

## Benefícios

1. **Performance**: Redução drástica no tamanho do banco de dados
2. **Flexibilidade**: Usuário decide exatamente quais transações futuras armazenar
3. **Melhor Experiência**: Interface intuitiva para gerenciar transações futuras
4. **Visualização Precisa**: Projeções são calculadas em tempo real, garantindo precisão

## Fluxo de Dados

```
[Cálculo de Projeções] → Ao navegar para meses futuros
    ↓
[Exibição na Tela de Transações] → Com checkboxes para seleção
    ↓
[Seleção pelo Usuário] → Individual ou em lote
    ↓
[API de Consolidação] → Grava no banco apenas as selecionadas
    ↓
[Atualização da Visualização] → Transações consolidadas mostradas como reais
```

## Como Utilizar

1. **Navegue para um mês futuro** usando os botões de navegação
2. **Observe as transações projetadas** marcadas com a etiqueta "Projetada"
3. Para consolidar uma única transação:
   - Clique no botão verde com ícone de check
4. Para consolidar várias transações:
   - Marque os checkboxes das transações desejadas
   - Clique no botão "Consolidar X Selecionadas" que aparece no topo

## Considerações Técnicas

- As projeções são recalculadas a cada acesso, garantindo que estejam sempre atualizadas
- A consolidação respeita limites de parcelas e datas de fim de recorrências
- O sistema evita duplicação, verificando se uma transação já existe antes de consolidar
