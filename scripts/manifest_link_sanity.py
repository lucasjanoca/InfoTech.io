#!/usr/bin/env python3
"""Validate PWA manifest links and install metadata on production HTML pages."""

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ADMIN_APP_ENTRY_PAGES = {
    "admin-install.html",
    "admin-login.html",
}
APPROVED_MANIFESTS = {
    "manifest.webmanifest",
    "admin-manifest.webmanifest",
}

errors: list[str] = []


class ManifestParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.manifests: list[str] = []
        self.theme_colors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key.lower(): (value or "") for key, value in attrs}

        if tag.lower() == "link":
            rel_tokens = {token.lower() for token in data.get("rel", "").split()}
            if "manifest" in rel_tokens:
                self.manifests.append(data.get("href", "").strip())
            return

        if tag.lower() == "meta" and data.get("name", "").lower() == "theme-color":
            self.theme_colors.append(data.get("content", "").strip())


def fail(message: str) -> None:
    errors.append(message)


def local_manifest_path(href: str) -> str | None:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc:
        return None
    return parsed.path.lstrip("/")


def manifest_theme_color(local_path: str) -> str | None:
    try:
        data = json.loads((ROOT / local_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{local_path}: não foi possível ler o manifest -> {exc}")
        return None

    color = data.get("theme_color")
    if not isinstance(color, str) or not color.strip():
        fail(f"{local_path}: theme_color ausente ou inválido")
        return None
    return color.strip().lower()


for html_path in sorted(ROOT.glob("*.html")):
    parser = ManifestParser()
    parser.feed(html_path.read_text(encoding="utf-8"))

    # Utility pages may intentionally omit install metadata.
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
    if local_path not in APPROVED_MANIFESTS:
        fail(f"{html_path.name}: manifest inesperado -> {local_path or href}")
        continue
    if not (ROOT / local_path).is_file():
        fail(f"{html_path.name}: manifest inexistente -> {local_path}")
        continue

    # Only the dedicated administrative install/login entry points define the
    # separate installed ADM app. Authenticated admin detail pages may remain
    # inside the main app shell without weakening authentication boundaries.
    if html_path.name in ADMIN_APP_ENTRY_PAGES and local_path != "admin-manifest.webmanifest":
        fail(f"{html_path.name}: esperado admin-manifest.webmanifest, encontrado {local_path}")

    # Pages that opt into an installable app must expose one browser theme color
    # and keep it aligned with the referenced manifest. This prevents visible
    # chrome/install UI drift without changing authentication or app boundaries.
    if len(parser.theme_colors) != 1:
        fail(f"{html_path.name}: deve declarar exatamente um meta theme-color")
        continue

    expected_color = manifest_theme_color(local_path)
    if expected_color is None:
        continue
    page_color = parser.theme_colors[0].lower()
    if page_color != expected_color:
        fail(
            f"{html_path.name}: theme-color {parser.theme_colors[0]} não corresponde "
            f"ao {local_path} ({expected_color})"
        )

if errors:
    for error in errors:
        print(f"ERROR: {error}")
    raise SystemExit(1)

print("PWA manifest link sanity check passed.")
