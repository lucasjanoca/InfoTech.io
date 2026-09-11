#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'manifest.webmanifest'
errors = []


def fail(message: str) -> None:
    errors.append(message)


def clean_text(shortcut: dict, field: str, label: str) -> str | None:
    value = shortcut.get(field)
    if not isinstance(value, str) or not value.strip():
        fail(f'manifest.webmanifest: atalho {label} deve ter {field} não vazio')
        return None
    if value != value.strip():
        fail(f'manifest.webmanifest: atalho {label} não deve ter espaços externos em {field}')
    if any(ord(char) < 32 for char in value):
        fail(f'manifest.webmanifest: atalho {label} não deve ter caracteres de controle em {field}')
    return value


try:
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
except Exception as exc:
    print(f'ERRO: manifest.webmanifest inválido: {exc}')
    sys.exit(1)

shortcuts = manifest.get('shortcuts')
if not isinstance(shortcuts, list) or not shortcuts:
    fail('manifest.webmanifest: shortcuts deve permanecer uma lista não vazia')
else:
    seen_names = set()
    seen_short_names = set()

    for index, shortcut in enumerate(shortcuts, 1):
        label = f'#{index}'
        if not isinstance(shortcut, dict):
            fail(f'manifest.webmanifest: atalho {label} inválido')
            continue

        name = clean_text(shortcut, 'name', label)
        short_name = clean_text(shortcut, 'short_name', label)
        clean_text(shortcut, 'description', label)

        if name is not None:
            key = name.casefold()
            if key in seen_names:
                fail(f'manifest.webmanifest: name de atalho duplicado: {name!r}')
            seen_names.add(key)

        if short_name is not None:
            key = short_name.casefold()
            if key in seen_short_names:
                fail(f'manifest.webmanifest: short_name de atalho duplicado: {short_name!r}')
            seen_short_names.add(key)

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} problema(s).')
    sys.exit(1)

print('OK: atalhos PWA mantêm nomes, nomes curtos e descrições válidos e sem duplicação.')
