const fields = [...document.querySelectorAll('input, textarea, select')];
const exerciseNumber = document.body.dataset.exercise;
const storageKey = `essential-grammar-additional-exercise-${exerciseNumber}`;
let savedAnswers = [];

try {
  savedAnswers = JSON.parse(localStorage.getItem(storageKey) || '[]');
} catch {
  savedAnswers = [];
}

fields.forEach((field, index) => {
  field.value = savedAnswers[index] || '';
  field.addEventListener('input', () => {
    localStorage.setItem(storageKey, JSON.stringify(fields.map((item) => item.value)));
  });
});

document.querySelector('#export').addEventListener('click', () => {
  const lines = fields.map((field, index) => {
    const answerNumber = field.dataset.answerNumber || index + 1;
    return `${answerNumber}. ${field.value}`;
  });
  const url = URL.createObjectURL(new Blob([lines.join('\n')], { type: 'text/plain' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = `additional-exercise-${exerciseNumber}-answers.txt`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
});
