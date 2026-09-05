#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlsplit, unquote
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SW_PATH = ROOT / 'sw.js'
errors = []


def fail(message: str) -> None:
    errors.append(message)


def extract_set(source: str, name: str) -> set[str]:
    match = re.search(
        rf"const\s+{re.escape(name)}\s*=\s*new Set\(\[(.*?)\]\);",
        source,
        re.DOTALL,
    )
    if not match:
        fail(f'sw.js: conjunto {name} não encontrado')
        return set()
    return set(re.findall(r"['\"]([^'\"]+)['\"]", match.group(1)))


def extract_array(source: str, name: str) -> list[str]:
    match = re.search(
        rf"const\s+{re.escape(name)}\s*=\s*\[(.*?)\];",
        source,
        re.DOTALL,
    )
    if not match:
        fail(f'sw.js: lista {name} não encontrada')
        return []

    body = match.group(1)
    values = re.findall(r"['\"]([^'\"]+)['\"]", body)

    # APP_SHELL também pode reutilizar constantes locais, como OFFLINE_URL.
    for identifier in re.findall(r'(?m)^\s*([A-Z][A-Z0-9_]*)\s*,?\s*$', body):
        constant = re.search(
            rf"const\s+{re.escape(identifier)}\s*=\s*['\"]([^'\"]+)['\"]\s*;",
            source,
        )
        if constant:
            values.append(constant.group(1))
        else:
            fail(f'sw.js: constante {identifier} usada em {name} não pôde ser resolvida')

    return values


def local_target(raw: str):
    parsed = urlsplit(raw)
    if parsed.scheme or parsed.netloc:
        return None
    path = unquote(parsed.path or '')
    if path == '/':
        return ROOT / 'index.html'
    if not path.startswith('/'):
        return None
    return ROOT / path.lstrip('/')


try:
    source = SW_PATH.read_text(encoding='utf-8')
except Exception as exc:
    print(f'ERRO: sw.js não pôde ser lido: {exc}', file=sys.stderr)
    raise SystemExit(1)

public_navigation = extract_set(source, 'PUBLIC_NAVIGATION_PATHS')
app_shell = extract_array(source, 'APP_SHELL')

if not public_navigation:
    fail('sw.js: PUBLIC_NAVIGATION_PATHS está vazio')
if not app_shell:
    fail('sw.js: APP_SHELL está vazio')

sensitive_markers = (
    '/admin',
    '/painel-admin',
    '/painel-cliente',
    '/cliente-admin',
    '/clientes-admin',
    '/login',
    '/cadastro',
    '/perfil',
    '/nova-solicitacao',
    '/detalhes-solicitacao',
    '/recuperar-senha',
    '/email-confirmado',
)

for route in sorted(public_navigation):
    if not route.startswith('/'):
        fail(f'sw.js: rota pública inválida -> {route}')
        continue
    if any(route == marker or route.startswith(marker + '.') or route.startswith(marker + '/') for marker in sensitive_markers):
        fail(f'sw.js: rota sensível presente na allowlist pública -> {route}')
    target = local_target(route)
    if target is None or not target.exists():
        fail(f'sw.js: rota pública inexistente -> {route}')

seen_shell = set()
for resource in app_shell:
    if resource in seen_shell:
        fail(f'sw.js: recurso duplicado no APP_SHELL -> {resource}')
        continue
    seen_shell.add(resource)

    target = local_target(resource)
    if target is None:
        fail(f'sw.js: APP_SHELL deve conter apenas recursos locais absolutos -> {resource}')
        continue
    if not target.exists():
        fail(f'sw.js: recurso inexistente no APP_SHELL -> {resource}')

    path = urlsplit(resource).path
    if path == '/' or path.endswith('.html'):
        if path not in public_navigation:
            fail(f'sw.js: navegação no APP_SHELL não está na allowlist pública -> {resource}')

if '/offline.html' not in public_navigation:
    fail('sw.js: offline.html deve permanecer na allowlist pública')
if '/offline.html' not in seen_shell:
    fail('sw.js: offline.html deve permanecer no APP_SHELL')

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} problema(s) no Service Worker.')
    raise SystemExit(1)

print(
    f'OK: Service Worker verificado ({len(public_navigation)} rotas públicas, '
    f'{len(app_shell)} recursos no APP_SHELL).'
)
