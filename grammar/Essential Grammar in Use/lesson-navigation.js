(function () {
  'use strict';

  const additionalExercises = [
    '1-2-am-is-are.html',
    '3-present-continuous.html',
    '4-present-simple.html',
    '5-7-present-simple-am-is-are-and-have-got.html',
    '8-9-present-continuous-and-present-simple.html',
    '10-13-was-were-and-past-simple.html',
    '14-past-simple-and-past-continuous.html',
    '15-present-and-past.html',
    '16-18-present-perfect.html',
    '19-22-present-perfect-and-past-simple.html',
    '23-present-past-and-present-perfect.html',
    '24-27-passive.html',
    '28-future.html',
    '29-past-present-and-future.html',
    '30-31-past-present-and-future.html',
    '32-ing-and-to.html',
    '33-34-a-and-the.html',
    '35-prepositions.html'
  ];

  const currentFile = location.pathname.split('/').pop();
  const isAdditionalExercise = Boolean(document.body.dataset.exercise);
  const additionalIndex = additionalExercises.indexOf(currentFile);
  const currentLesson = Number(currentFile.match(/^lesson-(\d+)\.html$/)?.[1]);
  if (!isAdditionalExercise && !currentLesson) return;

  const total = isAdditionalExercise ? additionalExercises.length : 115;
  const currentIndex = isAdditionalExercise ? additionalIndex : currentLesson - 7;
  const previousHref = isAdditionalExercise
    ? additionalExercises[currentIndex - 1]
    : currentLesson > 7 ? `lesson-${String(currentLesson - 1).padStart(3, '0')}.html` : '';
  const nextHref = isAdditionalExercise
    ? additionalExercises[currentIndex + 1]
    : currentLesson < total ? `lesson-${String(currentLesson + 1).padStart(3, '0')}.html` : '';

  const makeLink = (label, href, className) => {
    const control = document.createElement(href ? 'a' : 'button');
    control.className = className;
    control.textContent = label;
    if (href) {
      control.href = href;
      control.target = '_blank';
      control.rel = 'noopener noreferrer';
    } else {
      control.type = 'button';
      control.disabled = true;
      control.setAttribute('aria-disabled', 'true');
    }
    return control;
  };

  const navigation = document.createElement('nav');
  navigation.className = 'lesson-navigation';
  navigation.setAttribute('aria-label', 'Lesson navigation');
  const previousControl = makeLink('Previous', previousHref, 'lesson-previous');
  const nextControl = makeLink('Next', nextHref, 'lesson-next');
  const submitControl = document.createElement('button');
  submitControl.type = 'button';
  submitControl.className = 'lesson-submit';
  submitControl.textContent = 'Submit';
  submitControl.setAttribute('aria-label', 'Export lesson answers');

  const progress = document.createElement('span');
  progress.className = 'lesson-progress';
  progress.textContent = isAdditionalExercise
    ? `Additional exercise ${document.body.dataset.exercise} of ${total}`
    : `Lesson ${currentLesson} of ${total}`;

  navigation.append(previousControl, submitControl, progress, nextControl);
  document.body.append(navigation);

  const storageKey = isAdditionalExercise
    ? `essential-grammar-additional-exercise-${document.body.dataset.exercise}`
    : `essential-grammar-lesson-${String(currentLesson).padStart(3, '0')}`;
  submitControl.addEventListener('click', () => {
    const fields = [...document.querySelectorAll('input, textarea, select')];
    localStorage.setItem(storageKey, JSON.stringify(fields.map((field) => field.value)));
    document.querySelector('#export-answers, #export')?.click();
  });
}());
