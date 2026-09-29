(function () {
  'use strict';

  const practice = document.querySelector('#textbook-practice');
  const grammar = document.querySelector('#grammar-practice');
  if (!practice || !grammar) return;

  const storageKey = 'nce-grammar:' + location.pathname;
  const savedAnswers = JSON.parse(localStorage.getItem(storageKey) || '[]');
  const legacyFieldCount = document.querySelectorAll('#grammar-practice textarea, .lesson-notes textarea').length;
  const newFieldCount = document.querySelectorAll('#lesson-content textarea, #textbook-practice textarea').length;
  const versionKey = storageKey + ':content-version';
  if (localStorage.getItem(versionKey) !== '2') {
    const previousCount = Number(practice.dataset.previousCount);
    let migrated;
    if (savedAnswers.length === legacyFieldCount) {
      // Original workbooks stored only grammar answers followed by notes.
      migrated = [...Array(newFieldCount).fill(''), ...savedAnswers];
    } else if (savedAnswers.length === previousCount + legacyFieldCount) {
      // Map the earlier photo-based worksheet layout by prompt, not position.
      const contentFields = [...document.querySelectorAll('#lesson-content textarea, #textbook-practice textarea')];
      migrated = contentFields.map((field) => {
        const index = field.getAttribute('data-previous-index');
        return index === null ? '' : (savedAnswers[Number(index)] || '');
      });
      migrated.push(...savedAnswers.slice(previousCount));
    }
    if (migrated) {
      // Keep the original array as a recovery copy before changing its layout.
      localStorage.setItem(storageKey + ':before-transcription', JSON.stringify(savedAnswers));
      localStorage.setItem(storageKey, JSON.stringify(migrated));
    }
    localStorage.setItem(versionKey, '2');
  }

  const targets = [
    ['lesson-content', 'Content · 课文'],
    ['textbook-practice', 'Practice · 练习'],
    ['grammar-practice', 'Grammar · 语法'],
    ['lesson-notes', 'Notes · 笔记']
  ];
  const notes = document.querySelector('.lesson-notes');
  if (notes) notes.id = 'lesson-notes';

  const menu = document.createElement('details');
  menu.className = 'section-menu';
  const summary = document.createElement('summary');
  summary.textContent = 'Menu · 目录';
  const links = document.createElement('div');
  links.className = 'section-menu-links';
  links.setAttribute('role', 'navigation');
  links.setAttribute('aria-label', 'Lesson sections');
  const sections = [];
  const wideScreen = window.matchMedia('(min-width: 1260px)');
  menu.open = wideScreen.matches;
  wideScreen.addEventListener('change', (event) => { menu.open = event.matches; });
  for (const [id, label] of targets) {
    const section = document.getElementById(id);
    if (!section) continue;
    const link = document.createElement('a');
    link.href = '#' + id;
    link.textContent = label;
    link.addEventListener('click', () => {
      if (!wideScreen.matches) {
        menu.open = false;
        // Move keyboard focus into the destination before hiding the link.
        section.setAttribute('tabindex', '-1');
        section.focus({ preventScroll: true });
      }
    });
    links.append(link);
    sections.push({ section, link });
  }
  menu.append(summary, links);
  document.body.append(menu);

  const updateCurrentSection = () => {
    let current = sections[0];
    for (const item of sections) {
      if (item.section.getBoundingClientRect().top <= 120) current = item;
    }
    for (const item of sections) {
      if (item === current) item.link.setAttribute('aria-current', 'location');
      else item.link.removeAttribute('aria-current');
    }
  };
  let scheduled = false;
  window.addEventListener('scroll', () => {
    if (scheduled) return;
    scheduled = true;
    window.requestAnimationFrame(() => {
      updateCurrentSection();
      scheduled = false;
    });
  }, { passive: true });
  window.addEventListener('resize', updateCurrentSection);
  updateCurrentSection();
}());
