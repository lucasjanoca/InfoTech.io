(() => {
  'use strict';

  const ensureStyles = () => {
    if (document.querySelector('link[data-infotech-global-polish]')) return;
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'css/global-polish-v12.css?v=12.0';
    link.dataset.infotechGlobalPolish = 'true';
    document.head.appendChild(link);
  };

  const icon = () => {
    const wrap = document.createElement('span');
    wrap.className = 'header-person header-person-clean';
    wrap.setAttribute('aria-hidden', 'true');
    wrap.innerHTML = '<svg viewBox="0 0 24 24" width="27" height="27" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8" r="3.5"></circle><path d="M5.5 20c.7-4 3.2-6 6.5-6s5.8 2 6.5 6"></path></svg>';
    return wrap;
  };

  const normalize = () => {
    document.querySelectorAll('.header-person').forEach(current => {
      if (current.classList.contains('header-person-clean')) return;
      current.replaceWith(icon());
    });
  };

  ensureStyles();
  normalize();
  document.addEventListener('DOMContentLoaded', () => { ensureStyles(); normalize(); }, { once: true });
  window.addEventListener('infotech:auth-ready', normalize);

  const slot = document.querySelector('.account-slot');
  if (slot && 'MutationObserver' in window) {
    new MutationObserver(normalize).observe(slot, { childList: true, subtree: true });
  }
})();
