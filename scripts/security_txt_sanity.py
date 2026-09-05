#!/usr/bin/env python3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, unquote
import sys

ROOT = Path(__file__).resolve().parents[1]
SECURITY_TXT = ROOT / '.well-known' / 'security.txt'
OFFICIAL_ORIGIN = 'https://infotech-io.com.br'
OFFICIAL_CANONICAL = f'{OFFICIAL_ORIGIN}/.well-known/security.txt'
REQUIRED_FIELDS = {'Contact', 'Expires', 'Canonical', 'Policy', 'Preferred-Languages'}

errors = []

try:
    text = SECURITY_TXT.read_text(encoding='utf-8', errors='strict')
except Exception as exc:
    print(f'ERRO: security.txt não pôde ser lido: {exc}')
    sys.exit(1)

fields = {}
for line_number, raw_line in enumerate(text.splitlines(), 1):
    line = raw_line.strip()
    if not line or line.startswith('#'):
        continue
    if ':' not in line:
        errors.append(f'linha {line_number} inválida: campo sem separador')
        continue
    name, value = (part.strip() for part in line.split(':', 1))
    if not name or not value:
        errors.append(f'linha {line_number} inválida: campo ou valor vazio')
        continue
    fields.setdefault(name, []).append(value)

for field in sorted(REQUIRED_FIELDS):
    if field not in fields:
        errors.append(f'campo obrigatório ausente: {field}')

canonicals = fields.get('Canonical', [])
if canonicals != [OFFICIAL_CANONICAL]:
    errors.append(f'Canonical deve ser exatamente {OFFICIAL_CANONICAL}')


def validate_official_https_url(field: str, require_existing_local_path: bool = False) -> None:
    values = fields.get(field, [])
    if len(values) != 1:
        errors.append(f'{field} deve aparecer exatamente uma vez')
        return
    value = values[0]
    parsed = urlsplit(value)
    if parsed.scheme.lower() != 'https' or parsed.netloc.lower() != 'infotech-io.com.br':
        errors.append(f'{field} deve usar HTTPS na origem oficial -> {value}')
        return
    if parsed.username or parsed.password or parsed.port or parsed.query or parsed.fragment:
        errors.append(f'{field} não deve conter credenciais, porta, query ou fragmento -> {value}')
        return
    if require_existing_local_path:
        path = unquote(parsed.path or '/')
        target = ROOT / ('index.html' if path == '/' else path.lstrip('/'))
        if not target.exists():
            errors.append(f'{field} aponta para recurso local inexistente -> {value}')


validate_official_https_url('Contact', require_existing_local_path=True)
validate_official_https_url('Policy', require_existing_local_path=True)

expires_values = fields.get('Expires', [])
if len(expires_values) != 1:
    errors.append('Expires deve aparecer exatamente uma vez')
else:
    expires_raw = expires_values[0]
    try:
        expires = datetime.fromisoformat(expires_raw.replace('Z', '+00:00'))
        if expires.tzinfo is None:
            raise ValueError('timezone ausente')
        if expires.astimezone(timezone.utc) <= datetime.now(timezone.utc):
            errors.append(f'security.txt expirado em {expires_raw}')
    except ValueError as exc:
        errors.append(f'Expires inválido ({expires_raw}): {exc}')

languages_values = fields.get('Preferred-Languages', [])
if len(languages_values) != 1:
    errors.append('Preferred-Languages deve aparecer exatamente uma vez')
else:
    languages = {item.strip().lower() for item in languages_values[0].split(',') if item.strip()}
    if 'pt-br' not in languages:
        errors.append('Preferred-Languages deve manter pt-BR')

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} problema(s) no security.txt.')
    sys.exit(1)

print('OK: security.txt mantém origem oficial, destinos locais válidos e expiração futura.')
