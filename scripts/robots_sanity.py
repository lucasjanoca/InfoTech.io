#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ROBOTS = ROOT / 'robots.txt'
OFFICIAL_SITEMAP = 'https://infotech-io.com.br/sitemap.xml'

# Rotas que não devem ser promovidas por mecanismos de busca. robots.txt não é
# controle de acesso; esta auditoria apenas reduz exposição acidental de rotas
# privadas/operacionais enquanto o noindex e as proteções reais continuam ativos.
SENSITIVE_PATHS = {
    '/admin-install.html',
    '/admin-login.html',
    '/admin-seguranca.html',
    '/admin-solicitacao.html',
    '/painel-admin.html',
    '/cliente-admin.html',
    '/clientes-admin.html',
    '/painel-cliente.html',
    '/detalhes-solicitacao.html',
    '/perfil.html',
    '/nova-solicitacao.html',
    '/recuperar-senha.html',
    '/login.html',
    '/cadastro.html',
    '/email-confirmado.html',
    '/solicitacao-enviada.html',
}

errors = []
text = ROBOTS.read_text(encoding='utf-8', errors='strict')
lines = []
for raw_line in text.splitlines():
    line = raw_line.split('#', 1)[0].strip()
    if line:
        lines.append(line)

sitemaps = [
    line.split(':', 1)[1].strip()
    for line in lines
    if line.lower().startswith('sitemap:')
]
if sitemaps != [OFFICIAL_SITEMAP]:
    errors.append(
        'robots.txt deve declarar exatamente uma vez o sitemap oficial '
        f'({OFFICIAL_SITEMAP})'
    )

rules = []
active_agents = []
for line in lines:
    if ':' not in line:
        continue
    key, value = (part.strip() for part in line.split(':', 1))
    key_lower = key.lower()
    if key_lower == 'user-agent':
        if not active_agents or rules and rules[-1][0] == '__group_break__':
            active_agents = []
        active_agents.append(value.lower())
        continue
    if key_lower in {'allow', 'disallow'}:
        if not active_agents:
            continue
        if '*' in active_agents:
            rules.append((key_lower, value))
        # Depois da primeira regra, um novo User-agent começa outro grupo.
        active_agents = list(active_agents)

# Reprocessamento simples e explícito dos grupos para evitar ambiguidades.
star_rules = []
current_agents = []
seen_rule_in_group = False
for line in lines:
    if ':' not in line:
        continue
    key, value = (part.strip() for part in line.split(':', 1))
    key_lower = key.lower()
    if key_lower == 'user-agent':
        if seen_rule_in_group:
            current_agents = []
            seen_rule_in_group = False
        current_agents.append(value.lower())
    elif key_lower in {'allow', 'disallow'}:
        seen_rule_in_group = True
        if '*' in current_agents and value:
            star_rules.append((key_lower, value))

if not star_rules:
    errors.append('robots.txt não possui regras para User-agent: *')


def path_is_disallowed(path: str) -> bool:
    matches = [(kind, pattern) for kind, pattern in star_rules if path.startswith(pattern)]
    if not matches:
        return False
    longest = max(len(pattern) for _, pattern in matches)
    strongest = [(kind, pattern) for kind, pattern in matches if len(pattern) == longest]
    # Em empate, Allow deve vencer, conforme comportamento comum dos crawlers.
    return all(kind == 'disallow' for kind, _ in strongest)


for path in sorted(SENSITIVE_PATHS):
    if not path_is_disallowed(path):
        errors.append(f'rota sensível não está efetivamente bloqueada no robots.txt: {path}')

if errors:
    for error in errors:
        print(f'ERRO: {error}')
    print(f'FALHOU: {len(errors)} problema(s) no robots.txt.')
    sys.exit(1)

print(f'OK: robots.txt mantém {len(SENSITIVE_PATHS)} rotas sensíveis fora da indexação pretendida.')
