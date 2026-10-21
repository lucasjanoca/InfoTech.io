# Revisão dos 17 itens — 20/10/2026

**Rascunho para revisão. Não publicar como conformidade concluída.** Implementação técnica e textos propostos não garantem ausência de processos, conformidade integral LGPD ou certificação WCAG. Continuam válidas as restrições de produção do PR #132.

## Matriz do pedido

| Item | Entrega / evidência | Situação |
|---|---|---|
| 1. Privacidade | Aviso ampliado: dados, finalidades, fornecedores, armazenamento, conservação e direitos | Preparado; identificar controlador e validar operação |
| 2. Termos | `termos.html`, vinculados ao cadastro e rodapé | Texto proposto; revisar contrato real |
| 3. Cookies | `cookies.html` e aviso informativo no rodapé, sem consentimento fictício | Frontend funcional; infraestrutura pendente |
| 4. Reembolso | `reembolso.html`: arrependimento, demais cancelamentos e atendimento | Preparado; validar processo operacional e canal público |
| 5. Formulários LGPD | Links junto ao cadastro e solicitação; ciência separada de publicidade; aviso contra dados sensíveis | Frontend; registro de versão/aceite no backend não implementado |
| 6. Dados necessários | Cadastro limitado a nome/e-mail/senha; orçamento e referência opcionais; teste impede novos campos pessoais sem revisão | Revisado no frontend; banco/retensão pendentes |
| 7. Tracking | Scripts ativos locais + biblioteca Supabase versionada no jsDelivr; teste de origens e assinaturas comuns de rastreadores | Nenhum tracker publicitário identificado; não certifica serviços externos |
| 8. Acessibilidade | Página explicativa, foco visível, redução de movimento, formulários e carrosséis sem autoplay | Parcial; leitor de tela e navegação visual pendentes |
| 9. Alt | Todas as imagens HTML da raiz têm atributo alt; duas descrições vazias são logotipos decorativos ao lado de texto | Verificação estática; adequação contextual ainda requer revisão visual |
| 10. Contraste | Placeholder #57708a substituído por #9fb3c9; bordas #7892ac; foco #67f3ff | Pares corrigidos medidos; não é auditoria de todas as telas |
| 11. Teclado | Abas com ArrowLeft/Right/Home/End, foco e ARIA; Escape no menu de conta; clones de links fora do Tab | Testes de abas aprovados; teste manual pendente |
| 12. Avaliações falsas | Nenhum bloco de avaliações/depoimentos ou schema AggregateRating encontrado nas páginas ativas | Não foram inventadas avaliações; conferir conteúdo futuro |
| 13. Promessas falsas | Removida linguagem absoluta selecionada; termos não prometem vendas, ranking ou ausência de falhas | Conferir alegações de portfólio e entregas comerciais |
| 14. Direitos de imagens | `IMAGE-RIGHTS-INVENTORY.md` lista arquivos, hash e usos | Pendente: evidência de autoria/licença e autorização de clientes |
| 15. Empresa | Página `informacoes-legais.html` com marca e links conhecidos | **Bloqueado:** razão/nome do prestador, cadastro e endereço não confirmados |
| 16. LGPD | Transparência e minimização no frontend; pendências discriminadas | **Não certificada:** depende de controles e práticas operacionais |
| 17. Outros riscos | Checklist abaixo | Revisão jurídica e operacional necessária |

## Bloqueadores antes de publicar

- Identificar se o prestador atua como pessoa física ou jurídica, nome/razão social, cadastro aplicável e endereço comercial que deve constar na oferta. Não usar dados pessoais da memória da conversa como cadastro empresarial público.
- Definir e testar e-mail ou outro canal público de atendimento/privacidade sem login. O contato atual depende da Área do Cliente e não atende adequadamente quem perdeu acesso ou não tem conta. Não inventar endereço de e-mail, CPF/CNPJ ou telefone.
- Confirmar autorização de uso de marcas, imagens e divulgação dos projetos do portfólio; substituir material sem autorização comprovada.
- Confirmar projeto Supabase, RLS, bucket privado, permissões administrativas, recuperação, exclusão/exportação e isolamento entre usuários. Não foram alterados.
- Documentar prazos efetivos de retenção por categoria, limpeza dos backups, fornecedores/suboperadores, região e mecanismo aplicável a transferências internacionais. Os textos não inventam prazos ou região.
- Revisar atendimento a titulares e consumidores: responsável, confirmação de recebimento, controle de prazos, exclusões legais, contestação e estorno. Uma página de política não executa esses processos.
- Revisar consentimento/aceite e registro de versões no servidor se necessário ao contrato. O checkbox do cadastro não é prova de consentimento para toda finalidade.
- Verificar cookies/scripts injetados pela hospedagem e serviços externos no ambiente publicado antes de afirmar que só há armazenamento funcional.
- Validar mobile/desktop, zoom, leitores de tela, foco e contraste em estados reais. Navegador local indisponível na sessão anterior; nenhuma certificação visual foi afirmada.
- Definir fluxo para menores, se o serviço vier a atendê-los, sem coletar data de nascimento de todos por conveniência.
- Revisar propostas, preços totais, prazos, encargos, garantias, mensalidades, licenças de software e autorização para manutenção/acesso a equipamentos. Nada foi inventado como condição contratual específica.

As novas páginas legais são network-only no Service Worker; nenhum conteúdo privado foi adicionado ao cache. A folha de acessibilidade foi incluída na lista de recursos públicos. O cache foi versionado novamente.

## Testes

24 verificadores Python; 22 testes Node; sintaxe JS; `git diff --check`. O novo teste estático valida imagens, links, campos e origens de scripts e mede três pares de cores, não a interface inteira. Os testes de abas exercitam o código real em DOM simulado. Testes não acessam usuários ou dados de produção. Resultados do GitHub Actions são separados dos testes locais.

## Fontes primárias consultadas

- LGPD: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm
- CDC: https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm
- Comércio eletrônico: https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2013/decreto/d7962.htm
- Direitos autorais: https://www.planalto.gov.br/ccivil_03/leis/l9610.htm
- Guia de cookies da ANPD: https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/guia-orientativo-cookies-e-protecao-de-dados-pessoais.pdf
- WCAG contraste: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
- WAI padrão de abas: https://www.w3.org/WAI/ARIA/apg/patterns/tabs/

## Rollback

Reverter este commit. Se houver publicação futura, incrementar novamente a versão do cache. Não há migração de banco nem mudança de DNS a desfazer.
