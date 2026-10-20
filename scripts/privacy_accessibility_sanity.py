#!/usr/bin/env python3
"""Static release regression checks, not a legal or WCAG certification."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit
import re
ROOT=Path(__file__).resolve().parents[1]
errors=[]
class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.tags=[]
    def handle_starttag(self,tag,attrs):self.tags.append((tag,dict(attrs)))
policies=['privacidade.html','termos.html','reembolso.html','cookies.html','acessibilidade.html','informacoes-legais.html']
loaded=set()
for file in sorted(ROOT.glob('*.html')):
    text=file.read_text();page=Page();page.feed(text)
    ids=[a['id'] for _,a in page.tags if 'id' in a]
    if len(ids)!=len(set(ids)):errors.append(f'{file.name}: duplicate ID')
    for tag,a in page.tags:
        if tag=='img' and 'alt' not in a:errors.append(f'{file.name}: image lacks alt')
        if tag=='script' and a.get('src'):
            u=urlsplit(a['src'])
            if u.netloc:
                if u.netloc!='cdn.jsdelivr.net' or not u.path.startswith('/npm/@supabase/supabase-js@'):
                    errors.append(f'{file.name}: unreviewed script origin: {u.netloc}')
            else:loaded.add(ROOT/u.path.lstrip('/'))
    if 'footer-legal-links' in text:
        for policy in policies:
            if f'href="{policy}"' not in text:errors.append(f'{file.name}: missing {policy}')
    if 'accessibility-legal.css' not in text:errors.append(f'{file.name}: missing accessibility CSS')
for path in loaded:
    source=path.read_text()
    if re.search(r'\b(?:gtag|fbq)\s*\(|googletagmanager\.com|google-analytics\.com|connect\.facebook\.net|static\.hotjar\.com|clarity\.ms',source,re.I):
        errors.append(f'{path.name}: new tracker requires privacy review')
    # Review dynamically inserted remote script loaders as well.
    if re.search(r'import\s*\(\s*[\'"]https?://|importScripts\s*\(\s*[\'"]https?://',source):
        errors.append(f'{path.name}: remote dynamic import requires review')
for name in ['cadastro.html','nova-solicitacao.html']:
    text=(ROOT/name).read_text()
    for policy in ['termos.html','privacidade.html']:
        form=re.search(r'<form\b.*?</form>',text,re.S)[0]
        if f'href="{policy}"' not in form:errors.append(f'{name}: form missing {policy}')
    if re.search(r'name=[\'"](?:cpf|cnpj|birthdate|address|phone)[\'"]',text,re.I):errors.append(f'{name}: extra personal field requires review')
# WCAG sRGB luminance; test the specific corrected control colors, not all rendered UI.
def luminance(color):
    c=[int(color[i:i+2],16)/255 for i in (1,3,5)]
    c=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c]
    return sum(x*w for x,w in zip(c,[.2126,.7152,.0722]))
def contrast(a,b):
    a,b=sorted([luminance(a),luminance(b)])
    return (b+.05)/(a+.05)
for fg,bg,minimum in [('#9fb3c9','#061225',4.5),('#7892ac','#061225',3),('#67f3ff','#020611',3)]:
    ratio=contrast(fg,bg)
    if ratio<minimum:errors.append(f'contrast {fg}/{bg}: {ratio:.2f} < {minimum}')
if errors:raise SystemExit('\n'.join(errors))
print(f'OK: {len(list(ROOT.glob("*.html")))} pages; policies, alt, script origins, minimal forms and corrected color pairs.')
