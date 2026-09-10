#!/usr/bin/env python3
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'io' / 'local.html'
errors = []


def fail(message: str) -> None:
    errors.append(message)


try:
    source = TARGET.read_text(encoding='utf-8')
except Exception as exc:
    print(f'ERRO: não foi possível ler io/local.html: {exc}')
    sys.exit(1)

matches = re.findall(r"\bconst\s+OLLAMA\s*=\s*(['\"])(.*?)\1\s*;", source)
if len(matches) != 1:
    fail('io/local.html: deve declarar exatamente uma constante OLLAMA literal')
else:
    endpoint = matches[0][1].strip()
    parsed = urlsplit(endpoint)
    if parsed.scheme not in {'http', 'https'}:
        fail('io/local.html: OLLAMA deve usar um endpoint HTTP(S) explícito')
    if parsed.hostname not in {'127.0.0.1', 'localhost', '::1'}:
        fail('io/local.html: OLLAMA deve permanecer restrito ao loopback local')
    if parsed.username or parsed.password:
        fail('io/local.html: OLLAMA não deve conter credenciais na URL')
    if parsed.query or parsed.fragment:
        fail('io/local.html: OLLAMA não deve conter query ou fragmento')

remote_ollama = re.findall(r"https?://[^'\"\s)]+:11434", source, re.IGNORECASE)
for candidate in remote_ollama:
    parsed = urlsplit(candidate)
    if parsed.hostname not in {'127.0.0.1', 'localhost', '::1'}:
        fail(f'io/local.html: endpoint Ollama remoto não permitido: {candidate}')

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} problema(s).')
    sys.exit(1)

print('OK: a interface io local mantém o endpoint Ollama restrito ao loopback e sem credenciais na URL.')
