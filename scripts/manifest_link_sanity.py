#!/usr/bin/env python3
"""Validate PWA manifest links on production HTML pages."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ADMIN_PAGES = {
    "admin-install.html",
    "admin-login.html",
    "admin-seguranca.html",
    "admin-solicitacao.html",
    "cliente-admin.html",
    "clientes-admin.html",
    "painel-admin.html",
}

errors: list[str] = []


class ManifestParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.manifests: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "link":
            return
        data = {key.lower(): (value or "") for key, value in attrs}
        rel_tokens = {token.lower() for token in data.get("rel", "").split()}
        if "manifest" in rel_tokens:
            self.manifests.append(data.get("href", "").strip())


def fail(message: str) -> None:
    errors.append(message)


def local_manifest_path(href: str) -> str | None:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc:
        return None
    return parsed.path.lstrip("/")


for html_path in sorted(ROOT.glob("*.html")):
    parser = ManifestParser()
    parser.feed(html_path.read_text(encoding="utf-8"))

    # Scriptless utility pages may intentionally omit install metadata.
    if not parser.manifests:
        continue

    if len(parser.manifests) != 1:
        fail(f"{html_path.name}: deve declarar exatamente um rel=manifest")
        continue

    href = parser.manifests[0]
    local_path = local_manifest_path(href)
    if local_path is None:
        fail(f"{html_path.name}: manifest deve permanecer na mesma origem")
        continue
    if local_path not in {"manifest.webmanifest", "admin-manifest.webmanifest"}:
        fail(f"{html_path.name}: manifest inesperado -> {local_path or href}")
        continue
    if not (ROOT / local_path).is_file():
        fail(f"{html_path.name}: manifest inexistente -> {local_path}")

    expected = "admin-manifest.webmanifest" if html_path.name in ADMIN_PAGES else "manifest.webmanifest"
    if local_path != expected:
        fail(f"{html_path.name}: esperado {expected}, encontrado {local_path}")

if errors:
    for error in errors:
        print(f"ERROR: {error}")
    raise SystemExit(1)

print("PWA manifest link sanity check passed.")
