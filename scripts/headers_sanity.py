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

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} problema(s).')
    sys.exit(1)

print('OK: _headers mantém as políticas globais e de /io esperadas.')
