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


def validate_allowlist_path(route: str, list_name: str) -> None:
    parsed = urlsplit(route)
    decoded_path = unquote(parsed.path)

    if route != route.strip():
        fail(f'sw.js: {list_name} não deve conter espaços externos -> {route!r}')
    if parsed.scheme or parsed.netloc:
        fail(f'sw.js: {list_name} deve conter apenas caminhos locais -> {route}')
    if parsed.query or parsed.fragment:
        fail(f'sw.js: {list_name} deve conter apenas caminhos sem query/fragmento -> {route}')
    if decoded_path != parsed.path:
        fail(f'sw.js: {list_name} não deve usar caminho percent-encoded -> {route}')
    if '\\' in decoded_path:
        fail(f'sw.js: {list_name} não deve usar barra invertida -> {route}')
    if '//' in decoded_path:
        fail(f'sw.js: {list_name} não deve usar barras duplicadas -> {route}')
    if any(segment in {'.', '..'} for segment in decoded_path.split('/')):
        fail(f'sw.js: {list_name} não deve conter segmentos . ou .. -> {route}')


try:
    source = SW_PATH.read_text(encoding='utf-8')
except Exception as exc:
    print(f'ERRO: sw.js não pôde ser lido: {exc}', file=sys.stderr)
    raise SystemExit(1)

public_navigation = extract_set(source, 'PUBLIC_NAVIGATION_PATHS')
notification_paths = extract_set(source, 'NOTIFICATION_PATHS')
app_shell = extract_array(source, 'APP_SHELL')

if not public_navigation:
    fail('sw.js: PUBLIC_NAVIGATION_PATHS está vazio')
if not notification_paths:
    fail('sw.js: NOTIFICATION_PATHS está vazio')
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
    validate_allowlist_path(route, 'PUBLIC_NAVIGATION_PATHS')
    if not route.startswith('/'):
        fail(f'sw.js: rota pública inválida -> {route}')
        continue
    if any(route == marker or route.startswith(marker + '.') or route.startswith(marker + '/') for marker in sensitive_markers):
        fail(f'sw.js: rota sensível presente na allowlist pública -> {route}')
    target = local_target(route)
    if target is None or not target.exists():
        fail(f'sw.js: rota pública inexistente -> {route}')

for route in sorted(notification_paths):
    validate_allowlist_path(route, 'NOTIFICATION_PATHS')
    target = local_target(route)
    if target is None or not target.exists():
        fail(f'sw.js: destino de notificação inexistente ou externo -> {route}')

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
if '/painel-cliente.html' not in notification_paths:
    fail('sw.js: painel-cliente.html deve permanecer como destino seguro de notificação')

notification_click = re.search(
    r"self\.addEventListener\(['\"]notificationclick['\"],\s*event\s*=>\s*\{(.*?)\n\}\);",
    source,
    re.DOTALL,
)
if not notification_click:
    fail('sw.js: handler notificationclick não encontrado')
else:
    body = notification_click.group(1)
    if 'candidate.origin === self.location.origin' not in body:
        fail('sw.js: notificationclick deve validar mesma origem antes de navegar')
    if 'NOTIFICATION_PATHS.has(candidate.pathname)' not in body:
        fail('sw.js: notificationclick deve validar a allowlist NOTIFICATION_PATHS')
    if "new URL('/painel-cliente.html', self.location.origin).href" not in body:
        fail('sw.js: notificationclick deve manter fallback seguro para painel-cliente.html')

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} problema(s) no Service Worker.')
    raise SystemExit(1)

print(
    f'OK: Service Worker verificado ({len(public_navigation)} rotas públicas, '
    f'{len(notification_paths)} destinos de notificação, {len(app_shell)} recursos no APP_SHELL).'
)
