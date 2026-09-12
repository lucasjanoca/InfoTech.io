#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []

# Atributos que podem iniciar navegação, submissão ou carregamento de recursos.
URL_ATTRIBUTES = {
    'href', 'src', 'action', 'formaction', 'poster',
}


def has_ascii_control(value: str) -> bool:
    return any(ord(char) < 0x20 or ord(char) == 0x7f for char in value)


class UrlParser(HTMLParser):
    def __init__(self, page: Path):
        super().__init__(convert_charrefs=True)
        self.page = page

    def handle_starttag(self, tag, attrs):
        for attr_name, raw_value in attrs:
            name = (attr_name or '').lower()
            if name not in URL_ATTRIBUTES:
                continue
            raw = raw_value or ''
            value = raw.strip()
            if not value:
                continue

            # Espaços externos podem ser descartados durante o parsing da URL e
            # tornam o destino efetivo diferente do valor literal revisado.
            if raw != value:
                errors.append(
                    f'{self.page.name}: espaço externo não permitido em '
                    f'{tag.lower()}[{name}] -> {raw!r}'
                )
                continue

            # Espaços literais internos podem ser convertidos implicitamente para
            # %20 pelo navegador, tornando o destino efetivo diferente do valor
            # revisado no HTML. URLs publicadas devem declarar o destino canônico.
            if ' ' in value:
                errors.append(
                    f'{self.page.name}: espaço literal não permitido em '
                    f'{tag.lower()}[{name}] -> {value!r}'
                )
                continue

            # Caracteres de controle C0/DEL podem ser descartados ou normalizados por
            # parsers de URL, tornando o destino efetivo diferente do texto revisado.
            if has_ascii_control(raw):
                errors.append(
                    f'{self.page.name}: caractere de controle não permitido em '
                    f'{tag.lower()}[{name}]'
                )
                continue

            # Barras invertidas podem ser normalizadas como separadores de URL por
            # navegadores e tornam a interpretação do destino ambígua. Caminhos web
            # publicados devem usar apenas barras POSIX.
            if '\\' in value:
                errors.append(
                    f'{self.page.name}: barra invertida não permitida em '
                    f'{tag.lower()}[{name}] -> {value}'
                )
                continue

            # URLs protocol-relative herdam o esquema da página e tornam a política
            # menos explícita. Em produção, recursos/navegações externas devem declarar
            # HTTPS diretamente.
            if value.startswith('//'):
                errors.append(
                    f'{self.page.name}: URL protocol-relative não permitida em '
                    f'{tag.lower()}[{name}] -> {value}'
                )
                continue

            parsed = urlsplit(value)

            # Credenciais embutidas em URLs podem vazar em histórico, logs, capturas e
            # referências copiadas. Nenhum destino HTML de produção deve depender de
            # userinfo; autenticação deve permanecer no fluxo próprio da aplicação.
            if parsed.username is not None or parsed.password is not None:
                errors.append(
                    f'{self.page.name}: credenciais embutidas não permitidas em '
                    f'{tag.lower()}[{name}]'
                )
                continue

            if parsed.scheme.lower() == 'http':
                errors.append(
                    f'{self.page.name}: URL HTTP insegura em '
                    f'{tag.lower()}[{name}] -> {value}'
                )


for page in sorted(ROOT.glob('*.html')):
    parser = UrlParser(page)
    try:
        parser.feed(page.read_text(encoding='utf-8'))
    except Exception as exc:
        errors.append(f'{page.name}: HTML não pôde ser analisado: {exc}')

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} URL(s) insegura(s).')
    sys.exit(1)

print(
    f'OK: {len(list(ROOT.glob("*.html")))} páginas sem URLs HTTP, '
    'protocol-relative, com espaços externos/internos, barras invertidas, caracteres '
    'de controle ou credenciais embutidas em atributos navegáveis/carregáveis.'
)
