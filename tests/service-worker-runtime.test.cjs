'use strict';

// Exercita o Service Worker real em uma sandbox Node, sem navegador, rede,
// Supabase ou credenciais. Cada caso recebe caches e listeners isolados.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const ORIGIN = 'https://infotech-io.com.br';
const workerSource = fs.readFileSync(path.join(__dirname, '..', 'sw.js'), 'utf8');

function makeWorker() {
  const handlers = new Map();
  const buckets = new Map();
  const requests = [];
  let network = async () => new FakeResponse('online');

  class FakeResponse {
    constructor(body, { ok = true, type = 'basic', cacheControl = '' } = {}) {
      this.body = body;
      this.ok = ok;
      this.type = type;
      this.cacheControl = cacheControl;
      this.headers = {
        get: name => name.toLowerCase() === 'cache-control' ? cacheControl : null
      };
    }
    clone() {
      return new FakeResponse(this.body, {
        ok: this.ok, type: this.type, cacheControl: this.cacheControl
      });
    }
    static error() {
      return new FakeResponse('', { ok: false, type: 'error' });
    }
  }

  class FakeRequest {
    constructor(input, options = {}) {
      this.url = new URL(typeof input === 'string' ? input : input.url, ORIGIN).href;
      this.method = options.method || (typeof input === 'string' ? 'GET' : input.method);
      this.mode = options.mode || (typeof input === 'string' ? 'cors' : input.mode);
      this.destination = options.destination || (typeof input === 'string' ? '' : input.destination);
    }
  }

  const cacheKey = request => new URL(typeof request === 'string' ? request : request.url, ORIGIN).href;
  const caches = {
    async open(name) {
      if (!buckets.has(name)) buckets.set(name, new Map());
      const entries = buckets.get(name);
      return {
        async put(request, response) {
          entries.set(cacheKey(request), response.clone());
        }
      };
    },
    async match(request, options = {}) {
      const target = cacheKey(request);
      for (const entries of buckets.values()) {
        for (const [key, response] of entries) {
          const samePath = options.ignoreSearch &&
            new URL(key).origin === new URL(target).origin &&
            new URL(key).pathname === new URL(target).pathname;
          if (key === target || samePath) return response.clone();
        }
      }
      return undefined;
    },
    async keys() {
      return [...buckets.keys()];
    },
    async delete(name) {
      return buckets.delete(name);
    }
  };

  const self = {
    location: { origin: ORIGIN },
    addEventListener(name, fn) { handlers.set(name, fn); },
    skipWaiting: async () => {},
    clients: { claim: async () => {}, matchAll: async () => [] },
    registration: { navigationPreload: null }
  };

  vm.runInNewContext(workerSource, {
    URL, Request: FakeRequest, Response: FakeResponse, self, caches,
    fetch: async request => {
      requests.push(cacheKey(request));
      return network(request);
    },
    console, Promise, Set
  }, { filename: 'sw.js', timeout: 1000 });

  async function dispatch(url, { method = 'GET', mode = 'navigate', destination = 'document' } = {}) {
    let responsePromise = null;
    const waiters = [];
    handlers.get('fetch')({
      request: new FakeRequest(url, { method, mode, destination }),
      preloadResponse: Promise.resolve(undefined),
      respondWith(promise) { responsePromise = Promise.resolve(promise); },
      waitUntil(promise) { waiters.push(promise); }
    });
    const intercepted = responsePromise !== null;
    const response = intercepted ? await responsePromise : undefined;
    await Promise.all(waiters);
    return { intercepted, response };
  }

  return {
    dispatch,
    setNetwork(handler) { network = handler; },
    cachedUrls() {
      return [...buckets.values()].flatMap(entries => [...entries.keys()]);
    },
    requests,
    FakeResponse
  };
}

test('navegação pública sem query mantém resposta e fallback offline', async () => {
  const sw = makeWorker();
  const online = await sw.dispatch('/index.html');
  assert.equal(online.intercepted, true);
  assert.equal(online.response.body, 'online');
  assert.deepEqual(sw.cachedUrls(), [ORIGIN + '/index.html']);

  sw.setNetwork(async () => { throw new Error('offline'); });
  const offline = await sw.dispatch('/index.html');
  assert.equal(offline.intercepted, true);
  assert.equal(offline.response.body, 'online');
});

test('OAuth e demais queries públicas não passam pelo cache do Service Worker', async () => {
  const sw = makeWorker();
  for (const route of [
    '/?code=temporary-oauth-code',
    '/index.html?code=temporary-oauth-code&state=state-token',
    '/index.html?error_description=sensitive-description',
    '/servicos.html?utm_campaign=marketing',
    '/?next=%2Fperfil.html'
  ]) {
    const result = await sw.dispatch(route);
    assert.equal(result.intercepted, false, 'Deveria ignorar: ' + route);
  }
  assert.deepEqual(sw.cachedUrls(), []);
  assert.deepEqual(sw.requests, []);
});

test('login, conta, recuperação e páginas administrativas não são interceptadas', async () => {
  const sw = makeWorker();
  for (const route of [
    '/login.html?code=oauth',
    '/cadastro.html',
    '/perfil.html',
    '/painel-cliente.html',
    '/painel-admin.html',
    '/admin-login.html',
    '/admin-seguranca.html',
    '/admin/configuracao',
    '/recuperar-senha.html',
    '/detalhes-solicitacao.html'
  ]) {
    assert.equal((await sw.dispatch(route)).intercepted, false, route);
  }
  assert.deepEqual(sw.cachedUrls(), []);
});

test('origem externa, Supabase e rotas de API não são interceptadas', async () => {
  const sw = makeWorker();
  for (const route of [
    'https://outro-site.example/index.html',
    'https://exemplo.supabase.co/auth/v1/token',
    ORIGIN + '/auth/v1/callback',
    ORIGIN + '/rest/v1/profiles',
    ORIGIN + '/storage/v1/object'
  ]) {
    assert.equal((await sw.dispatch(route)).intercepted, false, route);
  }
});

test('requisições POST e navegações desconhecidas ficam fora do cache', async () => {
  const sw = makeWorker();
  assert.equal((await sw.dispatch('/', { method: 'POST' })).intercepted, false);
  assert.equal((await sw.dispatch('/rota-nao-listada.html')).intercepted, false);
  assert.deepEqual(sw.cachedUrls(), []);
});

test('respostas privadas e no-store nunca são persistidas', async () => {
  for (const cacheControl of ['private, max-age=0', 'no-store']) {
    const sw = makeWorker();
    sw.setNetwork(async () => new sw.FakeResponse('confidencial', { cacheControl }));
    const { intercepted, response } = await sw.dispatch('/index.html');
    assert.equal(intercepted, true);
    assert.equal(response.body, 'confidencial');
    assert.deepEqual(sw.cachedUrls(), [], cacheControl);
  }
});

test('scripts públicos podem usar cache estático', async () => {
  const sw = makeWorker();
  const result = await sw.dispatch('/css/jss/v6-ui.js', { mode: 'cors', destination: 'script' });
  assert.equal(result.intercepted, true);
  assert.deepEqual(sw.cachedUrls(), [ORIGIN + '/css/jss/v6-ui.js']);
});

test('response opaca ou HTTP com erro não entra no cache', async () => {
  for (const options of [{ type: 'opaque' }, { ok: false }]) {
    const sw = makeWorker();
    sw.setNetwork(async () => new sw.FakeResponse('erro', options));
    const { intercepted } = await sw.dispatch('/index.html');
    assert.equal(intercepted, true);
    assert.deepEqual(sw.cachedUrls(), []);
  }
});
