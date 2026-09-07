#!/usr/bin/env python3
from pathlib import Path
import json
import re
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


def validate_install_icons(name: str, manifest: dict) -> None:
    icons = manifest.get('icons')
    if not isinstance(icons, list):
        fail(f'{name}: icons deve permanecer uma lista')
        return

    required = {
        ('192x192', 'image/webp'),
        ('512x512', 'image/webp'),
    }
    allowed_purposes = {'any', 'maskable', 'monochrome'}
    found = set()
    seen = set()

    for index, icon in enumerate(icons, 1):
        if not isinstance(icon, dict):
            fail(f'{name}: ícone #{index} inválido')
            continue

        src = icon.get('src')
        sizes = icon.get('sizes')
        media_type = icon.get('type')
        purpose = icon.get('purpose')

        if not isinstance(src, str) or not src.strip():
            fail(f'{name}: ícone #{index} deve ter src não vazio')
        if not isinstance(sizes, str) or re.fullmatch(r'(?:[1-9]\d*x[1-9]\d*|any)(?:\s+(?:[1-9]\d*x[1-9]\d*|any))*', sizes.strip()) is None:
            fail(f'{name}: ícone #{index} deve ter sizes válido')
        if not isinstance(media_type, str) or re.fullmatch(r'image/[a-z0-9.+-]+', media_type.strip().lower()) is None:
            fail(f'{name}: ícone #{index} deve ter type de imagem válido')

        purpose_tokens = [token.strip().lower() for token in purpose.split()] if isinstance(purpose, str) else []
        purposes = set(purpose_tokens)
        signature = (src, sizes, media_type)

        if signature in seen:
            fail(f'{name}: ícone de instalação duplicado no item #{index} para o mesmo src, sizes e type')
        else:
            seen.add(signature)

        if len(purpose_tokens) != len(purposes):
            fail(f'{name}: ícone #{index} contém tokens purpose duplicados')

        invalid_purposes = sorted(purposes - allowed_purposes)
        if invalid_purposes:
            fail(f'{name}: ícone #{index} contém purpose inválido: {", ".join(invalid_purposes)}')

        if 'any' not in purposes:
            fail(f'{name}: ícone #{index} deve manter purpose com suporte a any')

        if (sizes, media_type) in required:
            found.add((sizes, media_type))

    missing = sorted(required - found)
    if missing:
        labels = ', '.join(f'{sizes} {media_type}' for sizes, media_type in missing)
        fail(f'{name}: ícones de instalação obrigatórios ausentes: {labels}')


def validate_common(name: str, manifest: dict) -> None:
    required_text = ('id', 'name', 'short_name', 'description', 'lang', 'dir', 'start_url', 'scope', 'display', 'theme_color', 'background_color')
    for field in required_text:
        value = manifest.get(field)
        if not isinstance(value, str) or not value.strip():
            fail(f'{name}: {field} ausente ou vazio')

    if manifest.get('lang') != 'pt-BR':
        fail(f'{name}: lang deve permanecer pt-BR')
    if manifest.get('dir') != 'ltr':
        fail(f'{name}: dir deve permanecer ltr para manter a direção de texto consistente com a interface pt-BR')
    if manifest.get('display') != 'standalone':
        fail(f'{name}: display deve permanecer standalone para experiência de app')
    if manifest.get('orientation') != 'any':
        fail(f'{name}: orientation deve permanecer any para não forçar a orientação do dispositivo')
    if manifest.get('prefer_related_applications') is not False:
        fail(f'{name}: prefer_related_applications deve permanecer false para priorizar o PWA da própria origem')

    launch_handler = manifest.get('launch_handler')
    if not isinstance(launch_handler, dict) or launch_handler.get('client_mode') != ['navigate-existing', 'auto']:
        fail(f'{name}: launch_handler.client_mode deve priorizar navigate-existing e manter auto como fallback')

    for field in ('theme_color', 'background_color'):
        value = manifest.get(field)
        if not isinstance(value, str) or re.fullmatch(r'#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?', value) is None:
            fail(f'{name}: {field} deve ser uma cor hexadecimal válida (#RGB ou #RRGGBB)')

    override = manifest.get('display_override')
    if override is not None:
        if not isinstance(override, list) or not override or override[0] != 'standalone':
            fail(f'{name}: display_override deve priorizar standalone')

    validate_install_icons(name, manifest)


main = load_manifest('manifest.webmanifest')
if main is not None:
    validate_common('manifest.webmanifest', main)
    if main.get('id') != '/':
        fail('manifest.webmanifest: id deve permanecer / para manter a identidade instalada do app')
    if main.get('name') != 'InfoTech.io':
        fail('manifest.webmanifest: name deve permanecer InfoTech.io')
    if main.get('short_name') != 'InfoTech':
        fail('manifest.webmanifest: short_name deve permanecer InfoTech')
    if main.get('start_url') != '/':
        fail('manifest.webmanifest: start_url deve permanecer / para abrir o app principal na Home')
    if main.get('scope') != '/':
        fail('manifest.webmanifest: scope deve permanecer / para preservar as rotas instaladas do app principal')

admin = load_manifest('admin-manifest.webmanifest')
if admin is not None:
    validate_common('admin-manifest.webmanifest', admin)
    if admin.get('id') != '/infotech-admin':
        fail('admin-manifest.webmanifest: id deve permanecer /infotech-admin para não colidir com o app principal')
    if admin.get('name') != 'InfoTech.io ADM':
        fail('admin-manifest.webmanifest: name deve permanecer InfoTech.io ADM')
    if admin.get('short_name') != 'InfoTech ADM':
        fail('admin-manifest.webmanifest: short_name deve permanecer InfoTech ADM')
    if admin.get('start_url') != '/admin-login.html':
        fail('admin-manifest.webmanifest: start_url deve permanecer /admin-login.html para manter a entrada do app administrativo')
    if admin.get('scope') != '/':
        fail('admin-manifest.webmanifest: scope deve permanecer / para alcançar as páginas administrativas publicadas na raiz')

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} problema(s).')
    sys.exit(1)

print('OK: identidade, direção de texto, ícones, entrada e experiência instalada dos manifests PWA estão consistentes.')