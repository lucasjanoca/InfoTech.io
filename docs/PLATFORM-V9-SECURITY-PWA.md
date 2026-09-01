# InfoTech.io V9 — Plataforma, segurança e PWA

Data: 2026-09-01

## Implementado nesta versão

- Service Worker principal em `/sw.js`, com cache apenas para shell e conteúdo público.
- Exclusão explícita de login, cadastro, perfil, painéis, páginas administrativas, recuperação de senha e integrações Supabase do cache.
- Página offline sem dados pessoais.
- Manifest PWA ampliado para instalação em celular/desktop.
- Ciclo de atualização do Service Worker e evento de instalação integrado ao `v6-ui.js`.
- Receptor de Web Push no Service Worker, pronto para uso quando o backend de inscrições/VAPID for conectado.
- Validação administrativa considerando `role` e `is_blocked`.
- Cabeçalhos de defesa adicionais no baseline de edge.
- CI ampliado para validar JavaScript, PWA, manifest e regras de não-cache de páginas sensíveis.

## Princípios de segurança

1. Nenhum segredo administrativo no navegador.
2. A chave publishable do Supabase pode ficar no cliente; autorização real precisa ficar em RLS/policies/funções seguras.
3. Service Worker não deve persistir respostas autenticadas.
4. Área administrativa exige autorização no banco; proteção visual do frontend nunca é a única barreira.
5. Uploads devem ser validados no cliente e, quando possível, também no backend/storage policy.
6. Toda mudança de esquema deve ser seguida de advisors e testes de RLS.

## Backend ainda não aplicado nesta sessão

O frontend da InfoTech.io aponta para o projeto Supabase `rgngqumqzylthdiazvfu`, mas o projeto conectado nesta sessão tem outro ref. Por segurança, nenhuma alteração de banco foi aplicada no projeto incorreto.

Quando o projeto correto estiver disponível, a revisão deve cobrir:

- RLS de todas as tabelas expostas;
- políticas de ownership para cliente e políticas administrativas;
- `USING` + `WITH CHECK` em UPDATE;
- Storage policies do bucket de anexos;
- tabela de inscrições push e Edge Function para envio;
- trilha de auditoria de ações administrativas;
- revogação de permissões excessivas e revisão de funções `SECURITY DEFINER`;
- advisors de segurança e performance;
- testes de acesso cruzado entre usuários para prevenir IDOR/BOLA.

## Observação sobre notificações push

O Service Worker agora sabe receber e abrir notificações. O envio real depende de uma inscrição Push por dispositivo e de um backend autorizado para enviar a mensagem. A chave privada de envio nunca deve ficar no repositório ou no navegador.
