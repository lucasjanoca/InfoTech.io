#!/usr/bin/env python3
from pathlib import Path
import re

source = Path('css/jss/v6-app.js').read_text(encoding='utf-8')

required_helpers = {
    'safeLocalGet': ('localStorage', 'getItem'),
    'safeLocalSet': ('localStorage', 'setItem'),
    'safeLocalRemove': ('localStorage', 'removeItem'),
    'safeSessionGet': ('sessionStorage', 'getItem'),
    'safeSessionSet': ('sessionStorage', 'setItem'),
    'safeSessionRemove': ('sessionStorage', 'removeItem'),
}


def function_span(text, name):
    """Return a named function span, balancing braces so nested try/catch is handled safely."""
    match = re.search(rf'function\s+{name}\s*\([^)]*\)\s*\{{', text)
    if not match:
        return None
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
    return match.start(), index


missing = [name for name in required_helpers if function_span(source, name) is None]
if missing:
    raise SystemExit('Missing fail-safe Web Storage helpers: ' + ', '.join(missing))

# A helper name alone is not enough: each helper must actually perform its intended storage
# operation inside a try/catch boundary so blocked/private Web Storage cannot abort UX flows.
for name, (storage, method) in required_helpers.items():
    start, end = function_span(source, name)
    body = source[start:end]
    operation = rf'\b{storage}\s*\.\s*{method}\s*\('
    if not re.search(operation, body):
        raise SystemExit(f'{name} does not call {storage}.{method}')
    if not re.search(r'\btry\s*\{', body) or not re.search(r'\bcatch\s*\(', body):
        raise SystemExit(f'{name} must contain a try/catch fail-safe boundary')

# Web Storage is optional UX state. Reads/writes/removals outside the helper bodies must not
# be able to abort authentication, registration, confirmation or a successful request.
stripped = source
spans = sorted((function_span(source, name) for name in required_helpers), reverse=True)
for start, end in spans:
    stripped = stripped[:start] + stripped[end:]

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
