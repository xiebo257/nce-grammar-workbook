(function () {
  'use strict';

  const navigation = document.querySelector('nav[aria-label="Lesson navigation"]');
  if (!navigation) return;

  const previousLink = navigation.querySelector('a[rel~="prev"]');
  const nextLink = navigation.querySelector('a[rel~="next"]');
  const progress = [...navigation.querySelectorAll('span')].find((item) => item.textContent.trim());

  const makeDisabledControl = (label, className) => {
    const control = document.createElement('button');
    control.type = 'button';
    control.className = className;
    control.disabled = true;
    control.setAttribute('aria-disabled', 'true');
    control.textContent = label;
    return control;
  };

  const previousControl = previousLink || makeDisabledControl('Previous lesson', 'lesson-previous');
  const nextControl = nextLink || makeDisabledControl('Next lesson', 'lesson-next');
  const submitControl = navigation.querySelector('#submit-answers') || document.createElement('button');
  submitControl.type = 'button';
  submitControl.className = 'lesson-submit';
  submitControl.id = 'submit-answers';
  submitControl.textContent = 'Submit';
  submitControl.setAttribute('aria-label', 'Export lesson answers');

  const addRelValues = (link, ...values) => {
    link.rel = [...new Set(link.rel.split(/\s+/).filter(Boolean).concat(values))].join(' ');
  };

  if (previousLink) {
    previousLink.classList.add('lesson-previous');
    previousLink.target = '_blank';
    addRelValues(previousLink, 'noopener', 'noreferrer');
  }
  if (nextLink) {
    nextLink.classList.add('lesson-next');
    nextLink.target = '_blank';
    addRelValues(nextLink, 'noopener', 'noreferrer');
  }

  navigation.classList.add('lesson-navigation');
  navigation.replaceChildren(
    previousControl,
    submitControl,
    progress || Object.assign(document.createElement('span'), { textContent: '' }),
    nextControl
  );
  const progressControl = navigation.children[2];
  progressControl.classList.add('lesson-progress');

  const storageKey = 'nce-grammar:' + location.pathname;
  submitControl.addEventListener('click', () => {
    const fields = [...document.querySelectorAll('textarea')];
    localStorage.setItem(storageKey, JSON.stringify(fields.map((field) => field.value)));
    document.querySelector('#export-answers')?.click();
  });
}());
