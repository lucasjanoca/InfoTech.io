# Changelog — InfoTech.io

Histórico consolidado das principais versões do projeto. Este arquivo substitui os antigos arquivos de alterações e READMEs de preview espalhados na raiz do repositório.

## V9.6

### Mobile / UX
- Refinamentos V15–V17 aplicados globalmente para melhorar espaçamento, títulos e acabamento das páginas no celular.
- Refinamentos V18–V19 incorporados com ajustes de badges/labels, apresentação da logo local do Rass Studio, preferência de contato e animação do cadeado de login.
- Página de Serviços com badge e título centralizados e contidos na largura da tela.
- Carrossel da página Sobre simplificado para navegação por swipe/arraste ou indicadores, sem botão Próximo redundante.
- Animação visual do cadeado refinada e respeitando `prefers-reduced-motion`.
- Espaços excessivos antes do rodapé reduzidos em páginas públicas e fluxos de autenticação.

### PWA
- Cache do Service Worker atualizado para `infotech-pwa-v9.6.1`.
- App shell atualizado com recursos usados pelos refinamentos mobile e pelo carrossel da página Sobre.
- Navegações só entram no cache quando pertencem a uma allowlist explícita de páginas públicas; rotas novas, desconhecidas, autenticadas e administrativas ficam fora do cache por padrão.
- Rotas sensíveis continuam fora do cache público do Service Worker.
- A auditoria local agora valida também `start_url`, ícones e atalhos do `manifest.webmanifest`, impedindo que futuras alterações publiquem um PWA com rota ou asset de instalação inexistente.
- Ícones do manifest principal, do manifest administrativo e dos atalhos PWA agora precisam permanecer na própria origem do app; referências externas são rejeitadas pelo sanity check.
- Nova auditoria dedicada do Service Worker valida que recursos do `APP_SHELL` existem, não se repetem e que páginas pré-cacheadas também pertencem à allowlist pública; rotas autenticadas e administrativas são rejeitadas automaticamente.

### Segurança / CI
- Nova auditoria dedicada da CSP valida a proteção `<meta http-equiv="Content-Security-Policy">` realmente portátil no GitHub Pages em todas as páginas HTML, exigindo baseline segura, rejeitando `unsafe-inline`, `unsafe-eval`, wildcards e origens HTTP; páginas sem scripts podem usar corretamente o fallback de `default-src`.
- Nova auditoria dedicada do `.well-known/security.txt` valida campos obrigatórios, `Canonical` oficial, URLs HTTPS de contato/política apontando para páginas locais existentes, `Preferred-Languages` com `pt-BR` e data de expiração ainda válida.
- O sanity check agora exige `noindex` também nas páginas utilitárias sensíveis `admin-install.html`, `email-confirmado.html` e `solicitacao-enviada.html`; a auditoria do `robots.txt` passa a incluir explicitamente o instalador administrativo.
- Nova auditoria dedicada do `robots.txt` valida o sitemap oficial e garante que rotas privadas, administrativas e pós-autenticação continuem efetivamente cobertas pelas regras de exclusão de indexação; o próprio check documenta que `robots.txt` não substitui autenticação, `noindex` ou RLS.
- O sitemap passa por validação dedicada no CI: apenas URLs HTTPS da origem oficial são aceitas, páginas privadas/admin são proibidas, destinos locais precisam existir e URLs duplicadas, com query ou fragmento são rejeitadas.
- O Site security check passa a rejeitar páginas HTML de produção que voltem a referenciar scripts `demo` ou `legacy`, evitando regressão acidental para fluxos locais antigos.
- O sanity check inspeciona o conteúdo dos scripts JavaScript locais realmente carregados pelas páginas de produção e rejeita as chaves exclusivas do armazenamento demo (`infotechDemoRequests` e `infotechDemoUser`), mesmo quando o nome do arquivo não contém `demo` ou `legacy`. A chave `infotechLastProtocol` permanece permitida porque o fluxo real a usa apenas em `sessionStorage` para transportar o protocolo recém-criado até a tela de sucesso.
- O CI também exige a allowlist de navegação pública do Service Worker e o bloqueio de cache para navegações fora dela.
- A varredura de segredos agora decodifica tokens JWT rastreados em arquivos públicos e rejeita automaticamente qualquer token Supabase cujo payload contenha `role=service_role`, mesmo quando o texto `service_role` não aparece ao lado da chave.
- O sanity check valida referências do manifest PWA além das referências HTML, mantendo instalação e atalhos protegidos contra links quebrados.
- A validação de integridade PWA também cobre `admin-manifest.webmanifest`, incluindo `start_url`, ícones e atalhos quando existirem, evitando regressões no app administrativo.
- O sanity check passa a permitir scripts externos apenas via HTTPS no host aprovado `cdn.jsdelivr.net` e exige versão semântica exata do SDK `@supabase/supabase-js`, bloqueando `@latest`, tags flutuantes, URLs sem versão e hosts de script não aprovados.
- A validação dos manifests agora também rejeita `start_url`, `scope` e atalhos externos à origem do app e garante que `start_url`/atalhos permaneçam dentro do `scope` declarado.

## V9.5

### Segurança / CI
- Actions externas do workflow Android fixadas por SHA imutável, reduzindo risco de supply-chain sem alterar o comportamento do build.
- Mantidos `permissions: contents: read`, Java 17, Android 16, Gradle 9.5 e geração do checksum SHA-256 do APK.
- Auditoria automática dos workflows passa a exigir `permissions` explícitas, bloquear `pull_request_target` e exigir SHA completo de 40 caracteres para Actions externas.

## V8.0

### Segurança
- CSP sem `unsafe-inline`.
- PKCE no Supabase Auth.
- Senha removida do Web Storage.
- MFA TOTP administrativo.
- RLS V8 e helper de usuário ativo.
- RPCs administrativas protegidas.
- Bucket privado e upload com allowlist.
- URLs assinadas mais curtas.
- `security.txt`.

### Qualidade
- Auditoria automática e GitHub Actions.
- Validação de CSS, HTML, JavaScript, manifest e sitemap.
- Melhorias de acessibilidade.
- Imagens com dimensões e prioridade de carregamento.
- Suporte a `prefers-reduced-motion`.

### SEO/PWA
- Canonical, Open Graph e Twitter Cards.
- Sitemap, robots, manifest e ícones 192/512.
- Páginas de Privacidade, Segurança e 404.

### Backend
- Criação/sincronização de perfil ligada ao Auth.
- Bloqueio aplicado também nas policies.
- Funções administrativas versionadas.

## V6.7 — Preview
- Artes originais do Instagram reutilizadas onde disponíveis.
- Novos emblemas para Aplicativos, Automação, Programas e Suporte.
- Logos e emblemas do conteúdo mantidos estáticos, concentrando animações em elementos de atenção.
- Personagem do cabeçalho refinado com novas animações.
- Carrosséis reescritos para arraste, impulso e loop contínuo mais estáveis.
- Fluxo login → cadastro → confirmação → solicitação passou a preservar destino e serviço escolhido.
- Credenciais inválidas podiam encaminhar ao cadastro sem colocar senha na URL.
- Ajustes de centralização das imagens internas.

## V6.6 — Preview
- Revisão focada em estabilidade, desempenho e compactação visual.
- Carrosséis otimizados com rolagem nativa no toque.
- Serviços reorganizados em grade 3 × 2.
- Projetos reorganizados em grade 3 × 2.
- Ajustes para reduzir overflow lateral, custo de pintura e travamentos no celular.
- Refinamentos de identidade visual e animação do personagem de acesso.

## V6.4 — Preview
- Revisão de estabilidade, desempenho e compactação visual.
- Serviços e projetos migrados de carrosséis para grades.
- Redução de elementos redundantes da interface.
- Aura neon sincronizada aplicada a marcas e ícones principais.
- Ajustes para reduzir overflow e melhorar desempenho móvel.

## V6.3 — Preview
- Carrosséis com loop visual, arraste no toque e autoplay.
- Animações da marca sincronizadas.
- Hero e textos da Home compactados.
- Página de Projetos e Sobre simplificadas.

## V6.2 — Preview
- Revisão focada em responsividade mobile, carrosséis, compactação de conteúdo e portfólio.
- Integrações existentes com Supabase preservadas.
- Melhorias concentradas em interface, navegação e apresentação.

## V5.1.5
- Corrigida referência ambígua de `request_id`.
- Função de salvamento passa a retornar JSON.
- UPSERT passa a usar `request_projects_pkey`.
- Ajustado fallback de UUID no JavaScript.

## V5.1.4
- Removida dependência obrigatória de `crypto.randomUUID()`.
- Adicionado gerador de UUID compatível com navegadores antigos.
- Corrigidos andamento do projeto, chat e upload de arquivos afetados por incompatibilidade.

## V5.1.3
- Botão de salvar andamento deixa de enviar formulário/causar redirecionamento indevido.
- Criada `admin_save_request_project_v2` com payload JSON.
- Sucesso exibido apenas após confirmação do banco.
- Progresso lido diretamente de `request_projects` por cliente e administrador.
- Atualização em tempo real do progresso.

## V5.1.2
- Criada tabela `request_projects` para prazo, etapas, histórico e porcentagem.
- Salvamento por função administrativa segura.
- Tela relê o banco antes de confirmar sucesso.
- Cliente e administrador usam a mesma fonte de dados.
- Compatibilidade mantida com o campo `project` legado.

## V5.1.1
- Corrigidos salvamento e leitura do progresso do projeto.
- Restaurado bloqueio/reativação de clientes.
- Bloqueio persistido no Supabase.
- Contas bloqueadas não mantêm sessão ativa.
- Conta administrativa protegida contra bloqueio pela interface.

## V5.1.0 — Dashboard profissional
- Indicadores de clientes, projetos ativos, mensagens e arquivos.
- Pesquisa global por cliente, e-mail, protocolo, serviço e título.
- Gráfico de solicitações por status.
- Atividades recentes.
- Indicador de saúde e conexão com Supabase.
- Layout responsivo em desktop, tablet e celular.

## V5.0.5.2 — Estabilidade
- Revisado salvamento do andamento do projeto.
- Função SQL atualiza `updated_at` e solicita recarga do cache da API.
- JavaScript aceita retorno em objeto ou lista do Supabase.
- Mensagens de erro mais claras para cache de função.
- Cache-busting do script de projeto no GitHub Pages.
- Links e arquivos locais revisados.

## V5.0.5.1
- Corrigido salvamento do andamento do projeto.
- Prazo, etapas e porcentagem salvos por função segura do Supabase.
- Sucesso exibido somente após confirmação do banco.
- Erros do Supabase expostos para diagnóstico.

## V5.0.5
- Arquivos migrados para Supabase Storage, com limite de 10 MB.
- Chat online com atualização em tempo real.
- Histórico automático de solicitações, mensagens, arquivos e andamento.
- Notificações para cliente e administrador.
- Prazo e etapas persistidos e sincronizados pelo Supabase.

## V5.0.4.1 — Correção de projeto
- Restauradas cinco etapas padrão no painel administrativo.
- Prazo e etapas passam a ser salvos no Supabase.
- Corrigido redirecionamento indevido para “Solicitação não encontrada”.
- Cliente passa a ver o mesmo progresso salvo pelo administrador.

## V5.0.1 — Autenticação Supabase
- Cadastro e login reais via Supabase Auth.
- Sessão persistente e logout real.
- Proteção das páginas do cliente por sessão.
- Nome salvo em `user_metadata.full_name`.
- Edição de nome/e-mail e troca de senha pelo perfil.
- Recuperação de senha por e-mail.
- Chave `service_role` não usada no frontend.
- Nesta etapa, autenticação online convivia com dados legados em `localStorage`.

## V4.9.1 — Segurança local
- Cliente pode alterar senha informando a senha atual.
- Troca de senha encerra outras sessões.
- Registro de último acesso e atividade recente.
- Administrador pode encerrar sessões sem bloquear a conta.
- Bloqueio/reativação invalida sessões antigas.
- Histórico local de ações de segurança.

## V4.9 — Controle de contas
- Status Ativo/Bloqueado na Área de Clientes.
- Administrador pode bloquear e reativar contas.
- Contas bloqueadas não acessam nem mantêm sessão.
- Compatibilidade com contas antigas sem status.
- Implementação ainda baseada em `localStorage`.

## V4.8.1
- Mantida a Área de Clientes.
- Adicionado “Esqueci minha senha”.
- Recuperação de senha local com validação de conta e confirmação da nova senha.
- Sessão encerrada após redefinição da própria senha.
- Login deixa de criar conta acidentalmente para e-mail inexistente.
- Recuperação ainda era somente demonstração local, sem envio real de e-mail.

## V4.8 — Área de Clientes
- Criada opção Clientes no menu administrativo.
- Lista de contas salvas no navegador.
- Pesquisa por nome, e-mail ou empresa.
- Indicadores de contas, solicitações e projetos ativos.
- Página individual do cliente e histórico de solicitações.
- Dados ainda eram locais via `localStorage`.

## V4.7.2 — Refinamento
- Revisão das 16 páginas HTML para desktop e celular.
- Correções de rolagem horizontal, navegação móvel e áreas de toque.
- Dashboard administrativo com agrupamentos de status consistentes.
- Data prevista de entrega no padrão brasileiro.
- Revisão de progresso, arquivos, chat e notificações.
- Padronização visual via `css/refinement-v472.css`.
- Títulos das abas e favicon padronizados.
- Preferência de redução de movimento respeitada.

## V4.7.1 — Dashboard administrativo
- Saudação e resumo administrativo.
- Indicadores automáticos por status e prioridade.
- Cards clicáveis e sincronizados com a lista.
- Pesquisa em tempo real.
- Filtros rápidos por situação.
- Layout responsivo preservando chat, arquivos, projeto, histórico e orçamentos.

## V4.6.1
- Títulos administrativos padronizados com a marca.
- Favicon adicionado às páginas administrativas.
- Correção de espaço extra antes do banner no celular.
- Cabeçalho móvel mantido com comportamento sticky.

## V4.6 — Refinamento
- Melhorias de responsividade e prevenção de rolagem horizontal.
- Abas de Conversa, Arquivos, Projeto e Histórico adaptadas ao celular.
- Áreas clicáveis maiores e foco visível para teclado.
- Melhor quebra de textos, protocolos, e-mails e nomes de arquivos.
- Padronização de formulários, cards e botões.
- Carregamento progressivo de imagens.
- Suporte a redução de movimento e fechamento de menus com Escape.
- Proteção contra duplo clique em formulários.
- Layout de impressão para detalhes e orçamento.

---

> Observação: versões intermediárias e artefatos de teste permanecem disponíveis no histórico do Git, mesmo após a limpeza da raiz do repositório.
