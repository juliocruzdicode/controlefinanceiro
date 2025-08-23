# Configuração da Autenticação Google OAuth

## Configuração Atual
- **Cliente ID**: 325182882851-gmflnq7r9ljl297atadbvjn7vc7fq8dg.apps.googleusercontent.com
- **Cliente Secret**: Armazenado no arquivo .env
- **URI de Redirecionamento**: https://prosperai.site/callback

## Instruções para Configurar no Google Cloud Console

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Vá para "APIs e Serviços" > "Credenciais"
3. Encontre o cliente OAuth ID existente e clique nele para editar
4. Em "URIs de redirecionamento autorizados", verifique se a seguinte URI está adicionada:
   ```
   https://prosperai.site/callback
   ```
5. Se não estiver, adicione-a e clique em "Salvar"

## Configurações Adicionais Recomendadas

1. Em "Tela de consentimento OAuth", verifique se:
   - O nome do aplicativo está correto
   - O domínio `prosperai.site` está nos domínios autorizados
   
2. Verifique se a API Google+ está habilitada no projeto:
   - Vá para "APIs e Serviços" > "Biblioteca"
   - Procure por "Google+ API" ou "Google Sign-In API"
   - Certifique-se de que está habilitada

## Testando a Autenticação

1. Acesse https://prosperai.site/
2. Clique no botão "Entrar com Google"
3. Você deve ser redirecionado para a tela de login do Google
4. Após o login, você deve ser redirecionado de volta para `https://prosperai.site/callback`
5. Se o redirecionamento não funcionar, verifique os logs do container para diagnóstico:
   ```bash
   docker logs controle_financeiro_app
   ```
