/* InfoTech.io — service worker principal
 * Cacheia somente shell/arquivos públicos. Rotas autenticadas, administrativas,
 * Supabase e requisições não-GET nunca entram no cache.
 */
'use strict';

const VERSION = 'infotech-pwa-v9.0.0';
const STATIC_CACHE = `${VERSION}-static`;
const PAGE_CACHE = `${VERSION}-pages`;
const OFFLINE_URL = '/offline.html';

const APP_SHELL = [
  OFFLINE_URL,
  '/manifest.webmanifest',
  '/assets/brand/logo-192.webp',
  '/assets/brand/logo-512.webp',
  '/css/v6.css?v=8.0'
];

const SENSITIVE_PATH = /\/(?:admin(?:-|\/)|painel-(?:admin|cliente)|cliente-admin|clientes-admin|login|cadastro|perfil|nova-solicitacao|detalhes-solicitacao|recuperar-senha|email-confirmado)(?:\.html)?(?:$|[/?#])/i;

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
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(key => key.startsWith('infotech-pwa-') && ![STATIC_CACHE, PAGE_CACHE].includes(key))
          .map(key => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin || isSensitive(url)) return;

  if (request.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        const fresh = await fetch(request);
        if (isCacheableResponse(fresh)) {
          const cache = await caches.open(PAGE_CACHE);
          await cache.put(request, fresh.clone());
        }
        return fresh;
      } catch {
        return (await caches.match(request)) || (await caches.match(OFFLINE_URL));
      }
    })());
    return;
  }

  const destination = request.destination;
  if (!['style', 'script', 'image', 'font', 'manifest'].includes(destination)) return;

  event.respondWith((async () => {
    const cached = await caches.match(request);
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
    if (target.origin === self.location.origin) url = target.pathname + target.search + target.hash;
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
