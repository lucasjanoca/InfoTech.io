
'use strict';
(function(){
const $=s=>document.querySelector(s),$$=s=>Array.from(document.querySelectorAll(s));
const year=$('[data-year]');if(year)year.textContent=String(new Date().getFullYear());
const nav=$('#navigation'),menu=$('#menu-button');
if(menu&&nav){menu.addEventListener('click',()=>{const next=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(next));menu.setAttribute('aria-label',next?'Fechar menu':'Abrir menu');nav.classList.toggle('open',next)});
$$('.main-nav a').forEach(a=>{a.addEventListener('click',()=>{nav.classList.remove('open');menu.setAttribute('aria-expanded','false');menu.setAttribute('aria-label','Abrir menu')});if(a.getAttribute('href')===location.pathname) a.setAttribute('aria-current','page')});
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&nav.classList.contains('open')){nav.classList.remove('open');menu.setAttribute('aria-expanded','false');menu.setAttribute('aria-label','Abrir menu');menu.focus()}})}
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
 if(pre&&Array.from(model.options).some(o=>o.value===pre))model.value=pre;
 const clean=v=>String(v||'').replace(/\s+/g,' ').trim();
 const safeValue=(v)=>clean(v)||'Não informado';
 const buildMessage=()=>{
   const lines=['Olá, InfoTech.io! Gostaria de solicitar uma proposta para meu projeto.','','*PEDIDO PELO SITE INFOTECH.IO*'];
   if(clean(customer?.value))lines.push('*Nome:* '+clean(customer.value));
   if(clean(business?.value))lines.push('*Negócio/marca:* '+clean(business.value));
   lines.push('*Projeto de referência:* '+(model.value?clean(model.selectedOptions[0]?.textContent):'Ideia própria, sem modelo definido'));
   lines.push('*Tipo de solução:* '+safeValue(goal.selectedOptions[0]?.textContent));
   lines.push('*Detalhes da ideia:* '+(brief.value.trim()||'Gostaria de conversar para definir os detalhes.'));
   lines.push('');
   lines.push('Gostaria de saber as possibilidades, o prazo e receber um orçamento. Obrigado!');
   return lines.join('\n');
 };
 send.addEventListener('click',()=>{
   const url='https://wa.me/5515997696477?text='+encodeURIComponent(buildMessage());
   send.href=url;
   if(feedback)feedback.textContent='O WhatsApp abrirá com seu pedido preenchido. Confira e toque em Enviar para falar com a InfoTech.io.';
 });
}
})();


/* Infotech Solutions V4, mobile switcher */
(()=>{const root=document.querySelector('.solutions-v4');if(!root)return;const bs=[...document.querySelectorAll('[data-service-tab]')],ps=[...document.querySelectorAll('[data-service-panel]')];if(!bs.length)return;
const show=id=>{for(const b of bs){const a=b.dataset.serviceTab===id;b.classList.toggle('s4-current',a);b.setAttribute('aria-pressed',String(a))}for(const p of ps)p.classList.toggle('s4-current',p.dataset.servicePanel===id);const s=document.querySelector('#s4-selected'),active=bs.find(b=>b.dataset.serviceTab===id);if(s&&active)s.textContent=active.textContent.replace(/\d+/g,'').trim()};
bs.forEach(b=>b.addEventListener('click',()=>show(b.dataset.serviceTab)));show('sites');root.classList.add('s4-ready')})();
