#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []


class DocumentParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.doctypes = []
        self.html_langs = []
        self.charsets = []

    def handle_decl(self, decl):
        if decl.strip().lower().startswith('doctype'):
            self.doctypes.append(decl.strip())

    def handle_starttag(self, tag, attrs):
        data = {name.lower(): (value or '') for name, value in attrs}
        tag = tag.lower()

        if tag == 'html':
            self.html_langs.append(data.get('lang', '').strip())
        elif tag == 'meta' and 'charset' in data:
            self.charsets.append(data.get('charset', '').strip())


def fail(message: str) -> None:
    errors.append(message)


pages = sorted(ROOT.glob('*.html'))
if not pages:
    fail('nenhuma página HTML de produção encontrada na raiz')

for page in pages:
    parser = DocumentParser()
    try:
        parser.feed(page.read_text(encoding='utf-8'))
    except Exception as exc:
        fail(f'{page.name}: HTML não pôde ser analisado: {exc}')
        continue

    if len(parser.doctypes) != 1 or parser.doctypes[0].lower() != 'doctype html':
        fail(f'{page.name}: deve declarar exatamente <!doctype html>')

    if len(parser.html_langs) != 1:
        fail(f'{page.name}: deve conter exatamente um elemento <html>')
    elif parser.html_langs[0].lower() != 'pt-br':
        fail(f'{page.name}: <html> deve declarar lang="pt-BR"')

    normalized_charsets = [value.lower().replace('_', '-') for value in parser.charsets]
    if len(normalized_charsets) != 1 or normalized_charsets[0] != 'utf-8':
        fail(f'{page.name}: deve declarar exatamente um <meta charset="utf-8">')

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} problema(s).')
    sys.exit(1)

print(f'OK: baseline de documento validada em {len(pages)} páginas de produção.')
