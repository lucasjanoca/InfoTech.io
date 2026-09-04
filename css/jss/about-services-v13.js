(() => {
  'use strict';

  const track = document.querySelector('#about-services');
  const title = document.querySelector('[data-about-service-title]');
  const text = document.querySelector('[data-about-service-text]');
  if (!track || !title || !text) return;

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

  let active = -1;
  let raf = 0;

  const logicalIndex = node => Number(node?.dataset?.loopIndex || 0);

  const update = () => {
    raf = 0;
    const items = [...track.children].filter(node => node.matches('article,a,.card,.process-step'));
    if (!items.length) return;

    const center = track.scrollLeft + track.clientWidth / 2;
    let nearest = items[0];
    let distance = Infinity;
    for (const item of items) {
      const itemCenter = item.offsetLeft + item.offsetWidth / 2;
      const current = Math.abs(itemCenter - center);
      if (current < distance) {
        distance = current;
        nearest = item;
      }
    }

    const index = Math.max(0, Math.min(details.length - 1, logicalIndex(nearest)));
    if (index === active) return;
    active = index;
    const detail = details[index];
    title.textContent = detail.title;
    text.textContent = detail.text;

    const banner = title.closest('.about-service-banner');
    if (banner) {
      banner.classList.remove('is-changing');
      void banner.offsetWidth;
      banner.classList.add('is-changing');
    }
  };

  const schedule = () => {
    if (!raf) raf = requestAnimationFrame(update);
  };

  track.addEventListener('scroll', schedule, { passive: true });
  new MutationObserver(schedule).observe(track, { childList: true });
  addEventListener('resize', schedule, { passive: true });
  requestAnimationFrame(() => requestAnimationFrame(schedule));
})();
