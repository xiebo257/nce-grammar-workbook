import { readFile, writeFile } from "node:fs/promises";

const inputPath = new URL("./Essential_Grammar_in_Use_4th_Ed_Study_Guide.md", import.meta.url);
const outputPath = new URL("./Essential_Grammar_in_Use_4th_Ed_Study_Guide.html", import.meta.url);
const markdown = await readFile(inputPath, "utf8");

const escapeHtml = (value) => value
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#39;");

const formatText = (value) => escapeHtml(value)
  .replace(/`([^`]+)`/g, "<code>$1</code>")
  .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

const guide = markdown.split("## Answer Key")[0];
const sections = [];
let currentSection;

for (const line of guide.split(/\r?\n/)) {
  const sectionMatch = line.match(/^## (.+)$/);
  if (sectionMatch) {
    currentSection = { title: sectionMatch[1], questions: [] };
    sections.push(currentSection);
    continue;
  }

  const questionMatch = line.match(/^\- \*\*(\d+\.\d+)\*\* \[Study: ([^\]]+)\]\s*(.*?)\s+\*\*A\*\*\s+(.+)$/);
  if (!questionMatch || !currentSection) continue;

  const [, id, study, rawPrompt, choicesSource] = questionMatch;
  // The source has answer letters accidentally prefixed to several early prompts.
  const prompt = rawPrompt.replace(/^[A-E]\s+(?=\S)/, "");
  const choices = [];
  const choicePattern = /(?:^|;\s*)\*\*([A-E])\*\*\s*([^;]+)/g;
  let choiceMatch;
  while ((choiceMatch = choicePattern.exec(`**A** ${choicesSource}`)) !== null) {
    choices.push({ letter: choiceMatch[1], text: choiceMatch[2].trim() });
  }
  currentSection.questions.push({ id, study, prompt, choices });
}

const questionMarkup = sections
  .filter((section) => section.questions.length)
  .map((section) => `
    <section class="topic" aria-labelledby="topic-${section.questions[0].id}">
      <h2 id="topic-${section.questions[0].id}">${formatText(section.title)}</h2>
      <div class="question-list">
        ${section.questions.map((question) => `
          <fieldset class="question" data-question-id="${question.id}">
            <legend><span class="question-number">${question.id}</span> <span class="prompt">${formatText(question.prompt)}</span></legend>
            <p class="study">Study: ${escapeHtml(question.study)}</p>
            <div class="choices">
              ${question.choices.map((choice) => `
                <label class="choice">
                  <input type="checkbox" name="q-${question.id}" value="${choice.letter}" data-choice-text="${escapeHtml(choice.text)}">
                  <span class="choice-letter">${choice.letter}</span>
                  <span>${formatText(choice.text)}</span>
                </label>`).join("")}
            </div>
          </fieldset>`).join("")}
      </div>
    </section>`).join("");

const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Essential Grammar in Use | Study Guide Drills</title>
  <style>
    :root { color-scheme: light; --ink: #1d2935; --muted: #5c6b78; --paper: #fbfaf6; --surface: #ffffff; --line: #d8dee4; --accent: #087e8b; --accent-dark: #055a64; --gold: #ffc857; }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body { margin: 0; background: #edf2f4; color: var(--ink); font: 16px/1.55 Arial, Helvetica, sans-serif; }
    .page { width: min(1100px, calc(100% - 40px)); margin: 0 auto; padding: 40px 0 72px; }
    .masthead { padding: 0 0 28px; border-bottom: 4px solid var(--gold); }
    .eyebrow { margin: 0 0 8px; color: var(--accent-dark); font-size: .78rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
    h1, h2 { margin: 0; line-height: 1.2; letter-spacing: 0; }
    h1 { max-width: 760px; font-family: Georgia, 'Times New Roman', serif; font-size: clamp(2rem, 4vw, 3.4rem); font-weight: 600; }
    .intro { max-width: 760px; margin: 16px 0 0; color: var(--muted); }
    .notice { margin: 26px 0 30px; padding: 15px 18px; background: #fff5d6; border-left: 4px solid #d59600; color: #5e490d; }
    .topic { margin-top: 44px; }
    h2 { margin-bottom: 16px; color: var(--accent-dark); font-size: 1.4rem; }
    .question-list { display: grid; gap: 14px; }
    .question { min-width: 0; margin: 0; padding: 18px 20px 20px; background: var(--surface); border: 1px solid var(--line); border-radius: 6px; }
    .question:focus-within { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(8, 126, 139, .13); }
    legend { max-width: 100%; padding: 0; font-size: 1rem; font-weight: 600; }
    .question-number { display: inline-block; min-width: 3.1rem; color: var(--accent-dark); font-variant-numeric: tabular-nums; }
    .study { margin: 5px 0 13px 3.1rem; color: var(--muted); font-size: .84rem; }
    .choices { display: grid; grid-template-columns: repeat(auto-fit, minmax(205px, 1fr)); gap: 8px; margin-left: 3.1rem; }
    .choice { display: flex; align-items: flex-start; gap: 8px; min-width: 0; padding: 8px 10px; border: 1px solid transparent; border-radius: 4px; cursor: pointer; }
    .choice:hover { background: #f1f8f8; border-color: #c1e2e5; }
    .choice input { appearance: none; flex: 0 0 auto; width: 17px; height: 17px; margin: 3px 0 0; border: 2px solid #8796a3; border-radius: 50%; background: #fff; cursor: pointer; }
    .choice input:checked { border-color: var(--accent); background: var(--accent); box-shadow: inset 0 0 0 3px #fff; }
    .choice-letter { flex: 0 0 auto; color: var(--accent-dark); font-weight: 700; }
    .submit-bar { position: sticky; bottom: 0; display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-top: 40px; padding: 14px 18px; background: rgba(255,255,255,.96); border: 1px solid var(--line); box-shadow: 0 -4px 18px rgba(29,41,53,.08); }
    .answered-count { color: var(--muted); font-size: .92rem; }
    button { border: 0; border-radius: 4px; padding: 11px 18px; background: var(--accent); color: #fff; font: inherit; font-weight: 700; cursor: pointer; }
    button:hover, button:focus-visible { background: var(--accent-dark); }
    button:focus-visible, input:focus-visible { outline: 3px solid var(--gold); outline-offset: 2px; }
    .results { margin-top: 42px; padding: 26px; background: var(--paper); border: 1px solid #d7d4c9; border-radius: 6px; }
    .results[hidden] { display: none; }
    .results h2 { margin-bottom: 8px; }
    .results p { margin: 0; color: var(--muted); }
    .answer-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(265px, 1fr)); gap: 10px; margin: 20px 0 0; padding: 0; list-style: none; }
    .answer-list li { padding: 12px 14px; background: #fff; border-left: 3px solid var(--accent); }
    .answer-list strong { color: var(--accent-dark); }
    .submitted-question { display: block; margin-bottom: 5px; }
    .submitted-answer { color: var(--muted); }
    @media (max-width: 640px) { .page { width: min(100% - 24px, 1100px); padding-top: 28px; } .question { padding: 16px; } .question-number { min-width: 0; } .study, .choices { margin-left: 0; } .choices { grid-template-columns: 1fr; } .submit-bar { align-items: stretch; flex-direction: column; } button { width: 100%; } .results { padding: 20px; } }
  </style>
</head>
<body>
  <main class="page">
    <header class="masthead">
      <p class="eyebrow">Essential Grammar in Use, Fourth Edition</p>
      <h1>Study Guide Drills</h1>
      <p class="intro">Choose the correct alternative. Some questions have more than one possible answer, so select every answer you would write.</p>
    </header>
    <aside class="notice">The original source does not include drills 14.9-14.10 or section 15, so those questions are not shown here.</aside>
    <form id="study-guide" novalidate>
      ${questionMarkup}
      <div class="submit-bar">
        <span class="answered-count" id="answered-count">0 questions answered</span>
        <button type="submit">Submit answers</button>
      </div>
    </form>
    <section class="results" id="results" hidden aria-live="polite" tabindex="-1">
      <h2>Your submitted answers</h2>
      <p id="results-summary"></p>
      <ol class="answer-list" id="answer-list"></ol>
    </section>
  </main>
  <script>
    const form = document.querySelector('#study-guide');
    const count = document.querySelector('#answered-count');
    const results = document.querySelector('#results');
    const summary = document.querySelector('#results-summary');
    const answerList = document.querySelector('#answer-list');
    const updateCount = () => {
      const answered = [...form.querySelectorAll('.question')].filter((question) => question.querySelector('input:checked')).length;
      count.textContent = answered + ' question' + (answered === 1 ? '' : 's') + ' answered';
    };
    form.addEventListener('change', updateCount);
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      const answeredQuestions = [...form.querySelectorAll('.question')].filter((question) => question.querySelector('input:checked'));
      answerList.replaceChildren();
      if (answeredQuestions.length === 0) {
        summary.textContent = 'No answers were submitted yet.';
      } else {
        summary.textContent = answeredQuestions.length + ' answered question' + (answeredQuestions.length === 1 ? '' : 's') + ' submitted.';
        for (const question of answeredQuestions) {
          const answers = [...question.querySelectorAll('input:checked')];
          const item = document.createElement('li');
          const prompt = document.createElement('span');
          prompt.className = 'submitted-question';
          const number = document.createElement('strong');
          number.textContent = question.dataset.questionId + '. ';
          prompt.append(number, question.querySelector('.prompt').textContent);
          const response = document.createElement('span');
          response.className = 'submitted-answer';
          response.textContent = 'Your answer: ' + answers.map((answer) => answer.value + '. ' + answer.dataset.choiceText).join('; ');
          item.append(prompt, response);
          answerList.append(item);
        }
      }
      results.hidden = false;
      results.focus({ preventScroll: true });
      results.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  </script>
</body>
</html>
`;

await writeFile(outputPath, html.replace(/[\t ]+$/gm, ""));
console.log(`Wrote ${outputPath.pathname} with ${sections.reduce((total, section) => total + section.questions.length, 0)} questions.`);
