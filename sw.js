/* InfoTech.io — service worker principal
 * Cacheia somente shell/arquivos públicos explicitamente permitidos. Rotas
 * autenticadas, administrativas, desconhecidas, Supabase e requisições não-GET
 * nunca entram no cache.
 */
'use strict';

const VERSION = 'infotech-pwa-v9.6.2';
const STATIC_CACHE = `${VERSION}-static`;
const PAGE_CACHE = `${VERSION}-pages`;
const OFFLINE_URL = '/offline.html';

const NOTIFICATION_PATHS = new Set([
  '/',
  '/index.html',
  '/painel-cliente.html',
  '/perfil.html',
  '/nova-solicitacao.html',
  '/detalhes-solicitacao.html'
]);

const PUBLIC_NAVIGATION_PATHS = new Set([
  '/',
  '/index.html',
  '/servicos.html',
  '/solicitacoes.html',
  '/projetos.html',
  '/contato.html',
  '/sobre.html',
  '/privacidade.html',
  '/seguranca.html',
  '/offline.html'
]);

const APP_SHELL = [
  OFFLINE_URL,
  '/',
  '/index.html',
  '/servicos.html',
  '/solicitacoes.html',
  '/projetos.html',
  '/contato.html',
  '/sobre.html',
  '/privacidade.html',
  '/seguranca.html',
  '/manifest.webmanifest',
  '/assets/brand/logo-192.webp',
  '/assets/brand/logo-512.webp',
  '/assets/brand/logo.webp',
  '/assets/brand/projetos.webp',
  '/assets/projects/padoka-logo.svg',
  '/assets/projects/stoski-films-logo.svg',
  '/assets/projects/mundo-kids.svg',
  '/css/v6.css',
  '/css/mobile-fixes-v15.css',
  '/css/site-premium-v10.css',
  '/css/jss/v6-ui.js',
  '/css/jss/about-services-v13.js'
];

const PUBLIC_ASSET_PATHS = new Set([
  "/assets/brand/aplicativos.svg",
  "/assets/brand/automacao.svg",
  "/assets/brand/contatos.webp",
  "/assets/brand/logo-192.webp",
  "/assets/brand/logo-512.webp",
  "/assets/brand/logo.webp",
  "/assets/brand/programas.svg",
  "/assets/brand/projetos.webp",
  "/assets/brand/rass-logo.svg",
  "/assets/brand/servicos.webp",
  "/assets/brand/sistemas.webp",
  "/assets/brand/sites.webp",
  "/assets/brand/solicitacoes.svg",
  "/assets/brand/suporte.svg",
  "/assets/brand/svc-aplicativos.svg",
  "/assets/brand/svc-automacao.svg",
  "/assets/brand/svc-programas.svg",
  "/assets/brand/svc-servicos.svg",
  "/assets/brand/svc-sistemas.svg",
  "/assets/brand/svc-sites.svg",
  "/assets/brand/svc-suporte.svg",
  "/assets/projects/mundo-kids.svg",
  "/assets/projects/padoka-logo.svg",
  "/assets/projects/stoski-films-logo.svg",
  "/css/admin-dashboard-v471.css",
  "/css/attachments.css",
  "/css/auth.css",
  "/css/clientes-admin-v48.css",
  "/css/contato.css",
  "/css/dashboard-v41.css",
  "/css/dashboard-v510.css",
  "/css/email-confirmation-v11.css",
  "/css/global-polish-v12.css",
  "/css/google-oauth.css",
  "/css/home-premium.css",
  "/css/home.css",
  "/css/jss/about-services-v13.js",
  "/css/jss/activity-supabase.js",
  "/css/jss/admin-auth-supabase.js",
  "/css/jss/attachments-supabase.js",
  "/css/jss/dashboard-v510.js",
  "/css/jss/email-confirmation-v11.js",
  "/css/jss/google-oauth.js",
  "/css/jss/header-account-clean.js",
  "/css/jss/mfa-recovery.js",
  "/css/jss/notifications-supabase.js",
  "/css/jss/project-demo.js",
  "/css/jss/project-supabase.js",
  "/css/jss/refinement-v46.js",
  "/css/jss/requests-supabase.js",
  "/css/jss/script.js",
  "/css/jss/supabase-config.js",
  "/css/jss/v6-admin.js",
  "/css/jss/v6-app.js",
  "/css/jss/v6-ui.js",
  "/css/layout-tuning-v14.css",
  "/css/mobile-fixes-v15.css",
  "/css/mobile-fixes-v16.css",
  "/css/mobile-fixes-v17.css",
  "/css/mobile-fixes-v18.css",
  "/css/mobile-fixes-v19.css",
  "/css/paginas.css",
  "/css/project.css",
  "/css/projetos.css",
  "/css/refinement-v46.css",
  "/css/refinement-v472.css",
  "/css/request-tabs.css",
  "/css/responsivo.css",
  "/css/service-card-center-v11.css",
  "/css/servicos.css",
  "/css/site-premium-v10-states.css",
  "/css/site-premium-v10.css",
  "/css/sobre.css",
  "/css/style.css",
  "/css/v6-core.css",
  "/css/v6.css"
]);

const SENSITIVE_PATH = /\/(?:admin(?:-|\/)[^?#]*|(?:painel-(?:admin|cliente)|cliente-admin|clientes-admin|solicitacoes-antigas|login|cadastro|perfil|nova-solicitacao|detalhes-solicitacao|recuperar-senha|email-confirmado)(?:\.html)?)(?:$|[/?#])/i;

const isCacheableResponse = response => {
  if (!response || !response.ok || response.type === 'opaque' || response.redirected) return false;
  const cc = (response.headers.get('cache-control') || '').toLowerCase();
  return !cc.includes('no-store') && !cc.includes('private');
};

const isSensitive = url =>
  SENSITIVE_PATH.test(url.pathname) ||
  url.hostname.endsWith('.supabase.co') ||
  url.pathname.startsWith('/rest/v1/') ||
  url.pathname.startsWith('/auth/v1/') ||
  url.pathname.startsWith('/storage/v1/');

// Public URLs with query parameters (notably OAuth ?code=...) must never be
// intercepted or stored under a CacheStorage key containing sensitive values.
const isPublicNavigation = url =>
  url.origin === self.location.origin && !url.search && PUBLIC_NAVIGATION_PATHS.has(url.pathname);

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(STATIC_CACHE);

    for (const url of APP_SHELL) {
      try {
        const response = await fetch(new Request(url, {
          method: 'GET',
          cache: 'reload',
          credentials: 'same-origin'
        }));
        if (isCacheableResponse(response)) {
          await cache.put(url, response.clone());
        }
      } catch {}
    }

    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    if (self.registration.navigationPreload) {
      try { await self.registration.navigationPreload.enable(); } catch {}
    }

    const keys = await caches.keys();
    await Promise.all(
      keys
        .filter(key => key.startsWith('infotech-pwa-') && ![STATIC_CACHE, PAGE_CACHE].includes(key))
        .map(key => caches.delete(key))
    );

    await self.clients.claim();

    const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    await Promise.all(windows.map(async client => {
      try {
        const url = new URL(client.url);
        if (isPublicNavigation(url)) {
          await client.navigate(client.url);
        }
      } catch {}
    }));
  })());
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET' || request.headers.has('authorization')) return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin || isSensitive(url)) return;

  if (request.mode === 'navigate') {
    if (!isPublicNavigation(url)) return;

    event.respondWith((async () => {
      const cached = await (await caches.open(PAGE_CACHE)).match(request) ||
        await (await caches.open(STATIC_CACHE)).match(request);
      try {
        const preload = await event.preloadResponse;
        const fresh = preload || await fetch(new Request(request, { cache: 'no-cache' }));
        if (isCacheableResponse(fresh)) {
          const cache = await caches.open(PAGE_CACHE);
          try { await cache.put(request, fresh.clone()); } catch {}
        }
        return fresh;
      } catch {
        return cached || (await (await caches.open(STATIC_CACHE)).match(OFFLINE_URL)) || Response.error();
      }
    })());
    return;
  }

  if (!PUBLIC_ASSET_PATHS.has(url.pathname) && url.pathname !== '/manifest.webmanifest') return;
  // Only the existing numeric asset version query is eligible for caching.
  if (url.search && !/^\?v=\d+(?:\.\d+)*$/.test(url.search)) return;

  const destination = request.destination;
  if (!['style', 'script', 'image', 'font', 'manifest'].includes(destination)) return;

  if (['style', 'script', 'manifest'].includes(destination)) {
    event.respondWith((async () => {
      const cached = await (await caches.open(STATIC_CACHE)).match(request);
      try {
        const fresh = await fetch(new Request(request, { cache: 'no-cache' }));
        if (isCacheableResponse(fresh)) {
          const cache = await caches.open(STATIC_CACHE);
          try { await cache.put(request, fresh.clone()); } catch {}
        }
        return fresh;
      } catch {
        return cached || Response.error();
      }
    })());
    return;
  }

  event.respondWith((async () => {
    const cached = await (await caches.open(STATIC_CACHE)).match(request);
    const refresh = fetch(request)
      .then(async response => {
        if (isCacheableResponse(response)) {
          const cache = await caches.open(STATIC_CACHE);
          try { await cache.put(request, response.clone()); } catch {}
        }
        return response;
      })
      .catch(() => null);

    event.waitUntil(refresh.then(() => undefined));
    return cached || (await refresh) || Response.error();
  })());
});

self.addEventListener('message', event => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting();
  if (event.data?.type === 'CLEAR_PUBLIC_CACHE') {
    event.waitUntil(Promise.all([caches.delete(STATIC_CACHE), caches.delete(PAGE_CACHE)]));
  }
});

self.addEventListener('push', event => {
  let payload = {};
  try { payload = event.data?.json?.() || {}; } catch {
    payload = { body: event.data?.text?.() || '' };
  }

  const title = String(payload.title || 'InfoTech.io').slice(0, 80);
  const body = String(payload.body || 'Você tem uma nova atualização.').slice(0, 240);
  let url = '/painel-cliente.html';
  try {
    const target = new URL(payload.url || url, self.location.origin);
    if (target.origin === self.location.origin && NOTIFICATION_PATHS.has(target.pathname)) {
      url = target.pathname + target.search + target.hash;
    }
  } catch {}

  event.waitUntil(self.registration.showNotification(title, {
    body,
    icon: '/assets/brand/logo-192.webp',
    badge: '/assets/brand/logo-192.webp',
    data: { url },
    tag: String(payload.tag || 'infotech-update').slice(0, 80),
    renotify: Boolean(payload.renotify)
  }));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  let target = new URL('/painel-cliente.html', self.location.origin).href;
  try {
    const candidate = new URL(event.notification.data?.url || '/painel-cliente.html', self.location.origin);
    if (candidate.origin === self.location.origin && NOTIFICATION_PATHS.has(candidate.pathname)) {
      target = candidate.href;
    }
  } catch {}
  event.waitUntil((async () => {
    const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const client of windows) {
      if ('focus' in client) {
        await client.navigate(target);
        return client.focus();
      }
    }
    return self.clients.openWindow ? self.clients.openWindow(target) : undefined;
  })());
});