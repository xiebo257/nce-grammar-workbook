const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const migration = fs.readFileSync(path.join(root, 'lesson-workbook.js'), 'utf8');
const fieldCounts = [22, 27, 25, 41, 23, 35, 30, 24, 28, 34, 20, 32, 18, 17, 21, 25, 17, 39, 19, 28, 22, 28, 18, 29, 14, 28, 16, 28, 16, 42, 26, 29, 20, 23, 18];

function migrationContext(savedAnswers, fieldCount) {
  const key = 'nce-grammar:/nce1/lesson-111.html';
  const storage = new Map();
  if (savedAnswers !== undefined) storage.set(key, JSON.stringify(savedAnswers));
  const context = {
    location: { pathname: '/nce1/lesson-111.html' },
    document: { querySelectorAll: () => Array(fieldCount).fill({}) },
    localStorage: {
      getItem: name => storage.get(name) ?? null,
      setItem: (name, value) => storage.set(name, String(value)),
    },
  };
  return { key, storage, context };
}

test('legacy notes move to the final notes field exactly once', () => {
  const { key, storage, context } = migrationContext(['Previous notes'], 28);
  vm.runInNewContext(migration, context);
  const answers = JSON.parse(storage.get(key));
  assert.equal(answers.length, 28);
  assert.equal(answers[0], '');
  assert.equal(answers[27], 'Previous notes');
  answers[0] = 'New answer';
  storage.set(key, JSON.stringify(answers));
  vm.runInNewContext(migration, context);
  assert.deepEqual(JSON.parse(storage.get(key)), answers);
});

test('existing multi-field answers and empty storage are not rewritten', () => {
  for (const initial of [undefined, [], ['Answer one', 'Answer two', 'Notes']]) {
    const { key, storage, context } = migrationContext(initial, 28);
    const original = storage.get(key);
    vm.runInNewContext(migration, context);
    assert.equal(storage.get(key), original);
    assert.equal(storage.get(key + ':workbook-layout-v1'), 'true');
  }
});

test('all 35 restored lessons retain expected answer counts and navigation', () => {
  for (let lesson = 110; lesson <= 144; lesson++) {
    const file = `lesson-${String(lesson).padStart(3, '0')}.html`;
    const html = fs.readFileSync(path.join(root, file), 'utf8');
    assert.equal((html.match(/class="answer-field"/g) || []).length, fieldCounts[lesson - 110], file);
    assert(html.includes(`Lesson ${lesson} of 144`), file);
    assert(html.includes(`href="lesson-${lesson - 1}.html"`), file);
    if (lesson < 144) assert(html.includes(`href="lesson-${lesson + 1}.html"`), file);
    assert(html.includes('href="lesson-workbook.css"'), file);
    if (lesson > 110) assert(html.includes('src="lesson-workbook.js"'), file);
    assert.equal((html.match(/aria-label="Your notes and answers"/g) || []).length, 1, file);
    for (const [, script] of html.matchAll(/<script>([\s\S]*?)<\/script>/g)) {
      assert.doesNotThrow(() => new vm.Script(script), file);
    }
  }
  const lessonFiles = fs.readdirSync(root).filter(file => /^lesson-\d{3}\.html$/.test(file));
  assert.equal(lessonFiles.length, 144);
});

test('Lesson 110 dollar amounts match the source workbook', () => {
  const html = fs.readFileSync(path.join(root, 'lesson-110.html'), 'utf8');
  assert(html.includes('Jane has sixty dollars; Mary has one hundred and fifty dollars; Ann has one hundred dollars.'));
  assert(!html.includes('Jane has sixty dollars; Mary has one hundred dollars; Ann has one hundred and fifty dollars.'));
});

test('incorrect placeholder titles are replaced with source lesson titles', () => {
  const expected = {
    122: 'Who (whom), which and that',
    124: '(who)/(whom), (which) and (that)',
    144: 'He hasn&#x27;t been served yet. He will be served soon.',
  };
  for (const [lesson, title] of Object.entries(expected)) {
    const html = fs.readFileSync(path.join(root, `lesson-${lesson}.html`), 'utf8');
    assert(html.includes(`<h1>Lesson ${lesson}: ${title}</h1>`));
  }
});
