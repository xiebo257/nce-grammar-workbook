(function () {
  'use strict';

  const navigation = document.querySelector('nav.lesson-navigation');
  if (!navigation) return;

  const currentFile = location.pathname.split('/').pop();
  const isAdditionalExercise = Boolean(document.body.dataset.exercise);
  const currentLesson = Number(currentFile.match(/^lesson-(\d+)\.html$/)?.[1]);
  const submitControl = navigation.querySelector('.lesson-submit');
  if (!submitControl || (!isAdditionalExercise && !currentLesson)) return;

  if (!isAdditionalExercise && currentLesson === 7) {
    const previous = navigation.querySelector('.lesson-previous');
    if (previous?.disabled) {
      const link = document.createElement('a');
      link.href = 'lesson-006.html';
      link.className = 'lesson-previous';
      link.target = '_blank';
      link.rel = 'prev noopener noreferrer';
      link.textContent = 'Previous';
      previous.replaceWith(link);
    }
  }

  navigation.querySelectorAll('a.lesson-previous, a.lesson-next').forEach((link) => {
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
  });

  const storageKey = isAdditionalExercise
    ? `essential-grammar-additional-exercise-${document.body.dataset.exercise}`
    : `essential-grammar-lesson-${String(currentLesson).padStart(3, '0')}`;
  submitControl.addEventListener('click', () => {
    const fields = [...document.querySelectorAll('input, textarea, select')];
    localStorage.setItem(storageKey, JSON.stringify(fields.map((field) => field.value)));
    document.querySelector('#export-answers, #export')?.click();
  });
}());
