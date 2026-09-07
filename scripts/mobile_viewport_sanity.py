#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []
checked_pages = 0
PWA_EDGE_TO_EDGE_PAGES = {
    'index.html',
    'admin-install.html',
    'admin-login.html',
    'offline.html',
}


class ViewportParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.viewports = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'meta':
            return
        data = {key.lower(): (value or '') for key, value in attrs}
        if data.get('name', '').strip().lower() == 'viewport':
            self.viewports.append(data.get('content', '').strip())


def parse_directives(content: str):
    directives = {}
    duplicates = []
    empty_segments = 0
    empty_keys = 0
    for item in content.split(','):
        part = item.strip()
        if not part:
            empty_segments += 1
            continue
        if '=' in part:
            key, value = part.split('=', 1)
            key = key.strip().lower()
            value = value.strip().lower()
        else:
            key = part.lower()
            value = ''
        if not key:
            empty_keys += 1
            continue
        if key in directives:
            duplicates.append(key)
        else:
            directives[key] = value
    return directives, duplicates, empty_segments, empty_keys


for page in sorted(ROOT.glob('*.html')):
    parser = ViewportParser()
    try:
        parser.feed(page.read_text(encoding='utf-8'))
    except Exception as exc:
        errors.append(f'{page.name}: HTML não pôde ser analisado: {exc}')
        continue

    checked_pages += 1
    if len(parser.viewports) != 1:
        errors.append(
            f'{page.name}: deve declarar exatamente um meta viewport; encontrados {len(parser.viewports)}.'
        )
        continue

    content = parser.viewports[0]
    directives, duplicate_directives, empty_segments, empty_keys = parse_directives(content)

    if empty_segments:
        errors.append(
            f'{page.name}: viewport não deve conter segmentos vazios separados por vírgula; '
            f'encontrado {content!r}.'
        )

    if empty_keys:
        errors.append(
            f'{page.name}: viewport não deve conter diretiva sem nome; encontrado {content!r}.'
        )

    if duplicate_directives:
        duplicates = ', '.join(sorted(set(duplicate_directives)))
        errors.append(
            f'{page.name}: viewport não deve repetir diretivas ({duplicates}); encontrado {content!r}.'
        )

    if directives.get('width') != 'device-width':
        errors.append(f'{page.name}: viewport deve usar width=device-width; encontrado {content!r}.')

    if directives.get('initial-scale') not in {'1', '1.0'}:
        errors.append(f'{page.name}: viewport deve usar initial-scale=1; encontrado {content!r}.')

    if page.name in PWA_EDGE_TO_EDGE_PAGES and directives.get('viewport-fit') != 'cover':
        errors.append(
            f'{page.name}: entrada PWA deve manter viewport-fit=cover para preservar a experiência '
            'edge-to-edge e as safe areas no modo instalado.'
        )

    user_scalable = directives.get('user-scalable')
    if user_scalable is not None:
        if user_scalable in {'no', '0', 'false'}:
            errors.append(
                f'{page.name}: viewport não pode desabilitar zoom com user-scalable={user_scalable}.'
            )
        elif user_scalable not in {'yes', '1', 'true'}:
            errors.append(
                f'{page.name}: user-scalable inválido no viewport -> {user_scalable!r}; '
                'remova a diretiva ou use um valor que preserve o zoom.'
            )

    maximum_scale = directives.get('maximum-scale')
    if maximum_scale is not None:
        try:
            parsed_maximum_scale = float(maximum_scale)
            if not math.isfinite(parsed_maximum_scale):
                raise ValueError
            if parsed_maximum_scale < 2:
                errors.append(
                    f'{page.name}: maximum-scale={maximum_scale} restringe excessivamente o zoom; '
                    'remova a diretiva ou permita pelo menos 2x.'
                )
        except ValueError:
            errors.append(f'{page.name}: maximum-scale inválido no viewport -> {maximum_scale!r}.')

if checked_pages == 0:
    errors.append('Nenhuma página HTML de produção foi encontrada na raiz; auditoria sem cobertura.')

if errors:
    print('Mobile viewport sanity: FALHOU')
    for error in errors:
        print(f'ERRO: {error}')
    sys.exit(1)

print(
    f'Mobile viewport sanity: OK — {checked_pages} página(s) de produção com viewport responsivo, '
    'zoom preservado e entradas PWA preparadas para safe areas.'
)