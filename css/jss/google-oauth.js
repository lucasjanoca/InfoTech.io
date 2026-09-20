(() => {
  'use strict';

  const button = document.querySelector('[data-google-auth]');
  if (!button) return;

  const container = button.closest('[data-google-auth-container]');
  const status = document.querySelector('[data-google-auth-status]');
  const cfg = window.INFOTECH_SUPABASE_CONFIG || {};
  const setStatus = text => { if (status) status.textContent = text; };
  const allowed = new Set(['painel-cliente.html', 'nova-solicitacao.html', 'perfil.html']);
  const unavailable = 'O acesso com Google está temporariamente indisponível. Entre com e-mail e senha.';

  function safeLocalSet(key, value) {
    try {
      localStorage.setItem(key, value);
      return true;
    } catch (_) {
      return false;
    }
  }

  function safeDestination(raw) {
    if (!raw) return 'painel-cliente.html';
    try {
      const url = new URL(raw, location.href);
      if (url.origin !== location.origin) return 'painel-cliente.html';
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
    if (/provider.*not enabled|unsupported provider|provider is disabled/i.test(message)) return unavailable;
    if (/redirect.*(not allowed|invalid|mismatch)|redirect_uri_mismatch/i.test(message)) {
      return 'O acesso pelo Google está com um endereço de retorno incorreto. Entre com e-mail e senha por enquanto.';
    }
    return 'Não foi possível iniciar o acesso pelo Google. Tente novamente ou entre com e-mail e senha.';
  }

  async function providerReady() {
    if (!cfg.url || !cfg.publishableKey) return false;
    try {
      const response = await fetch(`${cfg.url}/auth/v1/settings`, {
        method: 'GET',
        headers: { apikey: cfg.publishableKey },
        cache: 'no-store'
      });
      if (!response.ok) return false;
      const settings = await response.json();
      return settings?.external?.google === true;
    } catch (error) {
      console.warn('Não foi possível verificar o provedor Google:', error);
      return false;
    }
  }

  async function init() {
    if (container) container.hidden = false;
    button.hidden = false;
    button.disabled = true;
    setStatus('Verificando disponibilidade do Google...');

    if (!cfg.url || !cfg.publishableKey || !window.supabase?.createClient) {
      setStatus(unavailable);
      return;
    }

    const db = window.infotechSupabase || window.supabase.createClient(cfg.url, cfg.publishableKey, {
      auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true,
        flowType: 'pkce', storageKey: 'infotech-auth-v8' }
    });
    window.infotechSupabase = db;

    const params = new URLSearchParams(location.search);
    if (params.has('error')) {
      setStatus(errorMessage({ message: params.get('error_description') || params.get('error') }));
    }

    const enabled = await providerReady();
    button.disabled = !enabled;
    if (!enabled) {
      setStatus(unavailable);
      return;
    }
    if (!params.has('error')) setStatus('');

    button.addEventListener('click', async () => {
      if (button.disabled) return;
      button.disabled = true;
      setStatus('Abrindo o acesso pelo Google...');
      try {
        // Revalida antes do redirecionamento para evitar mostrar JSON do Supabase.
        if (!(await providerReady())) {
          setStatus(unavailable);
          return;
        }
        const destination = safeDestination(params.get('destino'));
        // Estado de navegação é apenas conveniência de UX; storage bloqueado não deve impedir o OAuth.
        safeLocalSet('infotech:after-confirm', destination);
        const redirectTo = new URL('login.html', location.href).href;
        const { error } = await db.auth.signInWithOAuth({
          provider: 'google',
          options: { redirectTo }
        });
        if (error) throw error;
      } catch (error) {
        console.error('Falha ao iniciar acesso com Google:', error);
        setStatus(errorMessage(error));
      } finally {
        button.disabled = !(await providerReady());
      }
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
