#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'manifest.webmanifest'
EXPECTED_ICON = {
    'src': 'assets/brand/logo-192.webp',
    'sizes': '192x192',
    'type': 'image/webp',
    'purpose': 'any',
}
errors = []


def fail(message: str) -> None:
    errors.append(message)


try:
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
except Exception as exc:
    print(f'ERRO: manifest.webmanifest inválido: {exc}')
    sys.exit(1)

shortcuts = manifest.get('shortcuts')
if not isinstance(shortcuts, list):
    fail('manifest.webmanifest: shortcuts deve permanecer uma lista')
else:
    for index, shortcut in enumerate(shortcuts, 1):
        if not isinstance(shortcut, dict):
            fail(f'manifest.webmanifest: atalho #{index} inválido')
            continue

        label = shortcut.get('name') or f'#{index}'
        icons = shortcut.get('icons')
        if not isinstance(icons, list) or len(icons) != 1:
            fail(f'manifest.webmanifest: atalho {label!r} deve manter exatamente um ícone')
            continue

        icon = icons[0]
        if not isinstance(icon, dict):
            fail(f'manifest.webmanifest: ícone do atalho {label!r} deve ser um objeto')
            continue

        for field, expected in EXPECTED_ICON.items():
            value = icon.get(field)
            if value != expected:
                fail(
                    f'manifest.webmanifest: ícone do atalho {label!r} deve manter '
                    f'{field} como {expected!r}'
                )

        src = icon.get('src')
        if isinstance(src, str):
            if src.startswith(('/', '//')) or '://' in src or '?' in src or '#' in src:
                fail(f'manifest.webmanifest: ícone do atalho {label!r} deve permanecer um asset local relativo')
            asset = (ROOT / src).resolve()
            try:
                asset.relative_to(ROOT.resolve())
            except ValueError:
                fail(f'manifest.webmanifest: ícone do atalho {label!r} não pode escapar da raiz do projeto')
            else:
                if not asset.is_file():
                    fail(f'manifest.webmanifest: asset do ícone do atalho {label!r} não existe: {src}')

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} problema(s).')
    sys.exit(1)

print('OK: ícones dos atalhos PWA permanecem locais, existentes e com metadata esperada.')
