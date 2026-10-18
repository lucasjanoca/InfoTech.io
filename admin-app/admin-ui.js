/* Loaded ONLY by the independently deployed administrative site. */
(() => {
  'use strict';
  const $ = selector => document.querySelector(selector);
  const $$ = selector => [...document.querySelectorAll(selector)];
  if (!globalThis.makeId) globalThis.makeId = () => crypto.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  $$('[data-year]').forEach(node => { node.textContent = String(new Date().getFullYear()); });
  const toggle = $('.menu-mobile');
  const menu = $('#menu-principal');
  const close = () => { menu?.classList.remove('ativo'); toggle?.setAttribute('aria-expanded', 'false'); };
  toggle?.addEventListener('click', () => {
    const open = menu?.classList.toggle('ativo');
    toggle.setAttribute('aria-expanded', String(Boolean(open)));
  });
  document.addEventListener('keydown', event => { if (event.key === 'Escape') close(); });
  $$('#menu-principal a').forEach(link => link.addEventListener('click', close));
  const header = $('.site-header');
  const scrollHeader = () => header?.classList.toggle('scrolled', scrollY > 10);
  addEventListener('scroll', scrollHeader, { passive: true }); scrollHeader();

  const button = $('#admin-pwa-install');
  let deferredPrompt = null;
  const standalone = () => matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
  addEventListener('beforeinstallprompt', event => {
    if (standalone()) return;
    event.preventDefault();
    deferredPrompt = event;
    if (button) button.hidden = false;
  });
  button?.addEventListener('click', async () => {
    if (!deferredPrompt) return;
    const event = deferredPrompt;
    deferredPrompt = null;
    button.hidden = true;
    try {
      await event.prompt();
      await event.userChoice;
      // Only appinstalled confirms installation; accepting a prompt is not proof.
    } catch (error) { console.warn('Instalação ADM não disponível:', error); }
  });
  addEventListener('appinstalled', () => { deferredPrompt = null; if (button) button.hidden = true; });
  if (standalone() && button) button.hidden = true;
  if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost')) {
    addEventListener('load', () => {
      navigator.serviceWorker.register('/admin-sw.js', { scope: '/', updateViaCache: 'none' })
        .then(registration => registration.update().catch(() => {}))
        .catch(error => console.warn('Service worker ADM indisponível:', error));
    });
  }
})();
