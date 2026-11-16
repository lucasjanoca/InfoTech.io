/* InfoTech.io Showcase V1 — UI independente, sem autenticação ou dados de clientes. */
'use strict';
const $ = (selector, root = document) => root.querySelector(selector);
const state = { projects: [], category: 'Todos', query: '' };
const grid = $('#projects-grid');
const resultLabel = $('#result-label');
const emptyState = $('#empty-state');
const dialog = $('#case-dialog');
const search = $('#project-search');
const typeNames = ['Todos', 'Sites', 'Sistemas', 'Catálogos', 'Experiências'];

function node(tag, className = '', value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (value !== undefined) element.textContent = String(value);
  return element;
}
function normalize(value) {
  return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR');
}
function safeUrl(value) {
  if (!value) return '';
  try {
    const url = new URL(value);
    return url.protocol === 'https:' ? url.href : '';
  } catch {
    return '';
  }
}
function badgeType(status) {
  if (status === 'Publicado') return '';
  if (status === 'Demonstração') return ' is-demo';
  return ' is-development';
}
function externalLink(label, url) {
  const href = safeUrl(url);
  if (!href) return null;
  const link = node('a', 'project-live-link', label);
  link.href = href;
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  link.setAttribute('aria-label', label + ' (abre em nova aba)');
  return link;
}
function createPreview(project) {
  const visual = node('div', 'project-visual visual-' + project.theme);
  visual.setAttribute('aria-hidden', 'true');
  const chrome = node('div', 'screen-chrome');
  const dots = node('span', 'chrome-dots');
  for (let i = 0; i < 3; i += 1) dots.append(node('i'));
  chrome.append(dots, node('span', '', 'INFOTECH / SELECTED WORK'), node('span', '', '↗'));
  const content = node('div', 'visual-content');
  content.append(node('span', 'visual-kicker', project.kicker), node('strong', 'visual-headline', project.headline), node('i', 'visual-underline'));
  visual.append(chrome, content, node('span', 'visual-badge', 'CASE / ' + project.category.toUpperCase()), node('span', 'visual-footer', project.name.toUpperCase()));
  return visual;
}
function createCard(project) {
  const card = node('article', 'project-card' + (project.featured ? ' is-featured' : ''));
  const content = node('div', 'project-content');
  const meta = node('div', 'project-meta');
  meta.append(node('span', '', project.category), node('span', 'project-status' + badgeType(project.status), project.status));
  const description = node('p', '', project.description);
  const tags = node('div', 'project-tags');
  project.stack.slice(0, 3).forEach((item) => tags.append(node('span', '', item)));
  const actions = node('div', 'project-actions');
  const details = node('button', 'details-button', 'Conhecer projeto ↗');
  details.type = 'button';
  details.setAttribute('aria-label', 'Conhecer o projeto ' + project.name);
  details.addEventListener('click', () => openCase(project));
  actions.append(details);
  const link = externalLink('Visitar site ↗', project.demo);
  if (link) actions.append(link);
  content.append(meta, node('h3', '', project.name), description, tags, actions);
  card.append(createPreview(project), content);
  return card;
}
function visibleProjects() {
  return state.projects.filter((p) => {
    if (state.category !== 'Todos' && state.category !== p.category) return false;
    if (!state.query) return true;
    return normalize([p.name, p.category, p.kicker, p.description, p.stack.join(' ')].join(' ')).includes(normalize(state.query));
  });
}
function render() {
  const projects = visibleProjects();
  const fragment = document.createDocumentFragment();
  projects.forEach((p) => fragment.append(createCard(p)));
  grid.replaceChildren(fragment);
  emptyState.hidden = projects.length !== 0;
  resultLabel.textContent = projects.length === 1 ? '1 projeto encontrado' : projects.length + ' projetos encontrados';
  document.querySelectorAll('[data-category]').forEach((button) => {
    const active = button.dataset.category === state.category;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
}
function setCategory(value) {
  if (!typeNames.includes(value)) return;
  state.category = value;
  render();
}
function openCase(project, updateUrl = true) {
  if (!project || !dialog || typeof dialog.showModal !== 'function') return;
  $('#case-kicker').textContent = project.kicker;
  $('#case-title').textContent = project.name;
  $('#case-description').textContent = project.description;
  $('#case-status').textContent = project.status;
  $('#case-category').textContent = project.category;
  $('#case-challenge').textContent = project.challenge;
  const features = $('#case-features');
  features.replaceChildren(...project.features.map((text) => node('li', '', text)));
  const stack = $('#case-stack');
  stack.replaceChildren(...project.stack.map((text) => node('span', '', text)));
  const demo = $('#case-demo');
  demo.hidden = !safeUrl(project.demo);
  if (!demo.hidden) demo.href = safeUrl(project.demo);
  const repo = $('#case-repo');
  repo.hidden = !safeUrl(project.repo);
  if (!repo.hidden) repo.href = safeUrl(project.repo);
  if (!dialog.open) dialog.showModal();
  if (updateUrl && location.hash !== '#projeto=' + project.id) {
    history.replaceState(null, '', '#projeto=' + encodeURIComponent(project.id));
  }
}
function openHashCase() {
  if (!location.hash.startsWith('#projeto=')) return;
  const slug = decodeURIComponent(location.hash.slice('#projeto='.length));
  const project = state.projects.find((p) => p.id === slug);
  if (project) openCase(project, false);
}
function initNavigation() {
  const toggle = $('.nav-toggle');
  const nav = $('#nav-items');
  toggle.addEventListener('click', () => {
    const next = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(next));
    nav.classList.toggle('open', next);
  });
  document.querySelectorAll('[data-nav]').forEach((link) => link.addEventListener('click', () => {
    toggle.setAttribute('aria-expanded', 'false');
    nav.classList.remove('open');
  }));
  document.addEventListener('keydown', (event) => {
    const typing = event.target.matches('input, textarea, [contenteditable]');
    if (event.key === '/' && !typing && !dialog.open) {
      event.preventDefault();
      search.focus();
    }
    if (event.key === 'Escape' && nav.classList.contains('open')) {
      nav.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
      toggle.focus();
    }
  });
}
function initDialog() {
  $('#dialog-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) dialog.close();
  });
  dialog.addEventListener('close', () => {
    if (location.hash.startsWith('#projeto=')) {
      history.replaceState(null, '', location.pathname + location.search + '#trabalhos');
    }
  });
  window.addEventListener('hashchange', openHashCase);
}
async function init() {
  $('#year').textContent = String(new Date().getFullYear());
  initNavigation();
  initDialog();
  $('#filters').addEventListener('click', (event) => {
    const button = event.target.closest('[data-category]');
    if (button) setCategory(button.dataset.category);
  });
  search.addEventListener('input', () => {
    state.query = search.value.trim();
    render();
  });
  $('#clear-filters').addEventListener('click', () => {
    search.value = '';
    state.query = '';
    setCategory('Todos');
    search.focus();
  });
  try {
    const response = await fetch('./projects.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('HTTP ' + response.status);
    const data = await response.json();
    if (!Array.isArray(data)) throw new Error('Formato inesperado do catálogo');
    state.projects = data.filter((p) => p && typeof p.id === 'string' && typeNames.includes(p.category) && Array.isArray(p.features) && Array.isArray(p.stack));
    $('#project-total').textContent = String(state.projects.length).padStart(2, '0');
    $('#all-count').textContent = String(state.projects.length);
    render();
    openHashCase();
  } catch (error) {
    resultLabel.textContent = 'Não foi possível carregar os projetos no momento.';
    emptyState.hidden = false;
    $('.empty-state h3').textContent = 'O catálogo está indisponível.';
    $('.empty-state p').textContent = 'Atualize a página para tentar novamente.';
    $('#clear-filters').hidden = true;
    console.error('Showcase: falha ao carregar catálogo', error);
  }
}
init();
