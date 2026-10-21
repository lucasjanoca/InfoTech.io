# Portfólio Lucas Janoca

## Objetivo e implementação

Reposicionar as quatro páginas públicas (início, projetos, sobre e contato) como portfólio pessoal de Lucas Janoca. A InfoTech permanece como marca e projeto, com a identidade escura e azul preservada. O acesso à Área do Cliente continua disponível no rodapé e no contato.

O novo CSS tem layouts para desktop e celular, navegação sempre visível, foco acessível e versão de impressão do perfil. O JavaScript público registra o PWA e abre a impressão; não carrega SDK de autenticação nem solicita instalação automaticamente. O cache recebe nova versão e os dois recursos públicos novos. Manifestos e rotas autenticadas permanecem separados.

Projetos e formação foram reaproveitados do conteúdo existente. Não foram acrescentados números de resultados, depoimentos, empregadores ou certificações. O monograma LJ evita atribuir uma foto fictícia ao titular. Confirmar conteúdo biográfico, endereço do LinkedIn e participação/autorização de cada projeto antes da publicação.

## Validação

- 24 verificadores Python aprovados.
- 22 testes Node aprovados.
- Sintaxe do novo JavaScript e git diff --check aprovados.
- Links locais e fragmentos das quatro páginas conferidos.
- Sem navegador executável disponível: avaliação visual, impressão efetiva e interação em dispositivos permanecem pendentes. Não houve validação de sessão real ou banco.
- Disponibilidade de destinos externos não certificada.

## Revisão manual antes de publicar

Abrir as quatro páginas em celular e desktop; conferir sobreposição, foco e navegação por teclado, projetos, contato, impressão do perfil e acesso à Área do Cliente. Validar atualização do service worker para visitantes com cache antigo. Confirmar texto e dados pessoais com Lucas.

As pendências jurídicas e de direitos de imagem dos relatórios anteriores continuam aplicáveis. Esta mudança não certifica conformidade jurídica ou acessibilidade integral.

## Reversão

Reverter o commit do portfólio; em eventual reversão após publicação autorizada, incrementar a versão do service worker para invalidar os recursos anteriores. Não há migração de banco nem alteração de domínio. O trabalho fica na branch de revisão e no PR; não autoriza merge ou deploy.
