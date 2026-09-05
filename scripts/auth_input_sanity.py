#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_PASSWORD_AUTOCOMPLETE = {'current-password', 'new-password'}
errors = []
password_inputs = 0


class PasswordInputParser(HTMLParser):
    def __init__(self, source: Path):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.inputs = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'input':
            return
        data = {key.lower(): (value or '') for key, value in attrs}
        if data.get('type', '').strip().lower() != 'password':
            return
        self.inputs.append(data)


for page in sorted(ROOT.rglob('*.html')):
    # Ignore generated/vendor directories if any are added in the future.
    if any(part in {'.git', 'node_modules', 'dist', 'build'} for part in page.parts):
        continue

    parser = PasswordInputParser(page)
    try:
        parser.feed(page.read_text(encoding='utf-8'))
    except Exception as exc:
        errors.append(f'{page.relative_to(ROOT)}: HTML não pôde ser analisado: {exc}')
        continue

    for field in parser.inputs:
        password_inputs += 1
        autocomplete = field.get('autocomplete', '').strip().lower()
        identifier = field.get('id') or field.get('name') or '(sem id/name)'
        if autocomplete not in ALLOWED_PASSWORD_AUTOCOMPLETE:
            errors.append(
                f'{page.relative_to(ROOT)}: campo de senha {identifier} deve usar '
                f'autocomplete="current-password" ou "new-password"; encontrado '
                f'{autocomplete or "ausente"!r}'
            )

if password_inputs == 0:
    errors.append('Nenhum campo type="password" foi encontrado; a auditoria perdeu cobertura.')

if errors:
    print('Auth input sanity: FALHOU')
    for error in errors:
        print(f'- {error}')
    sys.exit(1)

print(
    f'Auth input sanity: OK — {password_inputs} campo(s) de senha usam autocomplete '
    'compatível com gerenciadores de senha.'
)
