# Guia de Configuração para Autenticação com Google

Este guia explica como configurar a autenticação com Google em sua aplicação Controle Financeiro.

## Pré-requisitos

1. Você precisa ter uma conta Google
2. Acesso ao [Google Cloud Console](https://console.cloud.google.com/)

## Passo a Passo para Configuração

### 1. Criar um Projeto no Google Cloud Platform

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Clique em "Selecionar um projeto" no topo da página
3. Clique em "Novo Projeto"
4. Digite um nome para o projeto (ex: "Controle Financeiro")
5. Clique em "Criar"

### 2. Configurar o OAuth Consent Screen (Tela de Consentimento)

1. No menu lateral, vá para "APIs e Serviços" > "Tela de consentimento OAuth"
2. Selecione "Externo" (ou "Interno" se for apenas para uso na sua organização)
3. Preencha os campos obrigatórios:
   - Nome do aplicativo: "Controle Financeiro"
   - Email de suporte do usuário: seu email
   - Email de contato do desenvolvedor: seu email
4. Clique em "Salvar e Continuar"
5. Na tela de "Escopos", clique em "Adicionar ou remover escopos"
6. Selecione os seguintes escopos:
   - `userinfo.email`
   - `userinfo.profile`
   - `openid`
7. Clique em "Atualizar" e depois "Salvar e Continuar"
8. Na tela de "Usuários de teste", adicione os emails que poderão testar o aplicativo (incluindo o seu)
9. Clique em "Salvar e Continuar"
10. Revise as informações e clique em "Voltar ao Painel"

### 3. Criar Credenciais OAuth

1. No menu lateral, vá para "APIs e Serviços" > "Credenciais"
2. Clique em "Criar Credenciais" e selecione "ID do cliente OAuth"
3. Em "Tipo de aplicativo", selecione "Aplicativo da Web"
4. Digite um nome para o cliente (ex: "Controle Financeiro Web")
5. Em "Origens JavaScript autorizadas", clique em "Adicionar URI" e adicione:
   - `http://localhost:5000` (para desenvolvimento)
   - `https://seu-dominio.com` (para produção, se aplicável)
6. Em "URIs de redirecionamento autorizados", clique em "Adicionar URI" e adicione:
   - `http://localhost:5000/auth/callback` (para desenvolvimento)
   - `https://seu-dominio.com/auth/callback` (para produção, se aplicável)
7. Clique em "Criar"
8. Uma janela aparecerá com seu ID do cliente e Chave secreta do cliente. Anote essas informações.

### 4. Configurar a Aplicação

1. Abra o arquivo `.env` (ou crie um a partir do `.env.example`)
2. Adicione as seguintes variáveis com os valores obtidos no passo anterior:
   ```
   GOOGLE_CLIENT_ID=seu-client-id-do-google
   GOOGLE_CLIENT_SECRET=sua-client-secret-do-google
   ```
3. Salve o arquivo

### 5. Testar a Autenticação

1. Inicie a aplicação
2. Acesse a página de login
3. Clique no botão "Entrar com Google"
4. Você será redirecionado para o Google para autenticação
5. Após autenticar, você será redirecionado de volta para a aplicação

## Solução de Problemas

### Erro "invalid_client"

Se você receber um erro como "invalid_client", verifique se:
- O ID do cliente e a chave secreta estão corretamente configurados no arquivo `.env`
- A URL de redirecionamento está exatamente igual à configurada no Google Cloud Console

### Erro "redirect_uri_mismatch"

Se você receber um erro como "redirect_uri_mismatch", verifique se:
- A URL de redirecionamento configurada no Google Cloud Console corresponde exatamente à URL usada pela aplicação
- Para desenvolvimento local, certifique-se de que está usando `http://localhost:5000/auth/callback` (com a porta correta)

### Outros Erros

Para outros erros, verifique os logs da aplicação (`app.log`) para mais detalhes.

## Considerações de Segurança

- Mantenha seu `GOOGLE_CLIENT_SECRET` seguro e nunca o inclua em código-fonte versionado
- Em produção, certifique-se de usar HTTPS para todas as comunicações
- Considere limitar o acesso à sua aplicação a apenas usuários específicos durante a fase de teste
