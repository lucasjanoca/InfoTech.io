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


def strip_function_body(text, name):
    """Remove one named function, balancing braces so try/catch helpers are handled correctly."""
    match = re.search(rf'function\s+{name}\s*\([^)]*\)\s*\{{', text)
    if not match:
        return text
    depth = 1
    index = match.end()
    quote = None
    escaped = False
    while index < len(text) and depth:
        char = text[index]
        if quote:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == quote:
                quote = None
        elif char in "'\"`":
            quote = char
        elif char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
        index += 1
    if depth:
        raise SystemExit(f'Unbalanced helper body: {name}')
    return text[:match.start()] + text[index:]


# Web Storage is optional UX state. Reads/writes/removals outside the helper bodies must not
# be able to abort authentication, registration, confirmation or a successful request.
stripped = source
for name in required_helpers:
    stripped = strip_function_body(stripped, name)

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
