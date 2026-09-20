#!/usr/bin/env python3
from pathlib import Path
import re

source = Path('css/jss/v6-app.js').read_text(encoding='utf-8')

required_helpers = {
    'safeLocalGet': r'function\s+safeLocalGet\s*\(',
    'safeLocalSet': r'function\s+safeLocalSet\s*\(',
    'safeLocalRemove': r'function\s+safeLocalRemove\s*\(',
    'safeSessionGet': r'function\s+safeSessionGet\s*\(',
    'safeSessionSet': r'function\s+safeSessionSet\s*\(',
    'safeSessionRemove': r'function\s+safeSessionRemove\s*\(',
}

missing = [name for name, pattern in required_helpers.items() if not re.search(pattern, source)]
if missing:
    raise SystemExit('Missing fail-safe Web Storage helpers: ' + ', '.join(missing))

# Web Storage is optional UX state. Reads/writes/removals outside the helper bodies must not
# be able to abort authentication, registration, confirmation or a successful request.
stripped = source
for name in required_helpers:
    pattern = re.compile(rf'function\s+{name}\s*\([^)]*\)\s*\{{.*?\}}', re.S)
    stripped = pattern.sub('', stripped)

forbidden = re.findall(r'\b(?:localStorage|sessionStorage)\s*\.\s*(?:getItem|setItem|removeItem)\s*\(', stripped)
if forbidden:
    raise SystemExit(f'Found {len(forbidden)} direct Web Storage access(es) outside fail-safe helpers')

# Destination validation must remain authoritative before persisted redirect state is used.
if 'safeDestination' not in source or "'painel-cliente.html'" not in source:
    raise SystemExit('Safe destination validation/fallback is missing')

# The request success page must retain a non-sensitive fallback protocol when storage is unavailable.
if 'INF-0000' not in source:
    raise SystemExit('Request success fallback protocol is missing')

print('V6 Web Storage resilience audit passed.')
