#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []
loaded_scripts = set()


class ScriptParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'script':
            return
        data = {k.lower(): (v or '') for k, v in attrs}
        src = data.get('src', '').strip()
        if src:
            self.scripts.append(src)


def local_script_path(raw: str, source: Path):
    value = (raw or '').strip()
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        return None
    path = unquote(parsed.path)
    if not path:
        return None
    if path.startswith('/'):
        return ROOT / path.lstrip('/')
    return source.parent / path


# Protege chamadas literais que abrem uma nova aba. O terceiro argumento precisa
# declarar noopener para impedir que a nova página receba acesso a window.opener.
window_open_blank = re.compile(
    r"window\.open\s*\(\s*[^,]+,\s*(['\"])_blank\1(?P<features>[^)]*)\)",
    re.IGNORECASE | re.DOTALL,
)

for page in sorted(ROOT.glob('*.html')):
    parser = ScriptParser()
    try:
        parser.feed(page.read_text(encoding='utf-8'))
    except Exception as exc:
        errors.append(f'{page.name}: HTML não pôde ser analisado: {exc}')
        continue

    for src in parser.scripts:
        target = local_script_path(src, page)
        if target is None or target.suffix.lower() != '.js' or not target.exists():
            continue
        loaded_scripts.add(target.resolve())

for script in sorted(loaded_scripts):
    try:
        text = script.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        continue

    for match in window_open_blank.finditer(text):
        features = match.group('features').lower()
        if 'noopener' not in features:
            relative = script.relative_to(ROOT.resolve())
            line = text.count('\n', 0, match.start()) + 1
            errors.append(
                f'{relative}:{line}: window.open para _blank sem noopener explícito'
            )

if errors:
    print('Aberturas JavaScript em nova aba sem isolamento não são permitidas:', file=sys.stderr)
    for error in errors:
        print(f'- {error}', file=sys.stderr)
    raise SystemExit(1)

print(f'OK: {len(loaded_scripts)} script(s) de produção sem window.open(_blank) inseguro.')
