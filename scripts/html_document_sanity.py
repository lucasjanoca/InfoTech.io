#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_ORIGIN = 'https://infotech-io.com.br'
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
        self.robots = []
        self.canonicals = []
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
        elif tag == 'meta' and data.get('name', '').strip().lower() == 'robots':
            self.robots.append(data.get('content', '').strip())
        elif tag == 'link':
            rel_tokens = {token.casefold() for token in data.get('rel', '').split()}
            if 'canonical' in rel_tokens:
                self.canonicals.append(data.get('href', '').strip())
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


def expected_canonical(page: Path) -> str:
    return f'{OFFICIAL_ORIGIN}/' if page.name == 'index.html' else f'{OFFICIAL_ORIGIN}/{page.name}'


pages = sorted(ROOT.glob('*.html'))
if not pages:
    fail('nenhuma página HTML de produção encontrada na raiz')

title_owners = {}
description_owners = {}
canonical_owners = {}

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
    else:
        description_key = normalized_descriptions[0].casefold()
        if description_key in description_owners:
            fail(
                f'{page.name}: meta description duplica a de {description_owners[description_key]} '
                f'("{normalized_descriptions[0]}")'
            )
        else:
            description_owners[description_key] = page.name

    robots_tokens = {
        token.strip().lower()
        for value in parser.robots
        for token in value.split(',')
        if token.strip()
    }
    is_indexable = 'noindex' not in robots_tokens
    if is_indexable:
        if len(parser.canonicals) != 1:
            fail(f'{page.name}: página indexável deve declarar exatamente um link canonical')
        else:
            canonical = parser.canonicals[0]
            parsed = urlparse(canonical)
            if parsed.scheme != 'https' or parsed.netloc != 'infotech-io.com.br':
                fail(f'{page.name}: canonical deve usar a origem HTTPS oficial da InfoTech.io')
            elif parsed.query or parsed.fragment:
                fail(f'{page.name}: canonical não pode conter query string ou fragmento')
            elif canonical != expected_canonical(page):
                fail(
                    f'{page.name}: canonical deve ser "{expected_canonical(page)}" '
                    f'(encontrado "{canonical}")'
                )
            canonical_key = canonical.casefold()
            if canonical_key in canonical_owners:
                fail(f'{page.name}: canonical duplica o de {canonical_owners[canonical_key]}')
            else:
                canonical_owners[canonical_key] = page.name

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} problema(s).')
    sys.exit(1)

print(f'OK: baseline de documento validada em {len(pages)} páginas de produção.')
