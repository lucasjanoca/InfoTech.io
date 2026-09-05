#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []


def fail(message: str) -> None:
    errors.append(message)


def load_manifest(name: str):
    path = ROOT / name
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        fail(f'{name}: manifesto inválido: {exc}')
        return None


def validate_common(name: str, manifest: dict) -> None:
    required_text = ('id', 'name', 'short_name', 'description', 'lang', 'display', 'theme_color', 'background_color')
    for field in required_text:
        value = manifest.get(field)
        if not isinstance(value, str) or not value.strip():
            fail(f'{name}: {field} ausente ou vazio')

    if manifest.get('lang') != 'pt-BR':
        fail(f'{name}: lang deve permanecer pt-BR')
    if manifest.get('display') != 'standalone':
        fail(f'{name}: display deve permanecer standalone para experiência de app')

    for field in ('theme_color', 'background_color'):
        value = manifest.get(field)
        if not isinstance(value, str) or not value.startswith('#') or len(value) not in (4, 7):
            fail(f'{name}: {field} deve ser uma cor hexadecimal válida')

    override = manifest.get('display_override')
    if override is not None:
        if not isinstance(override, list) or not override or override[0] != 'standalone':
            fail(f'{name}: display_override deve priorizar standalone')


main = load_manifest('manifest.webmanifest')
if main is not None:
    validate_common('manifest.webmanifest', main)
    if main.get('id') != '/':
        fail('manifest.webmanifest: id deve permanecer / para manter a identidade instalada do app')
    if main.get('name') != 'InfoTech.io':
        fail('manifest.webmanifest: name deve permanecer InfoTech.io')
    if main.get('short_name') != 'InfoTech':
        fail('manifest.webmanifest: short_name deve permanecer InfoTech')

admin = load_manifest('admin-manifest.webmanifest')
if admin is not None:
    validate_common('admin-manifest.webmanifest', admin)
    if admin.get('id') != '/infotech-admin':
        fail('admin-manifest.webmanifest: id deve permanecer /infotech-admin para não colidir com o app principal')
    if admin.get('name') != 'InfoTech.io ADM':
        fail('admin-manifest.webmanifest: name deve permanecer InfoTech.io ADM')
    if admin.get('short_name') != 'InfoTech ADM':
        fail('admin-manifest.webmanifest: short_name deve permanecer InfoTech ADM')

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} problema(s).')
    sys.exit(1)

print('OK: identidade e experiência instalada dos manifests PWA estão consistentes.')
