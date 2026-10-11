# AGENTS.md — Guia para agentes de IA da InfoTech.io

Este arquivo orienta Codex e outros agentes que trabalham **neste repositório**, que contém o site e a área do cliente da InfoTech.io. Prioridade: segurança de dados, estabilidade da produção e alterações pequenas, verificáveis e reversíveis.

## 1. Antes de editar

1. Leia `README.md`, `SECURITY.md`, este arquivo e as partes relevantes de `docs/`.
2. Identifique o fluxo afetado, os arquivos responsáveis e os testes já existentes. Não faça refatorações gerais para resolver um bug pontual.
3. Trabalhe em **branch separada** e abra Pull Request para `main`. Não faça push direto para `main`, merge automático ou deploy sem aprovação explícita.
4. Preserve recursos que já funcionam. Documente os riscos, o comportamento esperado e uma forma de reverter.
5. Se faltar acesso, credencial, ambiente de teste ou informação do banco, informe o bloqueio; não invente resultados nem tente contornar permissões.

## 2. Mapa do projeto

- `index.html` e demais `*.html` na raiz: páginas públicas, autenticação, cliente e administração.
- `css/`: estilos e ajustes responsivos; `css/jss/`: JavaScript da aplicação, integrações e interface.
- `css/jss/supabase-config.js`, `css/jss/*supabase*.js` e arquivos de autenticação: integração com Supabase; mudanças aqui exigem atenção especial.
- `manifest.webmanifest`, `admin-manifest.webmanifest`, `sw.js`, `offline.html`: PWA, instalação e funcionamento offline.
- `io/`: funcionalidade separada; não misture suas rotas e cache com o site principal sem necessidade.
- `android-app/`: aplicativo Android; evite alterar o build quando a tarefa é apenas web.
- `scripts/`: verificações locais; `.github/workflows/`: GitHub Actions; `_headers`: cabeçalhos de segurança; `docs/`: documentação e procedimentos.

O projeto utiliza HTML, CSS, JavaScript, GitHub Pages e Supabase. **Não presuma** que há Node/npm, framework frontend, servidor privado ou infraestrutura não documentada.

## 3. Regras de segurança (obrigatórias)

- Siga `SECURITY.md`. Nunca exponha, gere ou versione `service_role`, `sb_secret_*`, senhas, tokens privados, `.env` de produção, chaves de assinatura ou dados pessoais.
- A chave **publicável** do Supabase pode aparecer no frontend; ela não substitui autorização no banco. A proteção real de dados depende de RLS, permissões e validação no servidor.
- Não altere SQL, policies RLS, grants, triggers, Edge Functions, usuários reais ou projetos Supabase sem autorização explícita e confirmação da instância correta.
- Não copie configurações, credenciais, código operacional ou banco de dados de clientes para resolver problemas deste repositório.
- Nunca trate elementos ocultos do frontend, variáveis locais ou verificações JavaScript como autorização de administrador.
- Para mudanças em login, recuperação de senha, upload, permissões ou área ADM, proponha testes de **acesso permitido e acesso negado**; teste isolamento entre usuários usando dados fictícios e ambiente autorizado.
- Não remova CSP, cabeçalhos, validações, auditorias ou controles de segurança apenas para fazer um teste passar.

## 4. PWA, compatibilidade e estabilidade

- Preserve navegação em celular e desktop; valide o fluxo real, inclusive a sessão autenticada.
- `sw.js` não deve armazenar respostas privadas, páginas administrativas, solicitações autenticadas, tokens ou respostas do Supabase. Revise escopo, invalidação e atualização do cache ao modificar o PWA.
- Trate `manifest.webmanifest` e `admin-manifest.webmanifest` como identidades distintas; não misture instalação do aplicativo público e do administrativo.
- Não altere domínio, `CNAME`, URLs de OAuth, projeto Supabase, configurações Cloudflare ou publicação em produção sem solicitação expressa.
- Faça mudanças compatíveis com o código existente; evite dependências, permissões de navegador ou novos serviços desnecessários.

## 5. Testes antes do Pull Request

Execute, da raiz do repositório, os testes pertinentes ao que foi alterado. A suíte local é baseada em scripts Python; exemplos:

```sh
python3 scripts/site_sanity.py
python3 scripts/auth_input_sanity.py
python3 scripts/web_storage_boundary.py
python3 scripts/web_storage_resilience.py
python3 scripts/service_worker_sanity.py
python3 scripts/manifest_identity_sanity.py
python3 scripts/csp_sanity.py
```

Para HTML/CSS/JS, verifique também os fluxos afetados manualmente em navegador e no celular, quando disponíveis. Para mudanças em JS, valide sintaxe com `node --check caminho/arquivo.js` **se Node estiver disponível**. Registre testes não executados e por quê; não diga que passou sem executá-lo.

Em `.github/workflows/`:
- Preserve `permissions: contents: read` e `timeout-minutes` por job, conforme `site-security-check.yml`.
- Fixe cada Action externa a **SHA completo verificado de 40 caracteres**, com comentário da versão para legibilidade; nunca substitua a auditoria por uma exceção sem justificativa.
- Confirme que `site-security-check.yml` e as checagens relacionadas passaram no PR; se algum job falhar, identifique a causa antes do merge.

## 6. Entrega e revisão

- Commits pequenos e descritivos; concentre cada PR em uma mudança coerente.
- O PR deve informar: problema, arquivos modificados, motivo, riscos (segurança/PWA/autenticação), testes e passos de validação manual/rollback.
- Novos comportamentos devem incluir teste de regressão quando viável; nunca simule dados reais para afirmar que backend ou login estão funcionando.
- Não faça merge sem aprovação do responsável. Se houver alterações concorrentes na `main`, reavalie o diff e as checagens.
