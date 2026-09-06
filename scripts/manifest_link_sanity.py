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
ADMIN_INSTALL_META = {
    "application-name": "InfoTech.io ADM",
    "mobile-web-app-capable": "yes",
    "apple-mobile-web-app-capable": "yes",
    "apple-mobile-web-app-status-bar-style": "default",
    "apple-mobile-web-app-title": "InfoTech.io ADM",
}
ADMIN_TOUCH_ICON = "assets/brand/logo-192.webp"

errors: list[str] = []


class ManifestParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.manifests: list[str] = []
        self.touch_icons: list[str] = []
        self.theme_colors: list[str] = []
        self.meta: dict[str, list[str]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key.lower(): (value or "") for key, value in attrs}

        if tag.lower() == "link":
            rel_tokens = {token.lower() for token in data.get("rel", "").split()}
            if "manifest" in rel_tokens:
                self.manifests.append(data.get("href", "").strip())
            if "apple-touch-icon" in rel_tokens:
                self.touch_icons.append(data.get("href", "").strip())
            return

        if tag.lower() == "meta":
            name = data.get("name", "").lower()
            if not name:
                return
            value = data.get("content", "").strip()
            self.meta.setdefault(name, []).append(value)
            if name == "theme-color":
                self.theme_colors.append(value)


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
    if html_path.name in ADMIN_APP_ENTRY_PAGES:
        if local_path != "admin-manifest.webmanifest":
            fail(f"{html_path.name}: esperado admin-manifest.webmanifest, encontrado {local_path}")

        # Keep standalone/mobile metadata aligned on both routes that users can
        # enter through when installing or launching the ADM app, including iOS.
        for name, expected in ADMIN_INSTALL_META.items():
            values = parser.meta.get(name, [])
            if len(values) != 1:
                fail(f"{html_path.name}: deve declarar exatamente um meta {name}")
                continue
            if values[0] != expected:
                fail(f"{html_path.name}: meta {name} deve ser {expected!r}, encontrado {values[0]!r}")

        # iOS still relies on apple-touch-icon for the installed home-screen
        # artwork. Keep a single local, repository-backed icon on both ADM
        # entry points so an external or missing asset cannot silently degrade
        # the installed app identity.
        if len(parser.touch_icons) != 1:
            fail(f"{html_path.name}: deve declarar exatamente um rel=apple-touch-icon")
        else:
            touch_icon = local_manifest_path(parser.touch_icons[0])
            if touch_icon is None:
                fail(f"{html_path.name}: apple-touch-icon deve permanecer na mesma origem")
            elif touch_icon != ADMIN_TOUCH_ICON:
                fail(
                    f"{html_path.name}: apple-touch-icon deve ser {ADMIN_TOUCH_ICON}, "
                    f"encontrado {touch_icon or parser.touch_icons[0]}"
                )
            elif not (ROOT / touch_icon).is_file():
                fail(f"{html_path.name}: apple-touch-icon inexistente -> {touch_icon}")

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
