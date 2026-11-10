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
  const downloadControl = document.querySelector('#download-answers') || makeDisabledControl('Download answers', 'lesson-download');
  submitControl.type = 'button';
  submitControl.className = 'lesson-submit';
  submitControl.id = 'submit-answers';
  submitControl.textContent = 'Submit';
  submitControl.setAttribute('aria-label', 'Copy lesson answers to the clipboard');
  downloadControl.type = 'button';
  downloadControl.className = 'lesson-download';
  downloadControl?.setAttribute('aria-label', 'Download lesson answers');

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
    downloadControl,
    progress || Object.assign(document.createElement('span'), { textContent: '' }),
    nextControl
  );
  const progressControl = navigation.children[3];
  progressControl.classList.add('lesson-progress');

  const storageKey = 'nce-grammar:' + location.pathname;

  const buildAnswersMarkdown = () => {
    const fields = [...document.querySelectorAll('textarea')];
    const completedAnswers = fields
      .map((field, index) => ({ field, index, answer: field.value.trim() }))
      .filter(({ answer }) => answer);
    const lessonTitle = document.querySelector('h1')?.textContent.trim() || document.title;
    const sections = [
      '# NCE Grammar Practice 1 - ' + lessonTitle,
      '',
      'Exported: ' + new Date().toLocaleString(),
      '',
      '## Answers',
      ''
    ];
    if (completedAnswers.length === 0) {
      sections.push('No answers have been entered yet.');
    }
    for (const { field, index, answer } of completedAnswers) {
      const prompt = field.closest('li')?.querySelector('.question-text')?.textContent.trim();
      const heading = prompt ? 'Question ' + (index + 1) : 'Notes and longer answers';
      sections.push('### ' + heading, '');
      if (prompt) sections.push('**Prompt:** ' + prompt, '');
      sections.push('**Your answer:**', '', answer, '');
    }
    return sections.join('\n');
  };

  const downloadAnswers = () => {
    const blob = new Blob([buildAnswersMarkdown()], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const lessonFile = location.pathname.split('/').pop() || 'lesson';
    link.href = url;
    link.download = 'nce1-' + lessonFile.replace(/\.html$/i, '-answers.md');
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  };

  downloadControl?.addEventListener('click', (event) => {
    event.preventDefault();
    event.stopImmediatePropagation();
    downloadAnswers();
  }, true);

  const copyTextToClipboard = async (text) => {
    if (navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(text);
        return;
      } catch (error) {
        // Fall through to the selection-based fallback when permission is denied.
      }
    }

    const helper = document.createElement('textarea');
    helper.value = text;
    helper.setAttribute('readonly', '');
    helper.style.position = 'fixed';
    helper.style.opacity = '0';
    document.body.appendChild(helper);
    helper.select();
    const copied = document.execCommand('copy');
    helper.remove();
    if (!copied) throw new Error('Clipboard copy was not available');
  };

  const showSubmitState = (label, ariaLabel) => {
    submitControl.textContent = label;
    submitControl.setAttribute('aria-label', ariaLabel);
    window.setTimeout(() => {
      submitControl.textContent = 'Submit';
      submitControl.setAttribute('aria-label', 'Copy lesson answers to the clipboard');
    }, 1800);
  };

  submitControl.addEventListener('click', async () => {
    const fields = [...document.querySelectorAll('textarea')];
    localStorage.setItem(storageKey, JSON.stringify(fields.map((field) => field.value)));
    try {
      await copyTextToClipboard(buildAnswersMarkdown());
      showSubmitState('Copied', 'Lesson answers copied to the clipboard');
    } catch (error) {
      showSubmitState('Copy failed', 'Copying lesson answers failed');
    }
  });
}());
