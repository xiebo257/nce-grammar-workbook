(function () {
  'use strict';

  const fields = [...document.querySelectorAll('textarea[data-answer]')];
  const storageKey = 'nce-grammar:' + location.pathname;
  const saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
  fields.forEach((field) => {
    field.value = saved[field.dataset.answer] || '';
    field.addEventListener('input', () => {
      const values = Object.fromEntries(fields.map((item) => [item.dataset.answer, item.value]));
      localStorage.setItem(storageKey, JSON.stringify(values));
    });
  });
}());
