import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join, resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const files = [
  'index.html',
  'projetos/index.html',
  'solucoes/index.html',
  'estudio/index.html',
  'contato/index.html',
];

const html = new Map(files.map((file) => [file, readFileSync(join(root, file), 'utf8')]));
const home = html.get('index.html');
const contact = html.get('contato/index.html');
const projects = JSON.parse(readFileSync(join(root, 'projects.json'), 'utf8'));

assert.equal(projects.length, 8, 'A quantidade de projetos mudou; atualize a prova da home.');
assert.match(home, /8 projetos apresentados/);
assert.match(home, /class="trust-rail/);
assert.match(home, /class="outcome-grid/);
assert.match(home, /class="case-proof-grid/);
assert.match(home, /class="path-grid/);
assert.match(home, /class="process-flow/);
assert.match(home, /class="home-faq/);

for (const [file, source] of html) {
  assert.equal((source.match(/<h1\b/gi) || []).length, 1, `${file} deve ter exatamente um H1.`);
  assert.match(source, /<html lang="pt-BR">/, `${file} deve declarar o idioma.`);
  assert.match(source, /<meta name="viewport"/, `${file} deve ter viewport responsivo.`);
  assert.match(source, /class="skip-link"/, `${file} deve manter o link de salto.`);
}

const allHtmlFiles = readdirSync(root, { recursive: true })
  .filter((file) => typeof file === 'string' && file.endsWith('.html') && !file.startsWith('.git'));
for (const file of allHtmlFiles) {
  const source = readFileSync(join(root, file), 'utf8');
  for (const match of source.matchAll(/(?:href|src)="(\/[^"]*)"/g)) {
    const target = decodeURIComponent(match[1].split(/[?#]/)[0]);
    let localPath = join(root, target.slice(1));
    if (existsSync(localPath) && statSync(localPath).isDirectory()) localPath = join(localPath, 'index.html');
    assert.ok(existsSync(localPath), `${file} aponta para um caminho ausente: ${match[1]}`);
  }
}

for (const match of home.matchAll(/<img\b[^>]*>/gi)) {
  assert.match(match[0], /\balt="[^"]*"/, `Imagem da home sem atributo alt: ${match[0]}`);
  const src = match[0].match(/\bsrc="([^"]+)"/)?.[1];
  if (src?.startsWith('/')) assert.ok(existsSync(join(root, src.slice(1))), `Imagem ausente: ${src}`);
  if (src?.includes('/covers/')) assert.match(match[0], /\balt="[^"]+"/, `Capa sem descrição: ${match[0]}`);
}

const goalValues = [...contact.matchAll(/<option value="([^"]+)">/g)].map((match) => match[1]);
for (const match of home.matchAll(/href="\/contato\/\?objetivo=([^"]+)"/g)) {
  const requestedGoal = decodeURIComponent(match[1]);
  assert.ok(goalValues.includes(requestedGoal), `Objetivo sem opção correspondente no briefing: ${requestedGoal}`);
}

const jsonLdBlocks = [...home.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)];
assert.ok(jsonLdBlocks.length > 0, 'A home deve ter dados estruturados.');
for (const block of jsonLdBlocks) JSON.parse(block[1]);
assert.match(home, /"@type": "FAQPage"/);

const js = readFileSync(join(root, 'assets/site.js'), 'utf8');
assert.match(js, /params\.get\('objetivo'\)/, 'O contato deve aceitar objetivo pré-selecionado.');
assert.match(home, /site\.css\?v=9\.5\.1/);
assert.match(contact, /site\.js\?v=8\.1\.0/);

console.log('Site smoke: OK');
