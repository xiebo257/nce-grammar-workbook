---
name: nce-correction
description: Review and correct NCE Grammar Practice 1 answer exports in this repository, write lesson-specific answer and correction reports, or repair incomplete nce1 lesson HTML against the source workbook. Use for pasted NCE lesson exports, requests to correct or continue an NCE lesson, and requests to fix a lesson section.
---

# NCE Correction

Work only within the repository that contains `nce1/`. This skill covers NCE Grammar Practice 1; do not silently apply its file conventions to the Essential Grammar in Use exercises or to NCE 2/3.

## Choose the operation

- For a pasted answer export, review every submitted answer and create the answer and correction artifacts unless the user asks for an in-chat result only.
- For a request to fix a lesson or section, repair the target HTML against the source workbook. Do not create correction artifacts until learner answers are supplied.
- When a learner export follows an HTML repair, include both the pending HTML repair and the new artifacts in verification, but keep their purposes distinct.
- Treat short follow-ups such as "go on" as continuation of the active lesson workflow, not permission for unrelated changes.
- Do not commit or push unless the user currently requests it or clearly continues an already-authorized commit-and-push workflow.

## Resolve the lesson

Read the lesson number and title from the export heading or target filename. Normalize the number to three digits:

- Lesson 7 -> `007`
- Lesson 14 -> `014`
- Lesson 144 -> `144`

Use these paths:

- Lesson page: `nce1/lesson-NNN.html`
- Extracted answer key: `nce1/answer-key/lesson-NNN.md`
- Answer-key index: `nce1/answer-key/README.md`
- Preserved export: `nce1/lesson-NNN-answers.md`
- Correction report: `nce1/lesson-NNN-correction.md`
- Source workbook: `nce1/新概念英语语法练习1_按课程索引.pdf`

Never overwrite an existing answer or correction artifact without first reading it and determining whether the new submission supersedes it.

## Establish the source of truth

1. Read the lesson-specific extracted answer key before grading. Compare every submitted item with the corresponding key entry; do not reconstruct expected answers from grammar intuition when a keyed answer exists.
2. Read the target lesson HTML and compare its prompts, examples, section headings, and answer-unit order with both the learner export and answer key. Worked examples are often omitted from the key, so use the HTML to map exported item numbers to key sections accurately.
3. The extracted keys were produced by OCR. If a key line is missing, malformed, or inconsistent with the prompt, use the answer-key index to locate and visually inspect the cited scanned PDF page. The rendered scan is authoritative over OCR, HTML, historical Git transcriptions, and inferred grammar rules.
4. Use the lesson's exercise pages from the source workbook when the HTML prompt itself is missing, compressed, ambiguous, or specifically challenged by the user. The PDF is image-only, so render the relevant pages and inspect them visually; do not trust empty text extraction.
5. Put temporary renders under `tmp/pdfs/` and remove only the files created for the task after verification.

Do not replace, duplicate, or modify the source PDF.

## Preserve the learner export

Save the export as supplied, including its heading, timestamp, prompts, answer order, capitalization, spelling, and mistakes. The answers file is a record, not the corrected version.

If HTML line breaks were collapsed by the exporter, preserve the raw exported prompt in the answers file. Use readable line breaks in the correction report when explaining paired questions.

## Grade the answers

Review every answer against both the prompt and the exercise instruction. Use these statuses consistently, including the icon in every correction-report status cell:

- `🟢 Right`: correct grammar, meaning, target form, spelling, and required content.
- `🔴 Error`: grammar, meaning, word choice, spelling, or completeness must change to satisfy the exercise.
- `🟡❗ Note`: the target grammar and meaning are correct, but there is a minor punctuation, formatting, optional wording, or omitted-explanation issue.

Do not use the plain words `Right`, `Error`, or `Note` by themselves in the report table. The icon makes the result scannable: green means correct, red means a required correction, and yellow plus an exclamation mark means a non-scoring note.

Scoring rules:

- Report the correct count and total explicitly.
- Errors reduce the strict score.
- Notes do not reduce a grammar score unless the noted feature is itself the exercise target; state the number and type of notes separately.
- Accept contractions used by the workbook, British forms such as `colour` and `grey`, and natural equivalent answers unless the exercise requires an exact transformation.
- Check viewpoint changes such as question `your` -> answer `my`.
- Check singular/plural agreement, possessive apostrophes, sentence-ending punctuation, and whether every part of a paired prompt was answered.

Do not invent errors to make the report look more substantial. If every answer is correct, say so plainly.

## Write the correction report

Use this shape:

```markdown
# Correction: NCE Grammar Practice 1 - Lesson N

**Date:** YYYY-MM-DD
**Source scope:** NCE Grammar Practice 1, Lesson N, "Title"
**Reference:** `nce1/lesson-NNN.html`; answer key: `nce1/answer-key/lesson-NNN.md`; source PDF: `nce1/新概念英语语法练习1_按课程索引.pdf`
**Learner file:** `nce1/lesson-NNN-answers.md`

Status: ...

**Strict score: X/Y ...**

| Item | Status | Learner answer | Correct answer / expected form | Explanation |
|---|---|---|---|---|
| 1 | 🟢 Right | `...` | `...` | ... |
| 2 | 🔴 Error | `...` | `...` | ... |
| 3 | 🟡❗ Note | `...` | `...` | ... |
```

Include one row per submitted item, in original order. Keep explanations specific to that item and concise enough for table readability. Use `<br>` inside table cells for multi-line answers.

After the item table, add:

1. `## Usage table` with the patterns actually exercised, examples, and practical reminders.
2. `## Key takeaway` with a short review list focused on demonstrated rules.
3. A one-line summary stating the result and the main correction focus.

Do not add unrelated grammar topics. Five to ten usage rows are usually enough; let lesson content determine the actual count.

## Repair lesson HTML

When the user requests a lesson or section fix:

- Restore complete prompts and worked examples from the source workbook instead of leaving slash-separated summaries.
- Preserve semantic headings, ordered-list numbering, labels, accessibility attributes, navigation, and the existing two-space document style.
- Use `<ol start="N">` when numbering resumes after a worked example.
- Let the ordered list render its marker; do not duplicate a visible number inside the list item.
- Use `<br>` between paired prompt lines.
- Keep one answer field per source response unit. Use `rows="3"` when a learner must enter two response lines.
- Preserve the count and order of existing learner-editable fields whenever the source permits, because localStorage maps answers by field index.
- Do not refactor unrelated content or shared assets.

If restoring the source necessarily changes answer-field indexing, call out the persistence impact before completion.

## Verify

Run checks proportional to the change:

- `git diff --check`
- Count exported question headings and correction table rows; each must equal the submitted item count.
- Confirm the report's expected forms and score against the lesson-specific extracted answer key, visually checking any uncertain OCR against its cited PDF page.
- Check the target page's inline JavaScript syntax when HTML changed.
- Run `node --check nce1/lesson-navigation.js` when lesson behavior is involved.
- Serve the repository root and require HTTP 200 for the changed page.
- Inspect desktop and mobile layouts in the browser when a browser backend is available. If it is unavailable, report that visual inspection was not run.
- Confirm previous/next links and `Lesson N of 144` remain correct.
- Remove task-created temporary renders.
- Review `git status` and leave unrelated files, including `.idea/`, untouched.

Before claiming completion, identify the exact changed files, score, remaining notes or errors, verification performed, and whether the work is only local or was committed/pushed.

## Commit only when authorized

When commit or push is requested, stage only the lesson HTML and lesson-specific answer/correction files produced by the active task. Follow the repository's Conventional Commit style, for example:

```text
docs(nce1): add lesson 14 correction
fix(nce1): restore lesson 14 section two
```

After pushing, confirm that the branch and configured remote point at the new commit. Never include unrelated untracked project files.
