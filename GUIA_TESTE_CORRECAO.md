# 🧪 Guia de Teste - Transações Recorrentes

## ✅ **Correção Aplicada**

O erro `TypeError: TransacaoForm.validate() got an unexpected keyword argument 'extra_validators'` foi **CORRIGIDO**.

### 🔧 **O que foi corrigido:**
- Método `validate()` em `TransacaoForm` agora aceita o parâmetro `extra_validators=None`
- Método `validate()` em `TransacaoRecorrenteForm` também corrigido
- Compatibilidade total com Flask-WTF restaurada

---

## 🧪 **Como Testar:**

### 1. **Teste de Transação Única** (Funcionalidade original)
1. Acesse: http://localhost:5001/nova-transacao
2. Preencha:
   - Descrição: "Compra no mercado"
   - Valor: 150,00
   - Tipo: Despesa
   - Data: Hoje
   - Categoria: Qualquer uma
3. **NÃO** marque "Transação Recorrente"
4. Clique "Salvar Transação"
5. ✅ **Esperado:** Transação salva normalmente

### 2. **Teste de Transação Recorrente Contínua**
1. Acesse: http://localhost:5001/nova-transacao
2. Preencha:
   - Descrição: "Salário Mensal"
   - Valor: 5000,00
   - Tipo: Receita
   - Data: 01/01/2024
   - Categoria: Salário (ou qualquer uma)
3. ✅ **Marque** "Transação Recorrente"
4. Configure:
   - Frequência: Mensal
   - Data de fim: (deixe em branco)
   - **NÃO** marque "Transação Parcelada"
5. Clique "Salvar Transação"
6. ✅ **Esperado:** Transação recorrente criada + várias transações geradas

### 3. **Teste de Transação Parcelada**
1. Acesse: http://localhost:5001/nova-transacao
2. Preencha:
   - Descrição: "Financiamento Carro"
   - Valor: 800,00
   - Tipo: Despesa
   - Data: 15/01/2024
   - Categoria: Transporte (ou qualquer uma)
3. ✅ **Marque** "Transação Recorrente"
4. Configure:
   - Frequência: Mensal
   - Data de fim: (pode deixar em branco)
   - ✅ **Marque** "Transação Parcelada"
   - Número de Parcelas: 12
5. Clique "Salvar Transação"
6. ✅ **Esperado:** Transação parcelada criada + 12 transações geradas

### 4. **Teste de Validação** (Para verificar se não há mais erros)
1. Acesse: http://localhost:5001/nova-transacao
2. Marque "Transação Recorrente" mas **NÃO** escolha frequência
3. Clique "Salvar Transação"
4. ✅ **Esperado:** Mensagem de erro "Frequência é obrigatória"

5. Marque "Transação Parcelada" mas **NÃO** informe número de parcelas
6. Clique "Salvar Transação"
7. ✅ **Esperado:** Mensagem de erro "Número de parcelas é obrigatório"

---

## 🌐 **URLs para Testar:**

- **Nova Transação:** http://localhost:5001/nova-transacao
- **Ver Transações:** http://localhost:5001/transacoes
- **Gerenciar Recorrentes:** http://localhost:5001/transacoes-recorrentes
- **Dashboard:** http://localhost:5001/

---

## 🎯 **Cenários de Teste Sugeridos:**

### ✅ **Cenário 1: Salário Mensal**
- Tipo: Receita
- Valor: R$ 5.000
- Frequência: Mensal
- Modalidade: Contínua (sem fim)

### ✅ **Cenário 2: Aluguel**
- Tipo: Despesa  
- Valor: R$ 1.500
- Frequência: Mensal
- Modalidade: Contínua (sem fim)

### ✅ **Cenário 3: Financiamento**
- Tipo: Despesa
- Valor: R$ 800
- Frequência: Mensal
- Modalidade: 24 parcelas

### ✅ **Cenário 4: Compras Semanais**
- Tipo: Despesa
- Valor: R$ 200
- Frequência: Semanal
- Modalidade: Contínua

### ✅ **Cenário 5: Curso Trimestral**
- Tipo: Despesa
- Valor: R$ 300
- Frequência: Trimestral
- Modalidade: 4 parcelas (1 ano)

---

## 🚨 **Se Ainda Houver Erro:**

1. Verifique se está na versão corrigida do código
2. Reinicie a aplicação:
   ```bash
   pkill -f "python app.py"
   .venv/bin/python app.py
   ```
3. Limpe o cache do navegador
4. Teste em uma aba anônima

---

## ✅ **Indicadores de Sucesso:**

- ✅ Formulário carrega sem erros
- ✅ Opções de recorrência aparecem/desaparecem dinamicamente
- ✅ Validações funcionam corretamente
- ✅ Transações são criadas sem erro `TypeError`
- ✅ Mensagens de sucesso aparecem
- ✅ Redirecionamento funciona

**🎉 O sistema deve estar funcionando perfeitamente agora!**
