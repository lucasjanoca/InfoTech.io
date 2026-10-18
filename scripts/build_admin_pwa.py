#!/usr/bin/env python3
"""Build a separate, admin-only static deployment from the existing admin pages.

Run: python3 scripts/build_admin_pwa.py
Cloudflare Pages: build command above; output directory: dist-admin.
The GitHub Pages client deployment is intentionally untouched during migration.
"""
from __future__ import annotations

import json
import re
import shutil
import struct
import zlib
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist-admin'
CLIENT_ORIGIN = 'https://infotech-io.com.br'
ADMIN_PAGES = (
    'admin-install.html', 'admin-login.html', 'painel-admin.html',
    'admin-seguranca.html', 'admin-solicitacao.html', 'clientes-admin.html',
    'cliente-admin.html', 'solicitacoes-antigas.html',
)
ADMIN_SET = set(ADMIN_PAGES)
JS_FILES = (
    'v6-admin.js', 'supabase-config.js', 'header-account-clean.js',
    'mfa-recovery.js',
)
HEADER = '''<header class="site-header"><nav class="navbar" aria-label="Navegação administrativa">
<a class="brand" href="painel-admin.html"><img src="/icons/admin-192.png" width="48" height="48" alt=""><span class="brand-copy"><strong>InfoTech <span>ADM</span></strong><small>ADMINISTRAÇÃO • ACESSO RESTRITO</small></span></a>
<button class="menu-mobile" type="button" aria-controls="menu-principal" aria-expanded="false" aria-label="Abrir menu"><span></span><span></span><span></span></button>
<ul class="menu" id="menu-principal"><li><a href="painel-admin.html">Painel</a></li><li><a href="clientes-admin.html">Clientes</a></li><li><a href="solicitacoes-antigas.html">Histórico</a></li><li><a href="admin-seguranca.html">Segurança</a></li><li><button type="button" id="admin-pwa-install" hidden>Instalar InfoTech ADM</button></li><li><a href="admin-install.html">Como instalar</a></li><li><a href="https://infotech-io.com.br/" rel="noopener">Site de clientes ↗</a></li></ul></nav></header>'''
FOOTER = '''<footer class="admin-app-footer"><strong>InfoTech ADM · Ambiente administrativo</strong>
<p><a href="painel-admin.html">Painel</a> · <a href="admin-seguranca.html">MFA</a> · <a href="admin-install.html">Instalar aplicativo</a></p>
<small>© <span data-year></span> InfoTech.io · As operações dependem das permissões do Supabase.</small></footer>'''


def write_png(path: Path, size: int) -> None:
    """Generate real PNG icons with a distinct ADM monogram; no build dependencies."""
    pixels = bytearray(size * size * 4)
    background, accent, white = (8, 19, 28, 255), (22, 214, 186, 255), (246, 255, 252, 255)
    def rect(x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int, int]) -> None:
        for y in range(max(0, y0), min(size, y1)):
            for x in range(max(0, x0), min(size, x1)):
                offset = (y * size + x) * 4
                pixels[offset:offset + 4] = bytes(color)
    rect(0, 0, size, size, background)
    edge = size // 13
    rect(edge, edge, size-edge, edge+max(3, size//55), accent)
    rect(edge, size-edge-max(3, size//55), size-edge, size-edge, accent)
    rect(edge, edge, edge+max(3, size//55), size-edge, accent)
    rect(size-edge-max(3, size//55), edge, size-edge, size-edge, accent)
    glyphs = {
        'A': ('01110','10001','10001','11111','10001','10001','10001'),
        'D': ('11110','10001','10001','10001','10001','10001','11110'),
        'M': ('10001','11011','10101','10101','10001','10001','10001'),
    }
    scale = max(2, size // 29)
    width = (5 * 3 + 2 * 1) * scale
    xstart, ystart = (size-width)//2, (size-7*scale)//2
    for index, glyph in enumerate('ADM'):
        for row, bits in enumerate(glyphs[glyph]):
            for col, bit in enumerate(bits):
                if bit == '1':
                    x = xstart + (index*6+col)*scale
                    y = ystart + row*scale
                    rect(x, y, x+scale, y+scale, white)
    raw = b''.join(b'\0' + pixels[y*size*4:(y+1)*size*4] for y in range(size))
    def chunk(tag: bytes, value: bytes) -> bytes:
        return struct.pack('>I', len(value)) + tag + value + struct.pack('>I', zlib.crc32(tag+value) & 0xffffffff)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def localize_links(html: str) -> str:
    """All non-administrative HTML links leave the admin origin."""
    def replace(match: re.Match[str]) -> str:
        quote, value = match.group(1), match.group(2)
        parsed = urlsplit(value)
        if parsed.scheme or value.startswith(('#', '//')):
            return match.group(0)
        target = parsed.path.lstrip('/')
        if target in ADMIN_SET or not (target == '' or target.endswith('.html')):
            return match.group(0)
        return f'href={quote}{CLIENT_ORIGIN}/{value.lstrip("/")}{quote}'
    return re.sub(r'href=(\"|\')(.*?)\1', replace, html, flags=re.I)


def transform(page: str) -> str:
    html = (ROOT / page).read_text(encoding='utf-8')
    html, count = re.subn(r'<link\b(?=[^>]*\brel="manifest")[^>]*>',
                          '<link rel="manifest" href="/admin-manifest.webmanifest">', html, flags=re.I)
    if count != 1:
        raise ValueError(f'{page}: expected exactly one existing manifest, found {count}')
    html = re.sub(r'<link\b(?=[^>]*\brel="(?:icon|apple-touch-icon)")[^>]*>',
                  lambda m: '<link rel="apple-touch-icon" href="/icons/admin-192.png">' if 'apple-touch-icon' in m.group(0) else '<link rel="icon" href="/icons/admin-192.png">', html, flags=re.I)
    html = re.sub(r'<meta\b[^>]*\bname="(?:application-name|apple-mobile-web-app-title)"[^>]*>',
                  lambda m: re.sub(r'content="[^"]*"', 'content="InfoTech ADM"', m.group(0)), html, flags=re.I)
    html = re.sub(r'(<title>).*?(</title>)', lambda m: m.group(1) + re.sub(r'InfoTech(?:\.io)?(?: ADM)?', 'InfoTech ADM', m.group(0)[len(m.group(1)):-len(m.group(2))], count=1) + m.group(2), html, count=1, flags=re.S)
    html = html.replace('</head>', '<link rel="stylesheet" href="/css/admin-app.css">\n</head>', 1)
    if page == 'admin-install.html':
        html = html.replace('Instalar app ADM</button>', 'Instalar InfoTech ADM</button>')
        html = html.replace('<div class="secure">', '<p id="install-guidance" class="secure" role="note"></p>\n<div class="secure">', 1)
        html, scripts = re.subn(r'<script(?:\s[^>]*)?>.*?</script>', '<script src="/css/jss/admin-install.js" defer></script>', html, flags=re.S | re.I)
        if scripts != 1:
            raise ValueError('admin-install.html: unexpected script count')
        html = re.sub(r"script-src 'self' 'sha256-[^']+'", "script-src 'self'", html)
        html = html.replace('data-sw="/sw.js"', 'data-sw="/admin-sw.js"')
    else:
        html, header_count = re.subn(r'<header class="site-header">.*?</header>', HEADER, html, count=1, flags=re.S)
        html, footer_count = re.subn(r'<footer class="site-footer[^\"]*">.*?</footer>', FOOTER, html, count=1, flags=re.S)
        if header_count != 1 or footer_count != 1:
            raise ValueError(f'{page}: admin header/footer structure changed')
        html, ui_count = re.subn(r'<script\b(?=[^>]*src="css/jss/v6-ui\.js[^\"]*")[^>]*></script>',
                                 '<script defer src="/css/jss/admin-ui.js"></script>', html, flags=re.I)
        if ui_count != 1:
            raise ValueError(f'{page}: could not replace client UI/PWA script')
    html = localize_links(html)
    if re.search(r'<link\b(?=[^>]*\brel="manifest")[^>]*manifest\.webmanifest', html, re.I) is None:
        raise ValueError(f'{page}: manifest lost')
    return html


def build() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    # Copy only admin documents and their shared static dependencies; no public HTML,
    # public service worker, client application JS, or project secrets are deployed.
    for page in ADMIN_PAGES:
        (OUT / page).write_text(transform(page), encoding='utf-8')
    shutil.copyfile(OUT / 'admin-install.html', OUT / 'index.html')
    shutil.copytree(ROOT / 'assets', OUT / 'assets')
    for source in (ROOT / 'css').rglob('*.css'):
        destination = OUT / source.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    scripts = OUT / 'css' / 'jss'
    scripts.mkdir(parents=True, exist_ok=True)
    for name in JS_FILES:
        shutil.copyfile(ROOT / 'css' / 'jss' / name, scripts / name)
    for name in ('admin-ui.js', 'admin-install.js'):
        shutil.copyfile(ROOT / 'admin-app' / name, scripts / name)
    shutil.copyfile(ROOT / 'admin-app' / 'admin-app.css', OUT / 'css' / 'admin-app.css')
    shutil.copyfile(ROOT / 'admin-app' / 'admin-sw.js', OUT / 'admin-sw.js')
    for size in (192, 512):
        write_png(OUT / 'icons' / f'admin-{size}.png', size)
    manifest = {
        'id': '/infotech-adm', 'name': 'InfoTech ADM', 'short_name': 'InfoTech ADM',
        'description': 'Administração independente da InfoTech.io', 'lang': 'pt-BR',
        'start_url': '/admin-login.html', 'scope': '/', 'display': 'standalone',
        'background_color': '#08131c', 'theme_color': '#08131c',
        'icons': [
            {'src': f'/icons/admin-{size}.png', 'sizes': f'{size}x{size}', 'type': 'image/png', 'purpose': 'any'}
            for size in (192, 512)
        ],
    }
    (OUT / 'admin-manifest.webmanifest').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    # Cloudflare Pages uses this file. Private routes and authorization responses
    # remain network-only and cannot be stored by the browser or CDN.
    (OUT / '_headers').write_text("""/*
  X-Robots-Tag: noindex, nofollow, noarchive
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: DENY
  Cache-Control: no-store
  Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; script-src-attr 'none'; style-src 'self' 'sha256-o+qTNUkd8EibA65r8cv82mGLWx/m4RdP6z/dOkDT5jM='; img-src 'self' data: blob: https://rgngqumqzylthdiazvfu.supabase.co; connect-src 'self' https://rgngqumqzylthdiazvfu.supabase.co wss://rgngqumqzylthdiazvfu.supabase.co; font-src 'self' data:; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; manifest-src 'self'; worker-src 'self'; upgrade-insecure-requests

/admin-sw.js
  Cache-Control: no-cache, no-store, must-revalidate
  Service-Worker-Allowed: /
""", encoding='utf-8')
    print(f'Built {len(ADMIN_PAGES)} admin routes at {OUT.relative_to(ROOT)}/')


if __name__ == '__main__':
    build()
