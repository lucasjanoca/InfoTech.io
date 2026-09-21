(() => {
  'use strict';
  const install = document.getElementById('install');
  const status = document.getElementById('status');
  const guidance = document.getElementById('install-guidance');
  let deferredPrompt = null;
  const standalone = () => matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
  const isIOS = () => /iphone|ipad|ipod/i.test(navigator.userAgent);
  if (standalone()) {
    location.replace('/admin-login.html');
    return;
  }
  const instructions = isIOS()
    ? 'No Safari do iPhone/iPad, toque em Compartilhar e escolha Adicionar à Tela de Início. Abra o ícone InfoTech ADM criado.'
    : 'Se o botão não aparecer, abra o menu do navegador e procure Instalar aplicativo ou Adicionar à tela inicial. Este navegador pode não oferecer instalação PWA.';
  if (guidance) guidance.textContent = instructions;
  if (status) status.textContent = 'Use a instalação do navegador. A administração exige login e MFA.';
  addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    deferredPrompt = event;
    if (install) install.hidden = false;
    if (status) status.textContent = 'O navegador disponibilizou a instalação do InfoTech ADM.';
  });
  install?.addEventListener('click', async () => {
    if (!deferredPrompt) return;
    const event = deferredPrompt;
    deferredPrompt = null;
    install.hidden = true;
    try {
      await event.prompt();
      const result = await event.userChoice;
      if (status) status.textContent = result?.outcome === 'accepted'
        ? 'Solicitação aceita. Aguarde o navegador confirmar a instalação.'
        : 'Instalação cancelada. Você também pode usar o menu do navegador.';
    } catch (error) {
      console.warn('Falha ao solicitar instalação ADM:', error);
      if (status) status.textContent = 'O navegador não abriu a instalação. Use as instruções abaixo.';
    }
  });
  addEventListener('appinstalled', () => {
    deferredPrompt = null;
    if (install) install.hidden = true;
    if (status) status.textContent = 'Instalação do InfoTech ADM confirmada pelo navegador.';
  });
  if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost')) {
    addEventListener('load', () => navigator.serviceWorker.register('/admin-sw.js', {
      scope: '/', updateViaCache: 'none'
    }).catch(error => { console.warn('Service worker ADM indisponível:', error); }));
  }
})();
