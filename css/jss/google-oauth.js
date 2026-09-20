(() => {
  'use strict';

  const button = document.querySelector('[data-google-auth]');
  if (!button) return;

  const container = button.closest('[data-google-auth-container]');
  const status = document.querySelector('[data-google-auth-status]');
  const cfg = window.INFOTECH_SUPABASE_CONFIG || {};
  const setStatus = (text) => { if (status) status.textContent = text; };
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

  async function init() {
    if (!cfg.url || !cfg.publishableKey || !window.supabase?.createClient) return;

    // Exibe a opção somente quando o provedor está de fato habilitado no Supabase.
    try {
      const res = await fetch(`${cfg.url}/auth/v1/settings`, {
        headers: { apikey: cfg.publishableKey },
        cache: 'no-store'
      });
      if (!res.ok) return;
      const settings = await res.json();
      if (settings?.external?.google !== true) return;
    } catch (_) {
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
    if (container) container.hidden = false;
    button.hidden = false;

    if (new URLSearchParams(location.search).has('error')) {
      setStatus('O acesso pelo Google não foi concluído. Tente novamente ou entre com e-mail e senha.');
    }

    button.addEventListener('click', async () => {
      if (button.disabled) return;
      button.disabled = true;
      setStatus('Abrindo o acesso pelo Google...');
      try {
        const destination = safeDestination(new URLSearchParams(location.search).get('destino'));
        localStorage.setItem('infotech:after-confirm', destination);
        // Um callback fixo facilita a configuração da lista de redirecionamentos.
        const redirectTo = new URL('login.html', location.href).href;
        const { error } = await db.auth.signInWithOAuth({
          provider: 'google',
          options: { redirectTo }
        });
        if (error) throw error;
      } catch (error) {
        console.error('Falha ao iniciar acesso com Google:', error);
        setStatus('Não foi possível abrir o acesso pelo Google. Tente novamente ou entre com e-mail e senha.');
        button.disabled = false;
      }
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
