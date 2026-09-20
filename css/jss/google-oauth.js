(() => {
  'use strict';

  const button = document.querySelector('[data-google-auth]');
  if (!button) return;

  const container = button.closest('[data-google-auth-container]');
  const status = document.querySelector('[data-google-auth-status]');
  const cfg = window.INFOTECH_SUPABASE_CONFIG || {};
  const setStatus = text => { if (status) status.textContent = text; };
  const allowed = new Set(['painel-cliente.html', 'nova-solicitacao.html', 'perfil.html']);

  function safeDestination(raw) {
    if (!raw) return 'painel-cliente.html';
    try {
      const url = new URL(raw, location.href);
      const file = url.pathname.split('/').pop();
      if (!allowed.has(file)) return 'painel-cliente.html';
      if (file === 'nova-solicitacao.html') {
        const service = String(url.searchParams.get('servico') || '').trim().slice(0, 80);
        return service ? `${file}?servico=${encodeURIComponent(service)}` : file;
      }
      return file;
    } catch (_) {
      return 'painel-cliente.html';
    }
  }

  function errorMessage(error) {
    const message = String(error?.message || '');
    if (/provider.*not enabled|unsupported provider|provider is disabled/i.test(message)) {
      return 'O Google ainda não está habilitado no projeto Supabase da InfoTech.io. O projeto da Padoka é separado.';
    }
    if (/redirect.*(not allowed|invalid|mismatch)|redirect_uri_mismatch/i.test(message)) {
      return 'O endereço de retorno da InfoTech.io não está autorizado na configuração de login do Supabase/Google.';
    }
    return 'Não foi possível iniciar o acesso pelo Google. Confira sua conexão ou tente novamente.';
  }

  function init() {
    // Não esconda o botão caso /auth/v1/settings demore, falhe ou seja bloqueado.
    // A autoridade real é o Supabase, que valida o provedor na tentativa de OAuth.
    if (container) container.hidden = false;
    button.hidden = false;
    if (!cfg.url || !cfg.publishableKey || !window.supabase?.createClient) {
      button.disabled = true;
      setStatus('O login está temporariamente indisponível. Atualize a página e tente novamente.');
      return;
    }

    const db = window.infotechSupabase || window.supabase.createClient(cfg.url, cfg.publishableKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
        flowType: 'pkce',
        storageKey: 'infotech-auth-v8'
      }
    });
    window.infotechSupabase = db;

    const params = new URLSearchParams(location.search);
    if (params.has('error')) {
      const description = params.get('error_description') || params.get('error') || '';
      setStatus(errorMessage({ message: description }));
    }

    button.addEventListener('click', async () => {
      if (button.disabled) return;
      button.disabled = true;
      setStatus('Abrindo o acesso pelo Google...');
      try {
        const destination = safeDestination(params.get('destino'));
        localStorage.setItem('infotech:after-confirm', destination);
        const redirectTo = new URL('login.html', location.href).href;
        const { error } = await db.auth.signInWithOAuth({
          provider: 'google',
          options: { redirectTo }
        });
        if (error) throw error;
      } catch (error) {
        console.error('Falha ao iniciar acesso com Google:', error);
        setStatus(errorMessage(error));
        button.disabled = false;
      }
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
