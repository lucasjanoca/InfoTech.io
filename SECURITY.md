# Segurança — InfoTech.io

A segurança deste projeto é tratada como parte do produto.

## Reportar uma vulnerabilidade

Não publique detalhes de uma possível vulnerabilidade em issues públicas, comentários ou redes sociais.

Use o canal de contato disponível no próprio site da InfoTech.io e informe apenas o necessário para que o problema possa ser reproduzido com segurança.

Evite acessar, alterar, copiar ou apagar dados de terceiros durante qualquer teste.

## Segredos

Nunca devem ser enviados ao repositório:

- chaves `service_role` ou secret keys do Supabase;
- senhas ou códigos de recuperação;
- arquivos `.env` de produção;
- chaves privadas, certificados privados ou tokens pessoais.

A chave publicável do Supabase usada pelo navegador não é um segredo; a proteção dos dados deve permanecer no RLS, nas permissões e nas funções do banco.

## Isolamento entre projetos

Este repositório contém o produto principal **InfoTech.io**. Projetos de clientes podem aparecer apenas como referências de portfólio, links ou assets de apresentação; o código de aplicação, backend, credenciais, regras de acesso e configurações operacionais desses projetos não devem ser reutilizados aqui para corrigir ou ampliar o site principal.

Antes de qualquer alteração em banco, autenticação, RLS, policies, grants, triggers ou Edge Functions, confirme explicitamente que o backend selecionado pertence à InfoTech.io e aplique somente os privilégios mínimos necessários. Nunca reutilize URL de projeto, identificador, chave, policy ou função de um projeto de cliente como atalho para resolver erros no produto principal.
