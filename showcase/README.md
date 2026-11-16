# InfoTech.io — Vitrine de Projetos (V1)

Este diretório contém uma nova experiência pública **isolada e reversível**, criada para avaliar a substituição futura das páginas institucionais por um portfólio de projetos. O site principal, a área do cliente, a administração, o PWA e o banco de dados **não foram removidos nem alterados**.

## Arquitetura limpa
- `index.html`: marcação semântica, navegação, seções e diálogo nativo.
- `styles.css`: identidade preta/azul, miniaturas editoriais em CSS, layouts mobile/desktop, foco e redução de movimento.
- `app.js`: renderização do catálogo, busca com normalização, filtros, detalhes e navegação.
- `projects.json`: fonte única dos projetos públicos, com status, descrição, tecnologias e links.

Sem framework, build, autenticação, Supabase, armazenamento local, rastreamento ou service worker. Os cartões utilizam **visuais conceituais (não capturas de tela)** para evitar atribuir falsamente telas a sites reais. Não publica código de repositórios privados ou dados de usuários.

## Executar localmente
```sh
cd showcase
python3 -m http.server 8080
# abrir http://localhost:8080/
```

Atenção: abrir `index.html` via `file://` pode bloquear o `fetch` do JSON.

## Checklist de aceitação
1. Verificar carregamento dos 10 cases, links e estados.
2. Usar categorias e busca ("rass", "estetica", "catálogo").
3. Abrir detalhes de um case, navegar pelo teclado, pressionar Escape.
4. Testar o menu e o grid em 360 px, 390 px, 768 px e desktop.
5. Testar prefers-reduced-motion e navegação com zoom de 200%.
6. Confirmar consentimento para marcas, conteúdos e descrições dos clientes.
7. Rever site, domínio, contato, política de privacidade e LGPD antes de lançar.
8. Medir Core Web Vitals em dispositivos reais (LCP, INP, CLS).
9. Atualizar `robots`/canonical apenas após aprovar produção.

## Implantação de teste
O preview pode ser servido por um Worker Cloudflare dedicado. **Não** publicar direto na branch `main`, nem modificar `CNAME`, DNS ou Supabase sem revisão. Arquivos do showcase devem ser publicados num origin próprio, com `robots: noindex, nofollow`.

## Próxima migração segura
Uma migração real exigirá estratégia separada para o domínio principal e os fluxos antigos: preservar a rota `/cliente` / autenticação ativa e administração em ambiente próprio antes de trocar a landing page; testar redirecionamentos, service worker, cache, sitemap, e os PRs antigos ainda abertos. Esta V1 não remove código legado.
