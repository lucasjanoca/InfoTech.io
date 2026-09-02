/* InfoTech.io — service worker principal
 * Cacheia somente shell/arquivos públicos. Rotas autenticadas, administrativas,
 * Supabase e requisições não-GET nunca entram no cache.
 */
'use strict';

const VERSION = 'infotech-pwa-v9.4.1';
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
  '/css/site-premium-v10.css',
  '/css/jss/v6-ui.js'
];

const SENSITIVE_PATH = /\/(?:admin(?:-|\/)|painel-(?:admin|cliente)|cliente-admin|clientes-admin|solicitacoes-antigas|login|cadastro|perfil|nova-solicitacao|detalhes-solicitacao|recuperar-senha|email-confirmado)(?:\.html)?(?:$|[/?#])/i;

const isCacheableResponse = response => {
  if (!response || !response.ok || response.type === 'opaque') return false;
  const cc = (response.headers.get('cache-control') || '').toLowerCase();
  return !cc.includes('no-store') && !cc.includes('private');
};

const isSensitive = url =>
  SENSITIVE_PATH.test(url.pathname) ||
  url.hostname.endsWith('.supabase.co') ||
  url.pathname.startsWith('/rest/v1/') ||
  url.pathname.startsWith('/auth/v1/') ||
  url.pathname.startsWith('/storage/v1/');

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

    const safeRefresh = /\/(?:|index|servicos|solicitacoes|projetos|contato|sobre|privacidade|seguranca)\.html$/i;
    const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });

    await Promise.all(windows.map(async client => {
      try {
        const url = new URL(client.url);
        const pathname = url.pathname === '/' ? '/index.html' : url.pathname;
        if (url.origin === self.location.origin && safeRefresh.test(pathname)) {
          await client.navigate(client.url);
        }
      } catch {}
    }));
  })());
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin || isSensitive(url)) return;

  if (request.mode === 'navigate') {
    event.respondWith((async () => {
      const cached = await caches.match(request, { ignoreSearch: true });

      const refresh = (async () => {
        try {
          const preload = await event.preloadResponse;
          const fresh = preload || await fetch(new Request(request, { cache: 'no-cache' }));
          if (isCacheableResponse(fresh)) {
            const cache = await caches.open(PAGE_CACHE);
            await cache.put(request, fresh.clone());
          }
          return fresh;
        } catch {
          return null;
        }
      })();

      event.waitUntil(refresh.then(() => undefined));

      if (cached) return cached;

      const fresh = await refresh;
      return fresh || (await caches.match(OFFLINE_URL));
    })());
    return;
  }

  const destination = request.destination;
  if (!['style', 'script', 'image', 'font', 'manifest'].includes(destination)) return;

  event.respondWith((async () => {
    const cached = await caches.match(request, { ignoreSearch: true });
    const refresh = fetch(request)
      .then(async response => {
        if (isCacheableResponse(response)) {
          const cache = await caches.open(STATIC_CACHE);
          await cache.put(request, response.clone());
        }
        return response;
      })
      .catch(() => null);

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
  const target = new URL(event.notification.data?.url || '/', self.location.origin).href;
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
