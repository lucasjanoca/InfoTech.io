const assert = require('node:assert/strict');
const fs = require('node:fs');
const test = require('node:test');
const vm = require('node:vm');

const uiSource = fs.readFileSync('css/jss/v6-ui.js', 'utf8');
const pwaStart = uiSource.indexOf('/* INFOTECH_PWA_V9_5');
const pwaEnd = uiSource.indexOf('/* INFOTECH_APP_INSTANT_NAV', pwaStart);
const pwaSource = uiSource.slice(pwaStart, pwaEnd);

function createStorage() {
  const values = new Map();
  return {
    getItem: key => values.has(key) ? values.get(key) : null,
    setItem: (key, value) => values.set(key, String(value)),
    removeItem: key => values.delete(key)
  };
}

function createPage(sessionStorage) {
  let currentBanner = null;

  const node = tag => ({
    tagName: tag.toUpperCase(),
    dataset: {},
    listeners: {},
    textContent: '',
    hidden: true,
    setAttribute(name, value) { this[name] = value; },
    addEventListener(name, handler) { this.listeners[name] = handler; },
    append() {},
    click() { this.listeners.click?.({ preventDefault() {} }); },
    remove() { if (currentBanner === this) currentBanner = null; }
  });

  const footer = node('span');
  footer.append = (...items) => {
    footer.installLink = items.find(item => typeof item === 'object') || null;
  };
  const document = {
    readyState: 'complete',
    body: {
      appendChild(element) {
        currentBanner = element;
      }
    },
    querySelector(selector) {
      if (selector === '[data-pwa-banner]') return currentBanner;
      if (selector === '.footer-legal-links') return footer;
      return null;
    },
    createElement(tag) {
      const element = node(tag);
      if (tag !== 'aside') return element;

      const close = node('button');
      const action = node('button');
      const instructions = node('p');
      element.querySelector = selector => ({
        '.pwa-install-close': close,
        '[data-pwa-action]': action,
        '[data-pwa-instructions]': instructions,
        '[data-pwa-help]': node('span')
      })[selector] || null;
      element.controls = { close, action, instructions };
      return element;
    }
  };

  const listeners = {};
  const navigator = { userAgent: '', standalone: false };
  const window = {
    navigator,
    matchMedia: () => ({ matches: false }),
    addEventListener(name, handler) { listeners[name] = handler; },
    dispatchEvent() {}
  };

  const context = vm.createContext({
    console,
    document,
    location: { pathname: '/projetos.html', protocol: 'https:', hostname: 'infotech-io.com.br' },
    navigator,
    sessionStorage,
    window
  });

  vm.runInContext(pwaSource, context);
  return { footer, getBanner: () => currentBanner };
}

test('fechar o banner PWA mantém o aviso oculto durante a sessão', () => {
  const storage = createStorage();
  const firstPage = createPage(storage);
  assert.ok(firstPage.getBanner(), 'o aviso deve aparecer na primeira visita');

  firstPage.getBanner().controls.close.click();
  assert.equal(firstPage.getBanner(), null);
  assert.equal(storage.getItem('infotech:pwa-banner-dismissed'), '1');

  const nextPage = createPage(storage);
  assert.equal(nextPage.getBanner(), null, 'o aviso fechado não deve reaparecer após navegar');

  nextPage.footer.installLink.click();
  assert.ok(nextPage.getBanner(), 'o link do rodapé deve reabrir o aviso sob pedido');
  assert.equal(storage.getItem('infotech:pwa-banner-dismissed'), null);
});

test('o portfólio usa duas colunas e texto legível em celular estreito', () => {
  const css = fs.readFileSync('css/mobile-fixes-v19.css', 'utf8');
  const start = css.indexOf('/* Portfólio: evita cartões');
  const mobilePortfolio = css.slice(start, start + 1000);

  assert.ok(start >= 0, 'o ajuste responsivo do portfólio deve existir');
  assert.match(mobilePortfolio, /@media\(max-width:480px\)/);
  assert.match(mobilePortfolio, /\.project-mini-grid\s*\{[^}]*grid-template-columns:repeat\(2,minmax\(0,1fr\)\)/s);
  assert.match(mobilePortfolio, /\.project-mini-card small\s*\{[^}]*font-size:\.72rem/s);
  assert.match(mobilePortfolio, /\.project-mini-card \.mini-status\s*\{[^}]*font-size:\.62rem/s);
});
