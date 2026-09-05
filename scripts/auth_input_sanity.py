#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_PASSWORD_AUTOCOMPLETE = {'current-password', 'new-password'}
errors = []
password_inputs = 0
login_forms = 0


class AuthInputParser(HTMLParser):
    def __init__(self, source: Path):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.form_stack = []
        self.forms = []
        self.inputs = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        data = {key.lower(): (value or '') for key, value in attrs}

        if tag == 'form':
            form = {'attrs': data, 'inputs': []}
            self.forms.append(form)
            self.form_stack.append(form)
            return

        if tag != 'input':
            return

        self.inputs.append(data)
        if self.form_stack:
            self.form_stack[-1]['inputs'].append(data)

    def handle_endtag(self, tag):
        if tag.lower() == 'form' and self.form_stack:
            self.form_stack.pop()


for page in sorted(ROOT.rglob('*.html')):
    # Ignore generated/vendor directories if any are added in the future.
    if any(part in {'.git', 'node_modules', 'dist', 'build'} for part in page.parts):
        continue

    parser = AuthInputParser(page)
    try:
        parser.feed(page.read_text(encoding='utf-8'))
    except Exception as exc:
        errors.append(f'{page.relative_to(ROOT)}: HTML não pôde ser analisado: {exc}')
        continue

    for field in parser.inputs:
        if field.get('type', '').strip().lower() != 'password':
            continue
        password_inputs += 1
        autocomplete = field.get('autocomplete', '').strip().lower()
        identifier = field.get('id') or field.get('name') or '(sem id/name)'
        if autocomplete not in ALLOWED_PASSWORD_AUTOCOMPLETE:
            errors.append(
                f'{page.relative_to(ROOT)}: campo de senha {identifier} deve usar '
                f'autocomplete="current-password" ou "new-password"; encontrado '
                f'{autocomplete or "ausente"!r}'
            )

    for form in parser.forms:
        current_passwords = [
            field for field in form['inputs']
            if field.get('type', '').strip().lower() == 'password'
            and field.get('autocomplete', '').strip().lower() == 'current-password'
        ]
        if not current_passwords:
            continue

        login_forms += 1
        identifiers = [
            field for field in form['inputs']
            if field.get('type', '').strip().lower() in {'email', 'text'}
            and (field.get('name') or field.get('id'))
        ]
        username_fields = [
            field for field in identifiers
            if field.get('autocomplete', '').strip().lower() == 'username'
        ]

        if len(username_fields) != 1:
            form_id = form['attrs'].get('id') or form['attrs'].get('name') or '(form sem id/name)'
            errors.append(
                f'{page.relative_to(ROOT)}: formulário de login {form_id} com '
                'autocomplete="current-password" deve ter exatamente um identificador '
                f'com autocomplete="username"; encontrados {len(username_fields)}.'
            )

if password_inputs == 0:
    errors.append('Nenhum campo type="password" foi encontrado; a auditoria perdeu cobertura.')

if login_forms == 0:
    errors.append('Nenhum formulário com autocomplete="current-password" foi encontrado; a auditoria perdeu cobertura de login.')

if errors:
    print('Auth input sanity: FALHOU')
    for error in errors:
        print(f'- {error}')
    sys.exit(1)

print(
    f'Auth input sanity: OK — {password_inputs} campo(s) de senha com autocomplete válido e '
    f'{login_forms} formulário(s) de login com identificador autocomplete="username".'
)
