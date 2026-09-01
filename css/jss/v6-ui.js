
(() => {
  'use strict';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const menuBtn=$('.menu-mobile'), menu=$('.menu');
  const closeMenu=()=>{menu?.classList.remove('ativo');menuBtn?.setAttribute('aria-expanded','false')};
  menuBtn?.addEventListener('click',e=>{e.stopPropagation();const open=menu?.classList.toggle('ativo');menuBtn.setAttribute('aria-expanded',String(Boolean(open)))});
  document.addEventListener('click',e=>{if(menu && menuBtn && !menu.contains(e.target) && !menuBtn.contains(e.target))closeMenu()});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')closeMenu()});
  $$('.menu a').forEach(a=>a.addEventListener('click',closeMenu));
  const header=$('.site-header');
  const head=()=>header?.classList.toggle('scrolled',scrollY>10);
  addEventListener('scroll',head,{passive:true});head();
  const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  const items=$$('.reveal');
  if(reduced || !('IntersectionObserver' in window)) items.forEach(x=>x.classList.add('visible'));
  else{
    const io=new IntersectionObserver((entries,o)=>entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('visible');o.unobserve(e.target)}}),{threshold:.1,rootMargin:'0px 0px -40px'});
    items.forEach((x,i)=>{x.classList.add(`reveal-delay-${Math.min(i%4,3)}`);io.observe(x)});
  }
  $$('[data-year]').forEach(x=>x.textContent=new Date().getFullYear());
  // Compatibilidade com um bug histórico do script antigo de mensagens.
  if(!globalThis.makeId) globalThis.makeId=()=>globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  // Tabs
  $$('[data-tabs]').forEach(root=>{
    const buttons=$$('[data-tab]',root), panels=$$('[data-panel]',root);
    const activate=name=>{
      buttons.forEach(b=>{const active=b.dataset.tab===name;b.classList.toggle('active',active);b.setAttribute('aria-selected',String(active))});
      panels.forEach(p=>p.hidden=p.dataset.panel!==name);
    };
    buttons.forEach(b=>b.addEventListener('click',()=>activate(b.dataset.tab)));
    if(buttons[0])activate(buttons[0].dataset.tab);
  });
  // Password strength
  $$('[data-password-meter]').forEach(input=>{
    const meter=document.getElementById(input.dataset.passwordMeter);
    if(!meter)return;
    const check=()=>{
      const v=input.value||''; let score=0;
      if(v.length>=8)score++; if(v.length>=12)score++; if(/[A-Z]/.test(v)&&/[a-z]/.test(v))score++; if(/\d/.test(v)&&/[^A-Za-z0-9]/.test(v))score++;
      meter.dataset.score=String(score);
    };
    input.addEventListener('input',check);check();
  });
})();

(() => {
  'use strict';
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;

  const logicalOf=item=>Number(item?.dataset?.loopIndex||0);
  const itemCenter=item=>item.offsetLeft+item.offsetWidth/2;
  const nearestIndex=(track,items)=>{
    const center=track.scrollLeft+track.clientWidth/2;
    let best=0,dist=Infinity;
    for(let i=0;i<items.length;i++){
      const d=Math.abs(itemCenter(items[i])-center);
      if(d<dist){dist=d;best=i}
    }
    return best;
  };
  const centerLeft=(track,item)=>itemCenter(item)-track.clientWidth/2;

  function cloneCard(node,index){
    const c=node.cloneNode(true);
    c.dataset.loopClone='true';
    c.dataset.loopIndex=String(index);
    c.removeAttribute('id');
    c.setAttribute('aria-hidden','true');
    c.querySelectorAll('[id]').forEach(x=>x.removeAttribute('id'));
    c.querySelectorAll('a,button,input,select,textarea,[tabindex]').forEach(x=>x.setAttribute('tabindex','-1'));
    c.querySelectorAll('img').forEach(img=>{img.loading='eager';img.decoding='async';img.fetchPriority='low'});
    return c;
  }

  function buildThreeRuns(track,originals){
    originals.forEach((item,i)=>item.dataset.loopIndex=String(i));
    const frag=document.createDocumentFragment();
    originals.forEach((item,i)=>frag.appendChild(cloneCard(item,i)));
    originals.forEach(item=>frag.appendChild(item));
    originals.forEach((item,i)=>frag.appendChild(cloneCard(item,i)));
    track.replaceChildren(frag);
    return [...track.children];
  }

  function dotsFor(host,count,go){
    const dots=host.querySelector('[data-carousel-dots],[data-snap-dots]') ||
      (host.nextElementSibling?.matches?.('[data-snap-dots]') ? host.nextElementSibling : null);
    if(!dots)return {update:()=>{}};
    dots.innerHTML='';
    const buttons=[];
    for(let i=0;i<count;i++){
      const b=document.createElement('button');
      b.type='button';
      b.setAttribute('aria-label',`Ir para item ${i+1}`);
      b.addEventListener('click',()=>go(i));
      dots.appendChild(b);buttons.push(b);
    }
    return {update(active){
      buttons.forEach((b,i)=>{
        const on=i===active;
        b.classList.toggle('active',on);
        b.setAttribute('aria-current',on?'true':'false');
      });
    }};
  }

  function setupLoop(track,originals,host,{autoplay=5000}={}){
    if(!track||originals.length<2)return;
    const count=originals.length;
    const items=buildThreeRuns(track,originals);
    const middleStart=count;
    let autoTimer=0, settleTimer=0, raf=0, motionRaf=0, suppressScrollUntil=0;
    let dragging=false, paused=false, active=0, programmatic=false;
    let pointerId=null, axis=null, startX=0, startY=0, startScroll=0, lastX=0, lastT=0, velocity=0, startIndex=middleStart, moved=false;

    const updateDots=()=>{
      const p=nearestIndex(track,items);
      active=logicalOf(items[p]);
      dots.update(active);
    };
    const requestDots=()=>{if(!raf)raf=requestAnimationFrame(()=>{raf=0;updateDots()})};

    const normalizeSeamless=()=>{
      const p=nearestIndex(track,items);
      const group=Math.floor(p/count);
      if(group===1)return p;
      const logical=logicalOf(items[p]);
      const source=items[p],target=items[middleStart+logical];
      if(source&&target){
        const relative=(track.scrollLeft+track.clientWidth/2)-itemCenter(source);
        suppressScrollUntil=performance.now()+120;
        track.scrollLeft=itemCenter(target)+relative-track.clientWidth/2;
        return middleStart+logical;
      }
      return p;
    };

    const stopMotion=()=>{if(motionRaf){cancelAnimationFrame(motionRaf);motionRaf=0}programmatic=false};

    const animateTo=(item,duration=250,done)=>{
      if(!item)return;
      stopMotion();programmatic=true;
      const from=track.scrollLeft,to=centerLeft(track,item);
      if(reduced||Math.abs(to-from)<1){track.scrollLeft=to;normalizeSeamless();requestDots();programmatic=false;done?.();return}
      const start=performance.now();
      const ease=t=>1-Math.pow(1-t,3);
      const tick=now=>{
        const t=Math.min(1,(now-start)/duration);
        track.scrollLeft=from+(to-from)*ease(t);
        if(t<1)motionRaf=requestAnimationFrame(tick);
        else{motionRaf=0;normalizeSeamless();requestDots();programmatic=false;done?.()}
      };
      motionRaf=requestAnimationFrame(tick);
    };

    // Pré-decodifica as imagens do carrossel para evitar flash ao cruzar as cópias do loop.
    items.forEach(item=>item.querySelectorAll?.('img').forEach(img=>{
      if(typeof img.decode==='function')img.decode().catch(()=>{});
    }));

    const schedule=()=>{
      clearTimeout(autoTimer);
      if(reduced||paused||dragging||document.hidden||autoplay<=0)return;
      autoTimer=setTimeout(()=>step(1),autoplay);
    };

    const settle=(forcedDir=0)=>{
      clearTimeout(settleTimer);
      let p=normalizeSeamless();
      if(forcedDir){
        const logicalStart=logicalOf(items[startIndex]||items[p]);
        const logicalNow=logicalOf(items[p]);
        if(logicalNow===logicalStart){p=Math.max(0,Math.min(items.length-1,p+forcedDir))}
      }
      animateTo(items[p],210,()=>{normalizeSeamless();requestDots();schedule()});
    };

    const settleSoon=()=>{
      clearTimeout(settleTimer);
      settleTimer=setTimeout(()=>settle(0),190);
    };

    const step=dir=>{
      normalizeSeamless();
      const p=nearestIndex(track,items);
      const target=items[Math.max(0,Math.min(items.length-1,p+dir))];
      animateTo(target,300,()=>{normalizeSeamless();requestDots();schedule()});
    };

    const goLogical=logical=>{
      normalizeSeamless();
      const p=nearestIndex(track,items);
      const candidates=[logical,middleStart+logical,middleStart*2+logical];
      const target=candidates.reduce((a,b)=>Math.abs(b-p)<Math.abs(a-p)?b:a,candidates[0]);
      animateTo(items[target],280,()=>{normalizeSeamless();requestDots();schedule()});
    };
    const dots=dotsFor(host,count,goLogical);

    const startPointer=e=>{
      if(e.pointerType==='mouse'&&e.button!==0)return;
      stopMotion();clearTimeout(autoTimer);clearTimeout(settleTimer);
      pointerId=e.pointerId;axis=null;dragging=true;paused=true;moved=false;
      startX=lastX=e.clientX;startY=e.clientY;startScroll=track.scrollLeft;lastT=performance.now();velocity=0;
      startIndex=nearestIndex(track,items);
      track.classList.add('is-dragging');
      try{track.setPointerCapture?.(e.pointerId)}catch(_){}
    };

    const movePointer=e=>{
      if(pointerId!==e.pointerId)return;
      const dx=e.clientX-startX,dy=e.clientY-startY;
      if(!axis&&Math.max(Math.abs(dx),Math.abs(dy))>6){
        axis=Math.abs(dx)>Math.abs(dy)*1.08?'x':'y';
        if(axis==='y'){
          dragging=false;paused=false;pointerId=null;track.classList.remove('is-dragging');schedule();return;
        }
      }
      if(axis!=='x')return;
      moved=moved||Math.abs(dx)>7;
      const now=performance.now(),dt=Math.max(8,now-lastT);
      track.scrollLeft=startScroll-dx;
      velocity=(lastX-e.clientX)/dt;
      lastX=e.clientX;lastT=now;
      requestDots();
      e.preventDefault();
    };

    const endPointer=e=>{
      if(pointerId!==e.pointerId&&pointerId!==null)return;
      const dx=(e?.clientX??lastX)-startX;
      pointerId=null;track.classList.remove('is-dragging');dragging=false;paused=false;
      suppressScrollUntil=performance.now()+140;
      if(axis!=='x'){axis=null;schedule();return}
      axis=null;
      const traveled=track.scrollLeft-startScroll;
      const forcedDir=Math.abs(traveled)>=6?(traveled>0?1:-1):(Math.abs(dx)>=8?(dx<0?1:-1):0);
      let v=Math.max(-46,Math.min(46,velocity*26));
      if(Math.abs(v)<.65){settle(forcedDir);return}
      const glide=()=>{
        track.scrollLeft+=v;
        normalizeSeamless();requestDots();
        v*=.925;
        if(Math.abs(v)<.28){motionRaf=0;settle(forcedDir);return}
        motionRaf=requestAnimationFrame(glide);
      };
      motionRaf=requestAnimationFrame(glide);
      if(moved){
        const block=ev=>{ev.preventDefault();ev.stopPropagation();track.removeEventListener('click',block,true)};
        track.addEventListener('click',block,true);
      }
    };

    track.addEventListener('pointerdown',startPointer);
    track.addEventListener('pointermove',movePointer,{passive:false});
    track.addEventListener('pointerup',endPointer);
    track.addEventListener('pointercancel',endPointer);
    track.addEventListener('scroll',()=>{if(performance.now()<suppressScrollUntil)return;if(pointerId===null&&!programmatic&&!motionRaf&&!dragging){normalizeSeamless();requestDots();settleSoon()}},{passive:true});
    track.addEventListener('wheel',()=>{paused=true;clearTimeout(autoTimer);clearTimeout(settleTimer);settleTimer=setTimeout(()=>{paused=false;settle(0)},220)},{passive:true});
    track.addEventListener('keydown',e=>{
      if(e.key==='ArrowLeft'){e.preventDefault();step(-1)}
      if(e.key==='ArrowRight'){e.preventDefault();step(1)}
    });
    track.tabIndex=0;
    track._loopNext=()=>step(1);track._loopPrev=()=>step(-1);track._loopGo=goLogical;
    document.addEventListener('visibilitychange',schedule);
    addEventListener('resize',()=>requestAnimationFrame(()=>{normalizeSeamless();settle(0)}),{passive:true});

    requestAnimationFrame(()=>requestAnimationFrame(()=>{
      track.scrollLeft=centerLeft(track,items[middleStart]);
      updateDots();schedule();
    }));
  }

  $$('[data-carousel]').forEach(root=>{
    const track=root.querySelector('.coverflow-stage');
    if(!track)return;
    const originals=$$(':scope > [data-carousel-slide]',track);
    root.querySelectorAll('[data-carousel-prev],[data-carousel-next],.carousel-arrow').forEach(x=>x.remove());
    setupLoop(track,originals,root,{autoplay:Number(root.dataset.autoplay||5000)});
  });

  $$('[data-snap-carousel]').forEach(track=>{
    const originals=[...track.children].filter(x=>x.matches('article,a,.card,.process-step'));
    setupLoop(track,originals,track.parentElement||track,{autoplay:Number(track.dataset.autoplay||5000)});
  });

  $$('[data-scroll-next]').forEach(btn=>btn.addEventListener('click',()=>{
    const track=document.querySelector(btn.dataset.scrollNext);
    if(typeof track?._loopNext==='function')track._loopNext();
  }));
})();

/* INFOTECH_PWA_V9_1 — aviso persistente de instalação + prompt nativo quando disponível */
(() => {
  'use strict';

  const page = location.pathname.split('/').pop() || 'index.html';
  if (/^admin-|^painel-admin|^cliente-admin|^clientes-admin|^offline\.html$/i.test(page) || location.pathname.startsWith('/io/')) return;

  let installEvent = null;
  let installLink = null;
  let banner = document.querySelector('[data-pwa-banner]') || null;

  const isStandalone = () =>
    window.matchMedia?.('(display-mode: standalone)').matches ||
    window.navigator.standalone === true;

  const isIos = () => /iphone|ipad|ipod/i.test(navigator.userAgent);

  const installHelp = () => {
    if (isIos()) return 'No iPhone/iPad: toque em Compartilhar e depois em “Adicionar à Tela de Início”.';
    return 'No Chrome: toque no menu ⋮ e escolha “Instalar app” ou “Adicionar à tela inicial”.';
  };

  const removeInstallLink = () => {
    installLink?.remove();
    installLink = null;
  };

  const removeBanner = () => {
    banner?.remove();
    banner = null;
  };

  const updateBanner = () => {
    if (!banner) return;
    const action = banner.querySelector('[data-pwa-action]');
    const help = banner.querySelector('[data-pwa-help]');
    if (action) action.textContent = installEvent ? 'Instalar agora' : 'Como instalar';
    if (help) {
      help.textContent = installEvent
        ? 'Instale a InfoTech.io no celular para abrir como um aplicativo.'
        : 'Instale a InfoTech.io no seu celular ou computador.';
    }
  };

  const bindBanner = () => {
    if (!banner || banner.dataset.pwaBound === '1') return;
    banner.dataset.pwaBound = '1';

    const close = banner.querySelector('.pwa-install-close');
    const action = banner.querySelector('[data-pwa-action]');
    const instructions = banner.querySelector('[data-pwa-instructions]');

    close?.addEventListener('click', removeBanner);

    action?.addEventListener('click', async () => {
      if (installEvent) {
        const event = installEvent;
        installEvent = null;
        await event.prompt();
        const choice = await event.userChoice.catch(() => null);

        if (choice?.outcome === 'accepted') {
          removeBanner();
          removeInstallLink();
          return;
        }
        updateBanner();
      }

      if (instructions) {
        instructions.textContent = installHelp();
        instructions.hidden = false;
      }
    });
  };

  const ensureBanner = () => {
    if (isStandalone()) {
      removeBanner();
      removeInstallLink();
      return;
    }

    if (!banner) {
      banner = document.createElement('aside');
      banner.className = 'pwa-install-banner';
      banner.setAttribute('data-pwa-banner', '');
      banner.setAttribute('aria-label', 'Instalar aplicativo InfoTech.io');
      banner.innerHTML = `
        <img src="assets/brand/logo-192.webp" width="52" height="52" alt="">
        <div class="pwa-install-copy">
          <strong>Baixar aplicativo InfoTech.io</strong>
          <span data-pwa-help>Instale a InfoTech.io no seu celular ou computador.</span>
        </div>
        <button class="btn btn-primary pwa-install-action" type="button" data-pwa-action>Como instalar</button>
        <button class="pwa-install-close" type="button" aria-label="Fechar aviso de instalação">×</button>
        <p class="pwa-install-instructions" data-pwa-instructions hidden></p>
      `;
      document.body.appendChild(banner);
    }

    bindBanner();
    updateBanner();
  };

  const ensureInstallLink = () => {
    if (isStandalone() || installLink) return;
    const host = document.querySelector('.footer-legal-links');
    if (!host) return;

    installLink = document.createElement('a');
    installLink.href = '#instalar-app';
    installLink.textContent = 'Instalar app';
    installLink.setAttribute('data-pwa-install', '');
    installLink.addEventListener('click', event => {
      event.preventDefault();
      ensureBanner();
      banner?.querySelector('[data-pwa-action]')?.click();
    });
    host.append(' · ', installLink);
  };

  window.addEventListener('beforeinstallprompt', event => {
    // Igual ao app da Padoka: seguramos o prompt nativo para abrir somente
    // depois de uma ação explícita do usuário no cartão "Instalar app".
    event.preventDefault();
    installEvent = event;
    ensureBanner();
    ensureInstallLink();
    updateBanner();
    window.dispatchEvent(new CustomEvent('infotech:pwa-install-ready'));
  });

  window.addEventListener('appinstalled', () => {
    installEvent = null;
    removeBanner();
    removeInstallLink();
    window.dispatchEvent(new CustomEvent('infotech:pwa-installed'));
  });

  const bootPwa = async () => {
    ensureBanner();
    ensureInstallLink();

    if (!('serviceWorker' in navigator)) return;
    if (location.protocol !== 'https:' && !['localhost', '127.0.0.1'].includes(location.hostname)) return;

    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/',
        updateViaCache: 'none'
      });

      registration.update().catch(() => {});
      registration.addEventListener('updatefound', () => {
        const worker = registration.installing;
        if (!worker) return;
        worker.addEventListener('statechange', () => {
          if (worker.state === 'installed' && navigator.serviceWorker.controller) {
            window.dispatchEvent(new CustomEvent('infotech:pwa-update-ready', { detail: { registration } }));
          }
        });
      });
    } catch (error) {
      console.warn('PWA InfoTech indisponível:', error);
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootPwa, { once: true });
  } else {
    bootPwa();
  }
})();


/* INFOTECH_APP_INSTANT_NAV_V9_3 — preaquece navegação pública e melhora sensação de app */
(() => {
  'use strict';

  const PUBLIC_PAGES = [
    '/',
    '/index.html',
    '/servicos.html',
    '/solicitacoes.html',
    '/projetos.html',
    '/contato.html',
    '/sobre.html'
  ];

  const isSensitivePath = pathname =>
    /\/(?:admin(?:-|\/)|painel-(?:admin|cliente)|cliente-admin|clientes-admin|login|cadastro|perfil|nova-solicitacao|detalhes-solicitacao|recuperar-senha|email-confirmado)(?:\.html)?(?:$|[/?#])/i.test(pathname);

  const warm = href => {
    try {
      const url = new URL(href, location.href);
      if (url.origin !== location.origin || isSensitivePath(url.pathname)) return;
      fetch(url.href, {
        method: 'GET',
        credentials: 'same-origin',
        cache: 'default',
        priority: 'low'
      }).catch(() => {});
    } catch {}
  };

  const warmCore = () => {
    PUBLIC_PAGES.forEach((href, index) => {
      setTimeout(() => warm(href), 120 + index * 80);
    });
  };

  const warmLink = event => {
    const a = event.target.closest?.('a[href]');
    if (!a || a.target === '_blank' || a.hasAttribute('download')) return;
    warm(a.href);
  };

  document.addEventListener('pointerover', warmLink, { passive: true });
  document.addEventListener('touchstart', warmLink, { passive: true });

  if ('requestIdleCallback' in window) {
    requestIdleCallback(warmCore, { timeout: 1800 });
  } else {
    setTimeout(warmCore, 700);
  }

  if (window.matchMedia?.('(display-mode: standalone)').matches || window.navigator.standalone === true) {
    document.documentElement.classList.add('infotech-standalone-app');
  }
})();


/* INFOTECH_APP_SHELL_V9_4 — experiência móvel inspirada no app da Padoka */
(() => {
  'use strict';

  const root=document.documentElement;
  const page=location.pathname.split('/').pop()||'index.html';
  const excluded=/^(?:admin-|painel-admin|cliente-admin|clientes-admin|solicitacoes-antigas|offline\.html)/i.test(page)||location.pathname.startsWith('/io/');
  if(excluded)return;

  const standalone=window.matchMedia?.('(display-mode: standalone)').matches||window.navigator.standalone===true;
  root.classList.add('infotech-app-shell-enabled');
  root.classList.toggle('infotech-standalone-app',standalone);

  if(standalone&&navigator.storage&&typeof navigator.storage.persist==='function'){
    navigator.storage.persist().catch(()=>{});
  }

  function hasPersistedSessionHint(){
    try{
      const raw=localStorage.getItem('infotech-auth-v8');
      if(!raw)return false;
      const parsed=JSON.parse(raw);
      return Boolean(parsed?.access_token||parsed?.user||parsed?.currentSession?.access_token);
    }catch{
      return false;
    }
  }

  const hasSessionHint=hasPersistedSessionHint();
  if(hasSessionHint){
    root.classList.add('infotech-session-hint');
    if(page==='login.html')root.classList.add('infotech-login-resume');
    const slot=document.querySelector('.account-slot');
    if(slot&&slot.querySelector('.account-login-fallback,.account-login-link')){
      slot.innerHTML='<div class="account-session-boot" role="status" aria-live="polite"><span class="account-session-dot" aria-hidden="true"></span><span>Carregando sua conta…</span></div>';
    }
  }

  const NAV_ITEMS=[
    {key:'home',href:'index.html',icon:'⌂',label:'Início'},
    {key:'services',href:'servicos.html',icon:'◇',label:'Serviços'},
    {key:'request',href:'nova-solicitacao.html',icon:'＋',label:'Solicitar'},
    {key:'projects',href:'projetos.html',icon:'▦',label:'Projetos'},
    {key:'account',href:hasSessionHint?'painel-cliente.html':'login.html',icon:'♙',label:'Conta'}
  ];

  const activeKey=(()=>{
    if(page==='index.html'||!page)return'home';
    if(page==='servicos.html')return'services';
    if(['nova-solicitacao.html','solicitacoes.html','solicitacao-enviada.html','detalhes-solicitacao.html'].includes(page))return'request';
    if(page==='projetos.html')return'projects';
    if(['login.html','cadastro.html','perfil.html','painel-cliente.html','recuperar-senha.html','email-confirmado.html'].includes(page))return'account';
    return'';
  })();

  function buildBottomNav(){
    if(document.querySelector('.infotech-app-bottom'))return;
    const nav=document.createElement('nav');
    nav.className='infotech-app-bottom';
    nav.setAttribute('aria-label','Navegação rápida do aplicativo');
    nav.innerHTML=NAV_ITEMS.map(item=>`
      <a href="${item.href}" data-app-nav="${item.key}" class="${item.key===activeKey?'active':''}" ${item.key===activeKey?'aria-current="page"':''}>
        <b aria-hidden="true">${item.icon}</b><span>${item.label}</span>
      </a>`).join('');
    document.body.appendChild(nav);
  }

  function removeLoginResume(){
    root.classList.remove('infotech-login-resume');
    document.querySelector('.infotech-auth-resume')?.remove();
  }

  function buildLoginResume(){
    if(!hasSessionHint||page!=='login.html'||document.querySelector('.infotech-auth-resume'))return;
    const card=document.createElement('aside');
    card.className='infotech-auth-resume';
    card.setAttribute('role','status');
    card.setAttribute('aria-live','polite');
    card.innerHTML='<span class="infotech-auth-resume-spinner" aria-hidden="true"></span><strong>Abrindo sua conta…</strong><small>Confirmando sua sessão salva com segurança.</small>';
    document.body.appendChild(card);
    window.setTimeout(removeLoginResume,4500);
  }

  function setAccountDestination(user){
    const account=document.querySelector('[data-app-nav="account"]');
    if(account)account.href=user?'painel-cliente.html':'login.html';
    root.classList.remove('infotech-session-hint');
    if(!user)removeLoginResume();
  }

  window.addEventListener('infotech:auth-ready',event=>setAccountDestination(event.detail?.user||null));

  window.addEventListener('pageshow',()=>{
    const client=window.infotechSupabase;
    if(!client?.auth?.getSession)return;
    client.auth.getSession().then(({data})=>setAccountDestination(data?.session?.user||null)).catch(()=>{});
  });

  const bootAppShell=()=>{buildBottomNav();buildLoginResume()};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bootAppShell,{once:true});
  else bootAppShell();

  try{
    const query=window.matchMedia('(display-mode: standalone)');
    query.addEventListener?.('change',event=>{
      root.classList.toggle('infotech-standalone-app',event.matches);
    });
  }catch{}
})();
