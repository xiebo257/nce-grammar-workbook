import { readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const directory = new URL('.', import.meta.url);
const groups = [
  { range: '1-2', title: 'am/is/are', members: [1, 2] },
  { range: '3', title: 'present continuous', members: [3] },
  { range: '4', title: 'present simple', members: [4] },
  { range: '5-7', title: 'present simple, am/is/are and have (got)', members: [5, 6, 7] },
  { range: '8-9', title: 'present continuous and present simple', members: [8, 9] },
  { range: '10-13', title: 'was/were and past simple', members: [10, 11, 12, 13] },
  { range: '14', title: 'past simple and past continuous', members: [14] },
  { range: '15', title: 'present and past', members: [15] },
  { range: '16-18', title: 'present perfect', members: [16, 17, 18] },
  { range: '19-22', title: 'present perfect and past simple', members: [19, 20, 21, 22] },
  { range: '23', title: 'present, past and present perfect', members: [23] },
  { range: '24-27', title: 'passive', members: [24, 25, 26, 27] },
  { range: '28', title: 'future', members: [28] },
  { range: '29', title: 'past, present and future', members: [29] },
  { range: '30-31', title: 'past, present and future', members: [30, 31] },
  { range: '32', title: '-ing and to ...', members: [32] },
  { range: '33-34', title: 'a and the', members: [33, 34] },
  { range: '35', title: 'prepositions', members: [35] },
];

const slugify = (value) => value
  .replaceAll('&', 'and')
  .replace(/\.\.\./g, '')
  .replace(/[^a-zA-Z0-9]+/g, '-')
  .replace(/^-|-$/g, '')
  .toLowerCase();

const readExercise = async (number) => {
  const name = `lesson-${String(number).padStart(3, '0')}.html`;
  const html = await readFile(new URL(name, directory), 'utf8');
  const body = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i)?.[1];
  if (!body) throw new Error(`Missing body in ${name}`);
  const section = body.match(/<section[\s\S]*?(?=<button id="export")/i)?.[0];
  if (!section) throw new Error(`Missing exercise section in ${name}`);
  let fallbackNumber = 0;
  return section.trim().replace(/<(input|textarea|select)([^>]*)>/g, (tag, element, attributes) => {
    if (attributes.includes('data-answer-number=')) return tag;
    fallbackNumber += 1;
    return `<${element}${attributes} aria-label="Answer ${number}-${fallbackNumber}" data-answer-number="${number}-${fallbackNumber}">`;
  });
};

const styleHref = 'exercise.css';
const scriptSrc = 'exercise.js';
for (const group of groups) {
  const blocks = await Promise.all(group.members.map(async (number) => {
    const section = await readExercise(number);
    return `    <article class="exercise-block" aria-labelledby="exercise-${number}">\n      <h2 id="exercise-${number}">Exercise ${number}</h2>\n      ${section}\n    </article>`;
  }));
  const filename = `${group.range}-${slugify(group.title)}.html`;
  const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Essential Grammar in Use - Additional Exercises ${group.range}</title>
  <link rel="stylesheet" href="${styleHref}">
</head>
<body data-exercise="${group.range}">
  <h1>Additional Exercises ${group.range}: ${group.title}</h1>
  <p>Essential Grammar in Use. Your answers are saved in this browser.</p>
${blocks.join('\n')}
  <button id="export" type="button">Export answers</button>
  <script src="${scriptSrc}"></script>
</body>
</html>
`;
  await writeFile(new URL(filename, directory), html);
  console.log(`Wrote ${filename}`);
}
