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

# Resolve simple const aliases so the audit covers both literal keys and deliberately
# named keys such as signupDraftKey without requiring production code to inline them.
constants = {
    name: value
    for name, _quote, value in re.findall(
        r"\bconst\s+([A-Za-z_$][\w$]*)\s*=\s*(['\"])([^'\"]+)\2\s*;",
        text,
    )
}

# Production call sites must go through the fail-safe helpers. The resilience audit
# separately verifies that each helper is a real try/catch wrapper around Web Storage
# and that no direct getItem/setItem/removeItem calls remain outside those helpers.
helper_pattern = re.compile(
    r"\b(safeLocal|safeSession)(?:Get|Set|Remove)\(\s*"
    r"(?:(['\"])([^'\"]+)\2|([A-Za-z_$][\w$]*))"
)

seen = set()
call_count = 0
for family, _quote, literal_key, alias in helper_pattern.findall(text):
    call_count += 1
    storage = 'localStorage' if family == 'safeLocal' else 'sessionStorage'
    if literal_key:
        key = literal_key
    else:
        key = constants.get(alias)
        if key is None:
            raise SystemExit(
                f'Web Storage key alias must resolve to a local string const: {storage}:{alias}'
            )
    seen.add((storage, key))

unexpected = sorted(seen - allowed)
if unexpected:
    raise SystemExit('Unexpected Web Storage keys in v6-app.js: ' + ', '.join(f'{storage}:{key}' for storage, key in unexpected))

missing = sorted(allowed - seen)
if missing:
    raise SystemExit('Expected Web Storage boundary changed; review and update this audit intentionally: ' + ', '.join(f'{storage}:{key}' for storage, key in missing))

for forbidden in ('service_role', 'supabase_service_role_key'):
    if forbidden in text.lower():
        raise SystemExit(f'Forbidden privileged credential marker in v6-app.js: {forbidden}')

print(f'Web Storage boundary OK: {call_count} fail-safe calls across {len(seen)} approved keys.')
