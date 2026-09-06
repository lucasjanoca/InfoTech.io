#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
HEADERS = ROOT / '_headers'
errors = []


def fail(message: str) -> None:
    errors.append(message)


text = HEADERS.read_text(encoding='utf-8')
blocks = [block for block in re.split(r'\n\s*\n', text.strip()) if block.strip()]
parsed = {}

for block in blocks:
    lines = block.splitlines()
    route = lines[0].strip()
    if route in parsed:
        fail(f'bloco de rota duplicado em _headers -> {route}')
        continue
    headers = {}
    for raw in lines[1:]:
        line = raw.strip()
        if not line or line.startswith('!'):
            continue
        if ':' not in line:
            fail(f'{route}: linha de header inválida -> {line}')
            continue
        name, value = line.split(':', 1)
        key = name.strip().lower()
        if key in headers:
            fail(f'{route}: header duplicado -> {name.strip()}')
            continue
        headers[key] = value.strip()
    parsed[route] = headers

for route in ('/*', '/io/*'):
    if route not in parsed:
        fail(f'bloco obrigatório ausente em _headers -> {route}')
        continue
    policy = parsed[route].get('permissions-policy', '')
    if not policy:
        fail(f'{route}: Permissions-Policy ausente')
    elif 'browsing-topics=()' not in {item.strip() for item in policy.split(',')}:
        fail(f'{route}: Permissions-Policy deve desabilitar browsing-topics')

if parsed.get('/*', {}).get('x-content-type-options', '').lower() != 'nosniff':
    fail('/*: X-Content-Type-Options deve permanecer nosniff')

if parsed.get('/*', {}).get('referrer-policy', '').lower() != 'strict-origin-when-cross-origin':
    fail('/*: Referrer-Policy deve permanecer strict-origin-when-cross-origin')

sensitive_routes = (
    '/io/*',
    '/admin-*',
    '/painel-admin.html',
    '/cliente-admin.html',
    '/clientes-admin.html',
)
required_robots = {'noindex', 'nofollow', 'noarchive'}
for route in sensitive_routes:
    headers = parsed.get(route)
    if headers is None:
        fail(f'bloco sensível obrigatório ausente em _headers -> {route}')
        continue
    if headers.get('cache-control', '').lower() != 'no-store':
        fail(f'{route}: Cache-Control deve permanecer no-store')
    robots = {item.strip().lower() for item in headers.get('x-robots-tag', '').split(',') if item.strip()}
    if not required_robots.issubset(robots):
        fail(f'{route}: X-Robots-Tag deve manter noindex, nofollow e noarchive')

offline_headers = parsed.get('/offline.html')
if offline_headers is None:
    fail('bloco obrigatório ausente em _headers -> /offline.html')
else:
    offline_robots = {
        item.strip().lower()
        for item in offline_headers.get('x-robots-tag', '').split(',')
        if item.strip()
    }
    if not required_robots.issubset(offline_robots):
        fail('/offline.html: X-Robots-Tag deve manter noindex, nofollow e noarchive')

sw_headers = parsed.get('/sw.js')
if sw_headers is None:
    fail('bloco obrigatório ausente em _headers -> /sw.js')
else:
    cache_tokens = {
        item.strip().lower()
        for item in sw_headers.get('cache-control', '').split(',')
        if item.strip()
    }
    if not {'no-cache', 'no-store', 'must-revalidate'}.issubset(cache_tokens):
        fail('/sw.js: Cache-Control deve manter no-cache, no-store e must-revalidate')
    if sw_headers.get('service-worker-allowed', '') != '/':
        fail('/sw.js: Service-Worker-Allowed deve permanecer /')

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} problema(s).')
    sys.exit(1)

print('OK: _headers mantém políticas globais, rotas sensíveis e fronteiras do Service Worker.')
