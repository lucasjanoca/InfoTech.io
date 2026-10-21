/* Public portfolio: no authentication SDK or automatic installation prompts. */
(() => {
  'use strict';
  document.querySelector('[data-print-profile]')?.addEventListener('click', () => window.print());
  if ('serviceWorker' in navigator && (location.protocol === 'https:' || ['localhost', '127.0.0.1'].includes(location.hostname))) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js', {scope:'/', updateViaCache:'none'}).catch(() => {});
    }, {once:true});
  }
})();
