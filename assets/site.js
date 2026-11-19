
'use strict';
(function(){
const $=s=>document.querySelector(s),$$=s=>Array.from(document.querySelectorAll(s));
const year=$('[data-year]');if(year)year.textContent=String(Math.max(2027,new Date().getFullYear()));
const nav=$('#navigation'),menu=$('#menu-button');
if(menu&&nav){menu.addEventListener('click',()=>{const next=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(next));menu.setAttribute('aria-label',next?'Fechar menu':'Abrir menu');nav.classList.toggle('open',next)});
$$('.main-nav a').forEach(a=>{a.addEventListener('click',()=>{nav.classList.remove('open');menu.setAttribute('aria-expanded','false')});if(a.getAttribute('href')===location.pathname) a.setAttribute('aria-current','page')});
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&nav.classList.contains('open')){nav.classList.remove('open');menu.setAttribute('aria-expanded','false');menu.focus()}})}
const cards=$$('[data-card]'),search=$('#search-project'),results=$('#results'),empty=$('#empty-search');
if(cards.length&&search){let category='Todos';
const norm=s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR');
function render(){let count=0;cards.forEach(card=>{const match=(category==='Todos'||card.dataset.category===category)&&norm(card.dataset.search).includes(norm(search.value.trim()));card.hidden=!match;if(match)count++});if(results)results.textContent=count===1?'1 projeto encontrado':count+' projetos encontrados';if(empty)empty.hidden=count>0;$$('[data-filter]').forEach(b=>{let active=b.dataset.filter===category;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active))})}
$$('[data-filter]').forEach(b=>b.addEventListener('click',()=>{category=b.dataset.filter;render()}));search.addEventListener('input',render);
const reset=$('#reset-filters');if(reset)reset.addEventListener('click',()=>{category='Todos';search.value='';render();search.focus()});render()}
const model=$('#model-select'),goal=$('#goal-select'),brief=$('#brief-description'),send=$('#send-request'),feedback=$('#brief-feedback'),customer=$('#client-name'),business=$('#business-name');
if(model&&goal&&brief&&send){
 const params=new URLSearchParams(location.search);
 const pre=params.get('modelo');
 if(pre&&Array.fr --- TRUNCATED --- 4,336 chars