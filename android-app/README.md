# InfoTech Android

Aplicativo Android nativo da InfoTech.io.

## O que este projeto resolve

- abre a InfoTech em um WebView próprio, sem barra ou notificações do Chrome;
- mantém login e sessão do site no armazenamento do aplicativo;
- usa somente HTTPS;
- bloqueia mixed content;
- mantém Safe Browsing ativo;
- abre links externos no aplicativo apropriado;
- suporta seleção de arquivos e downloads;
- inclui tela de erro/retry e splash da marca;
- usa o mesmo site e o mesmo Supabase, então atualizações do site entram no app sem duplicar regras de negócio.

## Build

O workflow `.github/workflows/android-app.yml` gera automaticamente um APK de teste instalável.

O APK de produção deve ser assinado com uma chave permanente antes de publicar na Play Store. Chaves de assinatura nunca devem ser commitadas neste repositório.
