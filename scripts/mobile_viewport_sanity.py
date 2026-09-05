#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []
checked_pages = 0


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
    for item in content.split(','):
        part = item.strip()
        if not part:
            continue
        if '=' in part:
            key, value = part.split('=', 1)
            directives[key.strip().lower()] = value.strip().lower()
        else:
            directives[part.lower()] = ''
    return directives


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
    directives = parse_directives(content)

    if directives.get('width') != 'device-width':
        errors.append(f'{page.name}: viewport deve usar width=device-width; encontrado {content!r}.')

    if directives.get('initial-scale') not in {'1', '1.0'}:
        errors.append(f'{page.name}: viewport deve usar initial-scale=1; encontrado {content!r}.')

    if directives.get('user-scalable') == 'no':
        errors.append(f'{page.name}: viewport não pode desabilitar zoom com user-scalable=no.')

    maximum_scale = directives.get('maximum-scale')
    if maximum_scale:
        try:
            if float(maximum_scale) < 2:
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
    f'Mobile viewport sanity: OK — {checked_pages} página(s) de produção com viewport responsivo '
    'e zoom preservado.'
)
