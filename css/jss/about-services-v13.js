(() => {
  'use strict';

  const carousel = document.querySelector('[data-about-carousel]');
  const title = document.querySelector('[data-about-service-title]');
  const text = document.querySelector('[data-about-service-text]');
  const nextButton = document.querySelector('[data-about-next]');
  const dotsRoot = document.querySelector('[data-about-dots]');
  if (!carousel || !title || !text) return;

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
    details.forEach((detail, index) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.setAttribute('aria-label', `Ver ${detail.title}`);
      button.addEventListener('click', () => show(index, true));
      dotsRoot.appendChild(button);
      dots.push(button);
    });
  }

  const animateBanner = () => {
    if (reduced) return;
    carousel.classList.remove('is-changing');
    void carousel.offsetWidth;
    carousel.classList.add('is-changing');
  };

  const render = () => {
    const detail = details[active];
    title.textContent = detail.title;
    text.textContent = detail.text;
    dots.forEach((dot, index) => {
      const on = index === active;
      dot.classList.toggle('active', on);
      dot.setAttribute('aria-current', on ? 'true' : 'false');
    });
    carousel.dataset.aboutActive = detail.title.toLowerCase();
    animateBanner();
  };

  const schedule = () => {
    clearTimeout(timer);
    if (reduced || document.hidden) return;
    timer = setTimeout(() => show(active + 1), 4200);
  };

  function show(index, userInitiated = false) {
    active = (index + details.length) % details.length;
    render();
    if (userInitiated || !document.hidden) schedule();
  }

  nextButton?.addEventListener('click', () => show(active + 1, true));

  carousel.addEventListener('pointerdown', event => {
    pointerStart = { x: event.clientX, y: event.clientY };
    clearTimeout(timer);
  });
  carousel.addEventListener('pointerup', event => {
    if (!pointerStart) return schedule();
    const dx = event.clientX - pointerStart.x;
    const dy = event.clientY - pointerStart.y;
    pointerStart = null;
    if (Math.abs(dx) > 42 && Math.abs(dx) > Math.abs(dy) * 1.15) {
      show(active + (dx < 0 ? 1 : -1), true);
    } else {
      schedule();
    }
  });
  carousel.addEventListener('pointercancel', () => {
    pointerStart = null;
    schedule();
  });

  carousel.tabIndex = 0;
  carousel.addEventListener('keydown', event => {
    if (event.key === 'ArrowRight') {
      event.preventDefault();
      show(active + 1, true);
    } else if (event.key === 'ArrowLeft') {
      event.preventDefault();
      show(active - 1, true);
    }
  });

  carousel.addEventListener('mouseenter', () => clearTimeout(timer));
  carousel.addEventListener('mouseleave', schedule);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) clearTimeout(timer);
    else schedule();
  });

  show(0);
})();
