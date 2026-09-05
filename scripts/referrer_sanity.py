#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = 'strict-origin-when-cross-origin'
errors = []


class ReferrerParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.policies = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'meta':
            return
        data = {key.lower(): (value or '') for key, value in attrs}
        if data.get('name', '').strip().lower() == 'referrer':
            self.policies.append(data.get('content', '').strip().lower())


for page in sorted(ROOT.glob('*.html')):
    parser = ReferrerParser()
    try:
        parser.feed(page.read_text(encoding='utf-8'))
    except Exception as exc:
        errors.append(f'{page.name}: HTML não pôde ser analisado: {exc}')
        continue

    if not parser.policies:
        errors.append(f'{page.name}: política de referrer ausente')
        continue

    if len(parser.policies) != 1:
        errors.append(f'{page.name}: deve existir exatamente uma política de referrer')
        continue

    if parser.policies[0] != EXPECTED:
        errors.append(
            f'{page.name}: política de referrer inesperada -> {parser.policies[0]!r}; '
            f'esperado {EXPECTED!r}'
        )

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} problema(s).')
    sys.exit(1)

print(f'OK: política de referrer validada em {len(list(ROOT.glob("*.html")))} páginas HTML.')
