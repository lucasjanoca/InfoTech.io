#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlsplit, unquote
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITEMAP = ROOT / 'sitemap.xml'
OFFICIAL_ORIGIN = 'https://infotech-io.com.br'
PRIVATE_PAGES = {
    'admin-login.html', 'admin-seguranca.html', 'admin-solicitacao.html',
    'painel-admin.html', 'cliente-admin.html', 'clientes-admin.html',
    'painel-cliente.html', 'detalhes-solicitacao.html', 'perfil.html',
    'nova-solicitacao.html', 'recuperar-senha.html', 'login.html', 'cadastro.html',
}

errors = []

try:
    root = ET.parse(SITEMAP).getroot()
except Exception as exc:
    print(f'ERRO: sitemap.xml inválido: {exc}', file=sys.stderr)
    raise SystemExit(1)

namespace = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
loc_nodes = root.findall('sm:url/sm:loc', namespace)
if not loc_nodes:
    errors.append('sitemap.xml não contém URLs')

seen = set()
for loc in loc_nodes:
    value = (loc.text or '').strip()
    if not value:
        errors.append('sitemap.xml contém <loc> vazio')
        continue

    if value in seen:
        errors.append(f'URL duplicada no sitemap: {value}')
        continue
    seen.add(value)

    parsed = urlsplit(value)
    origin = f'{parsed.scheme}://{parsed.netloc}' if parsed.scheme and parsed.netloc else ''
    if origin != OFFICIAL_ORIGIN:
        errors.append(f'URL fora da origem oficial: {value}')
        continue

    if parsed.query or parsed.fragment:
        errors.append(f'URL de sitemap não deve conter query/fragmento: {value}')

    path = unquote(parsed.path or '/')
    page_name = Path(path).name if path != '/' else 'index.html'
    if page_name in PRIVATE_PAGES:
        errors.append(f'página privada não pode entrar no sitemap: {value}')

    target = ROOT / ('index.html' if path == '/' else path.lstrip('/'))
    if not target.exists() or not target.is_file():
        errors.append(f'URL aponta para página local inexistente: {value}')

if errors:
    for error in errors:
        print(f'ERRO: {error}', file=sys.stderr)
    print(f'FALHOU: {len(errors)} problema(s) no sitemap.', file=sys.stderr)
    raise SystemExit(1)

print(f'OK: sitemap validado com {len(seen)} URL(s) públicas da origem oficial.')
