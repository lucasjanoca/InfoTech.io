#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []


class CSPParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.policies = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'meta':
            return
        data = {k.lower(): (v or '') for k, v in attrs}
        if data.get('http-equiv', '').lower() == 'content-security-policy':
            self.policies.append(data.get('content', '').strip())


def parse_directives(policy: str):
    directives = {}
    for raw in policy.split(';'):
        raw = raw.strip()
        if not raw:
            continue
        parts = raw.split()
        name = parts[0].lower()
        directives[name] = [value.lower() for value in parts[1:]]
    return directives


for page in sorted(ROOT.glob('*.html')):
    parser = CSPParser()
    try:
        parser.feed(page.read_text(encoding='utf-8'))
    except Exception as exc:
        errors.append(f'{page.name}: HTML não pôde ser analisado: {exc}')
        continue

    if len(parser.policies) != 1:
        errors.append(f'{page.name}: esperado exatamente 1 meta CSP, encontrado {len(parser.policies)}')
        continue

    policy = parser.policies[0]
    directives = parse_directives(policy)

    required = {
        'default-src': "'self'",
        'object-src': "'none'",
        'base-uri': "'self'",
    }
    for directive, required_value in required.items():
        values = directives.get(directive)
        if values is None:
            errors.append(f'{page.name}: CSP sem diretiva obrigatória {directive}')
        elif required_value not in values:
            errors.append(f'{page.name}: {directive} deve conter {required_value}')

    # script-src é opcional em páginas sem scripts: nesse caso default-src é o fallback CSP.
    # Quando declarado, porém, deve manter a mesma baseline segura do restante do site.
    script_values = directives.get('script-src', directives.get('default-src', []))
    if "'self'" not in script_values:
        errors.append(f"{page.name}: fonte efetiva de scripts deve conter 'self'")
    for forbidden in ("'unsafe-inline'", "'unsafe-eval'", '*'):
        if forbidden in script_values:
            errors.append(f'{page.name}: fonte efetiva de scripts contém valor perigoso {forbidden}')

    if '*' in directives.get('default-src', []):
        errors.append(f'{page.name}: default-src não pode usar wildcard')

    # Meta CSP é a camada realmente portável no GitHub Pages. Evite fontes HTTP
    # acidentais em qualquer diretiva, sem confundir wss:// com tráfego inseguro.
    for directive, values in directives.items():
        for value in values:
            if re.match(r'^http://', value, re.IGNORECASE):
                errors.append(f'{page.name}: {directive} contém origem HTTP insegura -> {value}')

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} problema(s) na baseline CSP.')
    sys.exit(1)

print(f'OK: baseline CSP validada em {len(list(ROOT.glob("*.html")))} páginas.')
