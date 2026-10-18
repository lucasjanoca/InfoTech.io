/* Installed ONLY at the admin origin. Private pages, API and auth responses are never cached. */
'use strict';
const PREFIX = 'infotech-adm-';
const STATIC = `${PREFIX}static-v1`;
// These are the ONLY responses allowed in Cache Storage, regardless of the
// site's conservative global HTTP no-store header. No HTML, profiles, session,
// requests, auth, Supabase responses or configuration files are in this list.
const ALLOWED = new Set([
  '/admin-manifest.webmanifest',
  '/icons/admin-192.png',
  '/icons/admin-512.png',
  '/css/admin-app.css',
  '/css/jss/admin-ui.js',
  '/css/jss/admin-install.js'
]);
self.addEventListener('install', event => {
  event.waitUntil(self.skipWaiting());
});
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names.filter(name => name.startsWith(PREFIX) && name !== STATIC).map(name => caches.delete(name)));
    await self.clients.claim();
  })());
});
self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET' || request.mode === 'navigate') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin || !ALLOWED.has(url.pathname)) return;
  event.respondWith((async () => {
    try {
      const response = await fetch(request);
      // Explicit static allowlist above is the security boundary, not HTTP
      // cache headers used by the CDN. These assets contain no user data.
      if (response.ok && response.type !== 'opaque') {
        const cache = await caches.open(STATIC);
        await cache.put(request, response.clone());
      }
      return response;
    } catch (error) {
      return (await caches.match(request)) || Response.error();
    }
  })());
});
self.addEventListener('message', event => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting();
  if (event.data?.type === 'CLEAR_ADMIN_CACHE') event.waitUntil(caches.delete(STATIC));
});
