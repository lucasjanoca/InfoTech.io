(() => {
  'use strict';

  const track = document.querySelector('#about-services');
  const title = document.querySelector('[data-about-service-title]');
  const text = document.querySelector('[data-about-service-text]');
  const nextButton = document.querySelector('[data-about-next]');
  const dotsRoot = document.querySelector('[data-about-dots]');
  if (!track || !title || !text) return;

  const slides = [...track.querySelectorAll('[data-about-slide]')];
  if (!slides.length) return;

  const details = [
    {
      title: 'Sites',
      text: 'Presença digital profissional para apresentar sua empresa, gerar confiança e facilitar o contato.'
    },
    {
      title: 'Sistemas',
      text: 'Ferramentas sob medida para organizar processos, informações e rotinas da sua empresa.'
    },
    {
      title: 'Tecnologia',
      text: 'Soluções práticas que conectam sua necessidade ao caminho digital mais simples e eficiente.'
    }
  ];

  let active = 0;
  let timer = 0;
  let pointerStart = null;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

  const dots = [];
  if (dotsRoot) {
    dotsRoot.replaceChildren();
    slides.forEach((_, index) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.setAttribute('aria-label', `Ver ${details[index]?.title || `item ${index + 1}`}`);
      button.addEventListener('click', () => show(index, true));
      dotsRoot.appendChild(button);
      dots.push(button);
    });
  }

  const animateBanner = () => {
    const banner = title.closest('.about-service-banner');
    if (!banner || reduced) return;
    banner.classList.remove('is-changing');
    void banner.offsetWidth;
    banner.classList.add('is-changing');
  };

  const render = () => {
    slides.forEach((slide, index) => {
      const on = index === active;
      slide.classList.toggle('is-active', on);
      slide.setAttribute('aria-hidden', String(!on));
      slide.tabIndex = on ? 0 : -1;
    });
    dots.forEach((dot, index) => {
      const on = index === active;
      dot.classList.toggle('active', on);
      dot.setAttribute('aria-current', on ? 'true' : 'false');
    });

    const detail = details[active] || details[0];
    title.textContent = detail.title;
    text.textContent = detail.text;
    animateBanner();
  };

  const schedule = () => {
    clearTimeout(timer);
    if (reduced || document.hidden) return;
    timer = setTimeout(() => show(active + 1, false), 4200);
  };

  function show(index, userInitiated = false) {
    active = (index + slides.length) % slides.length;
    render();
    if (userInitiated || !document.hidden) schedule();
  }

  nextButton?.addEventListener('click', () => show(active + 1, true));

  track.addEventListener('pointerdown', event => {
    pointerStart = { x: event.clientX, y: event.clientY };
    clearTimeout(timer);
  });
  track.addEventListener('pointerup', event => {
    if (!pointerStart) return schedule();
    const dx = event.clientX - pointerStart.x;
    const dy = event.clientY - pointerStart.y;
    pointerStart = null;
    if (Math.abs(dx) > 38 && Math.abs(dx) > Math.abs(dy) * 1.15) {
      show(active + (dx < 0 ? 1 : -1), true);
    } else {
      schedule();
    }
  });
  track.addEventListener('pointercancel', () => {
    pointerStart = null;
    schedule();
  });

  track.addEventListener('keydown', event => {
    if (event.key === 'ArrowRight') {
      event.preventDefault();
      show(active + 1, true);
    }
    if (event.key === 'ArrowLeft') {
      event.preventDefault();
      show(active - 1, true);
    }
  });

  track.addEventListener('mouseenter', () => clearTimeout(timer));
  track.addEventListener('mouseleave', schedule);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) clearTimeout(timer);
    else schedule();
  });

  show(0, false);
})();
