#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ('manifest.webmanifest', 'admin-manifest.webmanifest')
EXPECTED_CATEGORIES = ['business', 'productivity', 'utilities']
errors = []


def fail(message: str) -> None:
    errors.append(message)


for name in MANIFESTS:
    path = ROOT / name
    try:
        manifest = json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        fail(f'{name}: manifesto inválido: {exc}')
        continue

    categories = manifest.get('categories')
    if not isinstance(categories, list) or not categories:
        fail(f'{name}: categories deve permanecer uma lista não vazia')
        continue

    if any(not isinstance(category, str) or not category.strip() for category in categories):
        fail(f'{name}: categories deve conter apenas valores de texto não vazios')
        continue

    normalized = [category.strip().lower() for category in categories]
    if categories != normalized:
        fail(f'{name}: categories deve permanecer normalizado em minúsculas e sem espaços externos')

    if len(normalized) != len(set(normalized)):
        fail(f'{name}: categories não deve conter valores duplicados')

    if normalized != EXPECTED_CATEGORIES:
        fail(
            f'{name}: categories deve permanecer {EXPECTED_CATEGORIES!r} '
            'para manter a identidade instalada consistente'
        )

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} problema(s).')
    sys.exit(1)

print('OK: categorias dos manifests PWA permanecem válidas, normalizadas e consistentes.')
