#!/usr/bin/env python3
from html.parser import HTMLParser
from ipaddress import ip_address
from pathlib import Path
from urllib.parse import urlsplit
import sys

ROOT = Path(__file__).resolve().parents[1]
URL_ATTRIBUTES = {'href', 'src', 'action', 'formaction', 'poster'}
LOCAL_HOSTNAMES = {'localhost'}
errors = []


def is_local_or_non_public_host(hostname: str) -> bool:
    normalized = hostname.rstrip('.').lower()
    if normalized in LOCAL_HOSTNAMES or normalized.endswith('.localhost'):
        return True

    try:
        address = ip_address(normalized)
    except ValueError:
        return False

    return not address.is_global


class HttpsAuthorityParser(HTMLParser):
    def __init__(self, page: Path):
        super().__init__(convert_charrefs=True)
        self.page = page

    def handle_starttag(self, tag, attrs):
        for attr_name, raw_value in attrs:
            name = (attr_name or '').lower()
            if name not in URL_ATTRIBUTES or not raw_value:
                continue

            value = raw_value.strip()
            parsed = urlsplit(value)
            if parsed.scheme.lower() != 'https':
                continue

            try:
                hostname = parsed.hostname
                parsed.port
            except ValueError as exc:
                errors.append(
                    f'{self.page.name}: autoridade HTTPS inválida em '
                    f'{tag.lower()}[{name}] -> {value!r} ({exc})'
                )
                continue

            if not parsed.netloc or not hostname:
                errors.append(
                    f'{self.page.name}: URL HTTPS absoluta sem host válido em '
                    f'{tag.lower()}[{name}] -> {value!r}'
                )
                continue

            if is_local_or_non_public_host(hostname):
                errors.append(
                    f'{self.page.name}: URL HTTPS absoluta aponta para host local/não público em '
                    f'{tag.lower()}[{name}] -> {value!r}'
                )


pages = sorted(ROOT.glob('*.html'))
for page in pages:
    parser = HttpsAuthorityParser(page)
    try:
        parser.feed(page.read_text(encoding='utf-8'))
    except Exception as exc:
        errors.append(f'{page.name}: HTML não pôde ser analisado: {exc}')

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} URL(s) HTTPS com autoridade inválida ou não pública.')
    sys.exit(1)

print(
    f'OK: {len(pages)} páginas sem URLs HTTPS absolutas com autoridade inválida '
    'ou host local/não público.'
)
