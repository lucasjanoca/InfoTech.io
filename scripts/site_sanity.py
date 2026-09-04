#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
errors = []


def fail(message: str) -> None:
    errors.append(message)


def local_path(raw: str, source: Path):
    value = (raw or '').strip()
    if not value or value.startswith(('#', 'data:', 'blob:', 'mailto:', 'tel:', 'javascript:')):
        return None
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        return None
    path = unquote(parsed.path)
    if not path:
        return None
    if path == '/':
        return ROOT / 'index.html'
    if path.startswith('/'):
        return ROOT / path.lstrip('/')
    return source.parent / path


class PageParser(HTMLParser):
    def __init__(self, source: Path):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.ids = set()
        self.duplicate_ids = set()
        self.has_csp = False
        self.csp = ''
        self.has_noindex = False
        self.resources = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        data = {k.lower(): (v or '') for k, v in attrs}
        element_id = data.get('id')
        if element_id:
            if element_id in self.ids:
                self.duplicate_ids.add(element_id)
            self.ids.add(element_id)

        if tag.lower() == 'meta':
            if data.get('http-equiv', '').lower() == 'content-security-policy':
                self.has_csp = True
                self.csp = data.get('content', '')
            if data.get('name', '').lower() == 'robots' and 'noindex' in data.get('content', '').lower():
                self.has_noindex = True

        resource_attr = None
        if tag.lower() in {'script', 'img', 'source'}:
            resource_attr = 'src'
        elif tag.lower() == 'link':
            resource_attr = 'href'

        if resource_attr and data.get(resource_attr):
            self.resources.append(data[resource_attr])
            if tag.lower() == 'script':
                self.scripts.append(data[resource_attr])


private_pages = {
    'admin-login.html', 'admin-seguranca.html', 'admin-solicitacao.html',
    'painel-admin.html', 'cliente-admin.html', 'clientes-admin.html',
    'painel-cliente.html', 'detalhes-solicitacao.html', 'perfil.html',
    'nova-solicitacao.html', 'recuperar-senha.html', 'login.html', 'cadastro.html',
}

# Somente chaves exclusivas do armazenamento persistente do fluxo demo.
# infotechLastProtocol não entra aqui: a produção usa essa chave em sessionStorage
# apenas para levar o protocolo recém-criado à tela de sucesso.
demo_storage_markers = {
    'infotechDemoRequests',
    'infotechDemoUser',
}

for page in sorted(ROOT.glob('*.html')):
    parser = PageParser(page)
    try:
        parser.feed(page.read_text(encoding='utf-8'))
    except Exception as exc:
        fail(f'{page.name}: HTML não pôde ser analisado: {exc}')
        continue

    if parser.duplicate_ids:
        fail(f'{page.name}: IDs duplicados: {sorted(parser.duplicate_ids)}')
    if not parser.has_csp:
        fail(f'{page.name}: CSP ausente')
    elif "'unsafe-inline'" in parser.csp:
        fail(f'{page.name}: CSP permite unsafe-inline')
    if page.name in private_pages and not parser.has_noindex:
        fail(f'{page.name}: página privada sem noindex')

    for ref in parser.resources:
        target = local_path(ref, page)
        if target is not None and not target.exists():
            fail(f'{page.name}: recurso local inexistente -> {ref}')

    for ref in parser.scripts:
        target = local_path(ref, page)
        if target is None or not target.exists() or target.suffix.lower() != '.js':
            continue
        try:
            script_text = target.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        found_markers = sorted(marker for marker in demo_storage_markers if marker in script_text)
        if found_markers:
            relative_target = target.resolve().relative_to(ROOT.resolve())
            fail(
                f'{page.name}: script de produção {relative_target} contém armazenamento demo: '
                f'{", ".join(found_markers)}'
            )


def validate_manifest(manifest_path: Path) -> None:
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    except Exception as exc:
        fail(f'{manifest_path.name} inválido: {exc}')
        return

    for field in ('start_url', 'scope'):
        value = manifest.get(field)
        if not isinstance(value, str) or not value.strip():
            fail(f'{manifest_path.name}: {field} ausente ou inválido')

    start_url = manifest.get('start_url')
    if isinstance(start_url, str):
        target = local_path(start_url, manifest_path)
        if target is not None and not target.exists():
            fail(f'{manifest_path.name}: start_url inexistente -> {start_url}')

    icons = manifest.get('icons', [])
    if not isinstance(icons, list) or not icons:
        fail(f'{manifest_path.name}: nenhum ícone declarado')
    else:
        for index, icon in enumerate(icons, 1):
            if not isinstance(icon, dict):
                fail(f'{manifest_path.name}: ícone #{index} inválido')
                continue
            src = icon.get('src')
            if not isinstance(src, str) or not src.strip():
                fail(f'{manifest_path.name}: ícone #{index} sem src')
                continue
            target = local_path(src, manifest_path)
            if target is not None and not target.exists():
                fail(f'{manifest_path.name}: ícone inexistente -> {src}')

    shortcuts = manifest.get('shortcuts', [])
    if shortcuts is not None and not isinstance(shortcuts, list):
        fail(f'{manifest_path.name}: shortcuts deve ser uma lista')
    elif isinstance(shortcuts, list):
        for index, shortcut in enumerate(shortcuts, 1):
            if not isinstance(shortcut, dict):
                fail(f'{manifest_path.name}: atalho #{index} inválido')
                continue
            url = shortcut.get('url')
            if not isinstance(url, str) or not url.strip():
                fail(f'{manifest_path.name}: atalho #{index} sem url')
            else:
                target = local_path(url, manifest_path)
                if target is not None and not target.exists():
                    fail(f'{manifest_path.name}: atalho inexistente -> {url}')
            shortcut_icons = shortcut.get('icons', [])
            if shortcut_icons is not None and not isinstance(shortcut_icons, list):
                fail(f'{manifest_path.name}: ícones do atalho #{index} devem ser uma lista')
                continue
            for icon in shortcut_icons or []:
                if not isinstance(icon, dict):
                    fail(f'{manifest_path.name}: ícone inválido no atalho #{index}')
                    continue
                src = icon.get('src')
                if not isinstance(src, str) or not src.strip():
                    fail(f'{manifest_path.name}: ícone sem src no atalho #{index}')
                    continue
                target = local_path(src, manifest_path)
                if target is not None and not target.exists():
                    fail(f'{manifest_path.name}: ícone de atalho inexistente -> {src}')


for manifest_name in ('manifest.webmanifest', 'admin-manifest.webmanifest'):
    validate_manifest(ROOT / manifest_name)

try:
    ET.parse(ROOT / 'sitemap.xml')
except Exception as exc:
    fail(f'sitemap.xml inválido: {exc}')

robots = (ROOT / 'robots.txt').read_text(encoding='utf-8', errors='replace')
if 'Sitemap: https://infotech-io.com.br/sitemap.xml' not in robots:
    fail('robots.txt não aponta para o sitemap oficial')

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} problema(s).')
    sys.exit(1)

print(f'OK: {len(list(ROOT.glob("*.html")))} páginas verificadas sem referências locais quebradas.')
