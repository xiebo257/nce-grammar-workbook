(function () {
  'use strict';

  const storageKey = 'nce-grammar:' + location.pathname;
  const layoutKey = storageKey + ':workbook-layout-v1';
  if (localStorage.getItem(layoutKey)) return;

  const fields = [...document.querySelectorAll('textarea')];
  const savedAnswers = JSON.parse(localStorage.getItem(storageKey) || '[]');

  // The previous placeholder pages stored only the final notes field.
  if (savedAnswers.length === 1 && fields.length > 1) {
    const restoredAnswers = Array(fields.length).fill('');
    restoredAnswers[fields.length - 1] = savedAnswers[0];
    localStorage.setItem(storageKey, JSON.stringify(restoredAnswers));
  }

  localStorage.setItem(layoutKey, 'true');
})();
