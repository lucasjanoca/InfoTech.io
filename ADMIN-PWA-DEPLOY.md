# InfoTech ADM — implantação independente (não ativada automaticamente)

## Arquitetura e estado

- **Clientes:** `https://infotech-io.com.br/`, GitHub Pages existente, `manifest.webmanifest` (id `/`), `sw.js`, layout público e área do cliente. Não houve alteração no site de produção nesta branch.
- **Admin:** build separado `dist-admin/`, destinado a um **projeto Cloudflare Pages diferente** com domínio `https://admin.infotech-io.com.br/`. O build gera somente oito páginas ADM e `index.html` de instalação, um manifesto exclusivo (id `/infotech-adm`, início `/admin-login.html`, escopo `/` **somente na origem ADM**), imagens PNG ADM 192/512, `admin-sw.js` e JS/CSS necessários. Nenhum HTML público, JS de cliente ou SW público é distribuído ali.
- Mesmo repositório de origem e banco Supabase, **origens e implantações independentes**. Subdomínio diferente isola service workers, Cache Storage, instalação PWA e armazenamento de sessão por origem. Não basta servir os dois na mesma origem com manifestos diferentes.
- Rotas ADM antigas no domínio público permanecem durante a migração para não interromper o serviço. A remoção/bloqueio dessas rotas e eventual link para o novo ADM só devem ocorrer depois do cutover e verificação do RLS. Isso é uma etapa pendente, não se deve anunciar a separação como integral em produção antes dela.

## 1. Criar o projeto Cloudflare Pages (requer autorização do proprietário)

Acesse https://dash.cloudflare.com/ e abra **Workers & Pages → Create application → Pages → Import an existing Git repository**. Vincule `lucasjanoca/InfoTech.io` a **um novo projeto** (por exemplo, `infotech-adm`). Não altere o projeto que eventualmente hospeda o site principal.

Configuração exata:

| Campo | Valor |
| --- | --- |
| Framework | None / nenhum |
| Root directory | raiz do repositório (`/`) |
| Production branch | `main` **após** aprovação/merge do PR |
| Build command | `python3 scripts/build_admin_pwa.py && python3 scripts/admin_pwa_sanity.py` |
| Build output directory | `dist-admin` |
| Variáveis/segredos | Nenhum adicional necessário; nunca usar service role no frontend |

O Pages fornecerá uma URL `https://<nome-real-do-projeto>.pages.dev/`. Não invente essa URL: copie-a do painel depois da implantação. O `index.html` na raiz do artefato apresenta instalação; o manifesto abre `/admin-login.html`.

Docs: https://developers.cloudflare.com/pages/get-started/git-integration/ ; https://developers.cloudflare.com/pages/configuration/build-configuration/

## 2. Vincular domínio (não executado)

No **novo** projeto Cloudflare Pages, abra **Custom domains → Set up a domain** e informe `admin.infotech-io.com.br`. Se a zona estiver na Cloudflare, o CNAME correspondente poderá ser criado automaticamente; caso contrário, o proprietário deve criar no provedor DNS um CNAME `admin` para a URL `*.pages.dev` real fornecida pelo novo projeto. **É necessário associar o domínio pelo Pages, não apenas criar o CNAME manualmente.** Verificar emissão TLS/HTTPS e se o domínio resolve antes de compartilhar.

Não alterar o CNAME do domínio raiz `infotech-io.com.br`, registros MX ou nomes de servidor. Não trocar DNS nem contratar serviço sem autorização.

Docs: https://developers.cloudflare.com/pages/configuration/custom-domains/

## 3. Supabase e Google — projeto existente, sem migração de banco

Projeto referenciado pelo frontend: `rgngqumqzylthdiazvfu`; dashboard de URLs (conferir interface atual): https://supabase.com/dashboard/project/rgngqumqzylthdiazvfu/auth/url-configuration

1. Manter **Site URL** do cliente `https://infotech-io.com.br/` (não substituir pelo subdomínio ADM nem por localhost).
2. Manter as Redirect URLs de cliente que já funcionam, incluindo `https://infotech-io.com.br/login.html` e demais rotas reais de confirmação/redefinição. Só acrescentar `https://admin.infotech-io.com.br/admin-login.html` se for configurado OAuth/links de e-mail administrativos; o login ADM atual utiliza `signInWithPassword`, não Google. Não adicionar coringas amplos desnecessários.
3. O OAuth Google do cliente redireciona explicitamente para a página de login na **origem atual**, portanto o build separado não o reescreve. Conferir no Supabase o callback de provedor Google (`https://rgngqumqzylthdiazvfu.supabase.co/auth/v1/callback`) e o retorno pós-login real. Nunca definir `http://localhost:3000` como Site URL de produção.
4. **Antes de liberar:** conferir diretamente no projeto correto políticas RLS de `profiles`, `requests`, `request_projects`, Storage e RPCs `admin_list_clients`, `admin_set_client_blocked`, `admin_save_request_project_v2`. Elas precisam verificar permissão admin no banco, status de bloqueio e MFA/AAL2 conforme o modelo existente. A checagem de `profiles.role` no JavaScript só orienta a navegação, **não substitui RLS/RPC**. Uma sessão de cliente jamais deve poder executar RPCs administrativas nem listar/alterar solicitações alheias via API.
5. A conexão Supabase disponível durante esta implementação retornou um projeto **diferente** do referenciado pelo site; portanto não foi possível auditar o RLS real, nem foi feita nenhuma alteração em banco, Auth ou dados.

Docs: https://supabase.com/docs/guides/auth/redirect-urls ; https://supabase.com/docs/guides/auth/social-login/auth-google

## 4. Testar antes do cutover

- [ ] CI do PR: build, manifesto, ícones PNG, escopo, arquivos/links, separação das rotas, `node --check`, limites do cache.
- [ ] Ambos os domínios carregam por HTTPS; a origem ADM não expõe páginas públicas, `sw.js` ou `manifest.webmanifest` do cliente.
- [ ] Android Chrome: instalar os dois, confirmar ícones e nomes diferentes e abrir cada um no destino correto.
- [ ] Desktop Chrome/Edge: instalar ambos sem substituição ou sobrescrita.
- [ ] iPhone Safari: Compartilhar → Adicionar à Tela de Início em **cada origem**; confirmar nomes/ícones, sem presumir disponibilidade de `beforeinstallprompt`.
- [ ] O botão de instalação aparece **somente quando o navegador entrega `beforeinstallprompt`**; confirmação somente no evento `appinstalled`; sem mensagens falsas de instalação.
- [ ] Service worker de cliente só controla `infotech-io.com.br`, ADM só `admin.infotech-io.com.br`; caches têm nomes isolados; nenhum HTML/API/solicitação administrativa armazenado offline.
- [ ] Login/sair admin, papel `profiles.role`, conta bloqueada, cadastro e desafio MFA, atualização de solicitação, clientes e histórico.
- [ ] Conta cliente não lê/escreve registros de outros usuários nem chama RPCs admin via REST (RLS real); Google login/retorno no aplicativo de cliente funciona.
- [ ] Não existem erros de JavaScript/requisições 404/CSP no console ou aba Network.

Após aprovar, fazer merge, ativar Pages/domínio e testar. **Só depois**, migrar links de entrada e remover/bloquear as páginas ADM do build público (ou colocar uma regra de redirecionamento cuidadosamente para páginas públicas legadas) em um segundo PR. Como rollback, retire o domínio do novo Pages e mantenha os caminhos ADM originais enquanto a falha é investigada.
