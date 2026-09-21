#!/usr/bin/env python3
"""Validate the generated independent admin distribution; run after build_admin_pwa.py."""
import json
import re
import struct
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist-admin'
ADMIN = {
    'index.html', 'admin-install.html', 'admin-login.html', 'painel-admin.html',
    'admin-seguranca.html', 'admin-solicitacao.html', 'clientes-admin.html',
    'cliente-admin.html', 'solicitacoes-antigas.html',
}
errors = []


def check(ok, message):
    if not ok:
        errors.append(message)


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.manifests = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'img') and attrs.get('src'):
            self.refs.append(attrs['src'])
        if tag == 'link' and attrs.get('href'):
            if attrs.get('rel') == 'manifest':
                self.manifests.append(attrs['href'])
            if attrs.get('rel') in ('stylesheet', 'icon', 'apple-touch-icon', 'preload'):
                self.refs.append(attrs['href'])
        if tag == 'a' and attrs.get('href'):
            value = attrs['href']
            path = urlsplit(value).path.lstrip('/')
            if path.endswith('.html') and not urlsplit(value).scheme and path not in ADMIN:
                errors.append(f'Client navigation retained on admin origin: {value}')


manifest = json.loads((DIST / 'admin-manifest.webmanifest').read_text(encoding='utf-8'))
client = json.loads((ROOT / 'manifest.webmanifest').read_text(encoding='utf-8'))
check(manifest['id'] != client['id'], 'PWA identity collides with customer app')
check(manifest['name'] == 'InfoTech ADM' and manifest['short_name'] == 'InfoTech ADM', 'Wrong admin identity')
check(manifest['start_url'] == '/admin-login.html' and manifest['scope'] == '/', 'Wrong admin origin scope/start')
check(manifest['display'] == 'standalone', 'App must run standalone')
check(set(DIST.glob('*.html')) == {DIST / p for p in ADMIN}, 'Public HTML leaked into admin build, or missing admin page')
check(not (DIST / 'sw.js').exists(), 'Public service worker leaked to admin build')
check(not (DIST / 'manifest.webmanifest').exists(), 'Public manifest leaked to admin build')
check(not (DIST / 'css/jss/v6-ui.js').exists(), 'Public PWA/client UI script leaked to admin build')
check(not (DIST / 'css/jss/v6-app.js').exists(), 'Client application JS leaked to admin build')

for icon in manifest['icons']:
    file = DIST / icon['src'].lstrip('/')
    check(file.is_file(), f'Missing icon {file}')
    if file.is_file():
        content = file.read_bytes()
        check(content[:8] == b'\x89PNG\r\n\x1a\n', f'Invalid PNG {file}')
        width, height = struct.unpack('>II', content[16:24])
        check(f'{width}x{height}' == icon['sizes'], f'Wrong icon dimensions {file}')

for page in ADMIN:
    path = DIST / page
    if not path.is_file():
        errors.append(f'Missing admin route {page}')
        continue
    markup = path.read_text(encoding='utf-8')
    parser = References()
    parser.feed(markup)
    check(parser.manifests == ['/admin-manifest.webmanifest'], f'{page}: wrong or duplicate manifest')
    check('manifest.webmanifest' not in markup.replace('admin-manifest.webmanifest', ''), f'{page}: customer manifest referenced')
    check('/sw.js' not in markup, f'{page}: customer SW referenced')
    check('v6-ui.js' not in markup, f'{page}: public PWA runtime referenced')
    for reference in parser.refs:
        url = urlsplit(reference)
        if url.scheme or reference.startswith('//') or reference.startswith('data:'):
            continue
        target = DIST / url.path.lstrip('/')
        check(target.is_file(), f'{page}: asset missing: {reference}')
    if page not in ('index.html', 'admin-install.html'):
        check('admin-ui.js' in markup and 'v6-admin.js' in markup, f'{page}: admin runtime missing')
        check('Instalar InfoTech ADM' in markup, f'{page}: admin installation control missing')
    else:
        check('admin-install.js' in markup, f'{page}: installation runtime missing')
        check('id="install-guidance"' in markup, f'{page}: manual installation instructions missing')

worker = (DIST / 'admin-sw.js').read_text(encoding='utf-8')
check("const PREFIX = 'infotech-adm-'" in worker, 'Cache prefix is not admin-specific')
check("request.mode === 'navigate'" in worker, 'Admin navigation must not be cached')
check('ALLOWED.has(url.pathname)' in worker, 'Cache lacks strict public-asset allowlist')
check("startsWith(PREFIX)" in worker, 'Worker might remove unrelated caches')
check('caches.match' in worker, 'Worker lacks fail-safe offline static fallback')
check('userChoice' in (DIST / 'css/jss/admin-install.js').read_text(encoding='utf-8'), 'Native install prompt missing')
check('appinstalled' in (DIST / 'css/jss/admin-install.js').read_text(encoding='utf-8'), 'Installation confirmation missing')
check('no-store' in (DIST / '_headers').read_text(encoding='utf-8'), 'Private responses may be cached')

if errors:
    for error in errors:
        print('FAIL:', error)
    raise SystemExit(1)
print(f'PASS: {len(ADMIN)} admin HTML routes, separate manifest/icons/SW, local assets, network-only private pages, native install')
