from pathlib import Path
import re

APP = Path('css/jss/v6-app.js')
text = APP.read_text(encoding='utf-8')

# v6-app may use Web Storage only for these narrowly scoped UI handoff keys.
# Authentication persistence remains owned by Supabase; secrets must never be stored here.
allowed = {
    ('localStorage', 'infotech:after-confirm'),
    ('sessionStorage', 'infotech:signup-draft-v8'),
    ('sessionStorage', 'infotechLastProtocol'),
}

calls = re.findall(r"\b(localStorage|sessionStorage)\.(?:getItem|setItem|removeItem)\(\s*(['\"])([^'\"]+)\2", text)
seen = {(storage, key) for storage, _quote, key in calls}
unexpected = sorted(seen - allowed)

if unexpected:
    raise SystemExit('Unexpected Web Storage keys in v6-app.js: ' + ', '.join(f'{storage}:{key}' for storage, key in unexpected))

missing = sorted(allowed - seen)
if missing:
    raise SystemExit('Expected Web Storage boundary changed; review and update this audit intentionally: ' + ', '.join(f'{storage}:{key}' for storage, key in missing))

for forbidden in ('service_role', 'supabase_service_role_key'):
    if forbidden in text.lower():
        raise SystemExit(f'Forbidden privileged credential marker in v6-app.js: {forbidden}')

print(f'Web Storage boundary OK: {len(calls)} calls across {len(seen)} approved keys.')
