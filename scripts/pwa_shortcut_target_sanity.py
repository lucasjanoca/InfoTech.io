#!/usr/bin/env python3
from pathlib import Path, PurePosixPath
import json
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'manifest.webmanifest'
errors = []


def fail(message: str) -> None:
    errors.append(message)


try:
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
except Exception as exc:
    print(f'ERRO: manifest.webmanifest inválido: {exc}')
    sys.exit(1)

scope = manifest.get('scope')
shortcuts = manifest.get('shortcuts')
seen_targets = {}

if scope != '/':
    fail('manifest.webmanifest: scope deve permanecer / para validar os atalhos publicados')

if not isinstance(shortcuts, list):
    fail('manifest.webmanifest: shortcuts deve permanecer uma lista')
else:
    for index, shortcut in enumerate(shortcuts, 1):
        if not isinstance(shortcut, dict):
            fail(f'manifest.webmanifest: atalho #{index} inválido')
            continue

        label = shortcut.get('name') or f'#{index}'
        url = shortcut.get('url')
        if not isinstance(url, str) or not url.strip():
            fail(f'manifest.webmanifest: atalho {label!r} deve ter url não vazia')
            continue
        if url != url.strip():
            fail(f'manifest.webmanifest: atalho {label!r} não deve ter espaços externos em url')
            continue

        parsed = urlsplit(url)
        if parsed.scheme or parsed.netloc or not parsed.path.startswith('/'):
            fail(f'manifest.webmanifest: atalho {label!r} deve permanecer na própria origem')
            continue
        if parsed.query or parsed.fragment:
            fail(f'manifest.webmanifest: atalho {label!r} não deve conter query ou fragmento')
            continue

        posix_path = PurePosixPath(parsed.path)
        if '..' in posix_path.parts:
            fail(f'manifest.webmanifest: atalho {label!r} não pode escapar da raiz do app')
            continue

        target_key = posix_path.as_posix()
        previous_label = seen_targets.get(target_key)
        if previous_label is not None:
            fail(
                f'manifest.webmanifest: atalhos {previous_label!r} e {label!r} '
                f'não podem apontar para o mesmo destino {target_key!r}'
            )
        else:
            seen_targets[target_key] = label

        relative = parsed.path.lstrip('/')
        target = ROOT / ('index.html' if not relative else relative)
        if not target.is_file():
            fail(f'manifest.webmanifest: destino do atalho {label!r} não existe: {parsed.path}')

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} problema(s).')
    sys.exit(1)

print('OK: destinos dos atalhos PWA permanecem locais, únicos, dentro do escopo e apontam para arquivos existentes.')
