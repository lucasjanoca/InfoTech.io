#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []


class DocumentParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.doctypes = []
        self.html_langs = []
        self.head_count = 0
        self.body_count = 0
        self.charsets = []
        self.titles = []
        self.descriptions = []
        self.in_title = False

    def handle_decl(self, decl):
        if decl.strip().lower().startswith('doctype'):
            self.doctypes.append(decl.strip())

    def handle_starttag(self, tag, attrs):
        data = {name.lower(): (value or '') for name, value in attrs}
        tag = tag.lower()

        if tag == 'html':
            self.html_langs.append(data.get('lang', '').strip())
        elif tag == 'head':
            self.head_count += 1
        elif tag == 'body':
            self.body_count += 1
        elif tag == 'meta' and 'charset' in data:
            self.charsets.append(data.get('charset', '').strip())
        elif tag == 'meta' and data.get('name', '').strip().lower() == 'description':
            self.descriptions.append(data.get('content', '').strip())
        elif tag == 'title':
            self.titles.append('')
            self.in_title = True

    def handle_data(self, data):
        if self.in_title and self.titles:
            self.titles[-1] += data

    def handle_endtag(self, tag):
        if tag.lower() == 'title':
            self.in_title = False


def fail(message: str) -> None:
    errors.append(message)


pages = sorted(ROOT.glob('*.html'))
if not pages:
    fail('nenhuma página HTML de produção encontrada na raiz')

title_owners = {}

for page in pages:
    parser = DocumentParser()
    try:
        raw = page.read_text(encoding='utf-8')
        parser.feed(raw)
    except Exception as exc:
        fail(f'{page.name}: HTML não pôde ser analisado: {exc}')
        continue

    if len(parser.doctypes) != 1 or parser.doctypes[0].lower() != 'doctype html':
        fail(f'{page.name}: deve declarar exatamente <!doctype html>')

    if len(parser.html_langs) != 1:
        fail(f'{page.name}: deve conter exatamente um elemento <html>')
    elif parser.html_langs[0].lower() != 'pt-br':
        fail(f'{page.name}: <html> deve declarar lang="pt-BR"')

    if parser.head_count != 1:
        fail(f'{page.name}: deve conter exatamente um elemento <head>')

    if parser.body_count != 1:
        fail(f'{page.name}: deve conter exatamente um elemento <body>')

    normalized_charsets = [value.lower().replace('_', '-') for value in parser.charsets]
    if len(normalized_charsets) != 1 or normalized_charsets[0] != 'utf-8':
        fail(f'{page.name}: deve declarar exatamente um <meta charset="utf-8">')
    else:
        prefix = raw.encode('utf-8')[:1024]
        if not re.search(rb'<meta\s+[^>]*charset\s*=\s*["\']?utf-8(?:["\']|\s|/?>)', prefix, re.IGNORECASE):
            fail(f'{page.name}: <meta charset="utf-8"> deve estar nos primeiros 1024 bytes')

    normalized_titles = [' '.join(value.split()) for value in parser.titles]
    if len(normalized_titles) != 1:
        fail(f'{page.name}: deve declarar exatamente um <title>')
    elif not normalized_titles[0]:
        fail(f'{page.name}: <title> não pode estar vazio')
    else:
        title_key = normalized_titles[0].casefold()
        if title_key in title_owners:
            fail(
                f'{page.name}: <title> duplica o título de {title_owners[title_key]} '
                f'("{normalized_titles[0]}")'
            )
        else:
            title_owners[title_key] = page.name

    normalized_descriptions = [' '.join(value.split()) for value in parser.descriptions]
    if len(normalized_descriptions) != 1:
        fail(f'{page.name}: deve declarar exatamente uma <meta name="description">')
    elif not normalized_descriptions[0]:
        fail(f'{page.name}: meta description não pode estar vazia')

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} problema(s).')
    sys.exit(1)

print(f'OK: baseline de documento validada em {len(pages)} páginas de produção.')
