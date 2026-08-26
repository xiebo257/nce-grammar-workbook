---
name: english-learn
description: Generate fresh English grammar tests from a supplied PDF and Study Guide exercise HTML, or grade learner answers against a PDF answer key. For random-topic tests, select a Study Guide topic, map every book unit listed under it, sample question patterns from each unit, and rewrite them into new questions. Use when the user explicitly asks for `test` (new fill-in, correction, Chinese-to-English, meaning-contrast, and personal-expression questions) or `correct` (the original workbook answer-checking workflow). Require the relevant PDF and HTML/answer inputs; ask the user to provide missing paths instead of inventing source material.
---

# English Learn

Support two explicit modes. Keep the modes separate so a request to generate practice does not accidentally reveal an answer key.

## Mode Selection and Required Inputs

1. Identify the requested mode from `test` or `correct`. If neither is clear, ask which mode the user wants. In `test` mode, treat `HTML`, `html`, `web form`, or `export answers` as an output-format request in addition to the normal chat test.
2. For `test`, require a searchable (or OCR-readable) grammar/answer-key PDF and one or more exercise HTML/source files. Also identify the book Unit, Study Guide topic, or exercise range when the sources contain more than one target. Keep those namespaces distinct. If the PDF or HTML is missing, say exactly which input is missing and ask for its path or upload; do not fabricate questions from memory.
3. For `correct`, require the learner answer file, the matching PDF answer key, and the exercise HTML/source when available. If any required input is missing, request it before grading.
4. Preserve all user source files. Do not edit exercise HTML, answer files, PDF files, CSS, or JavaScript unless the user explicitly asks for a source change. A newly generated test HTML file is allowed when the user requests HTML output.
5. Interpret `random unit` as one randomly selected PDF book Unit and constrain every generated item to that Unit's grammar. Interpret `random topic` as one randomly selected Study Guide topic from the supplied Study Guide HTML. For a random topic, read that topic's `study` labels, resolve the listed PDF book Units, and include at least one freshly rewritten question pattern from every mapped book Unit. Never substitute a Study Guide topic for a requested book Unit.
6. When generating HTML tests for this workbook, use `/Users/admin/IdeaProjects/nce-grammar-workbook/grammar/Essential Grammar in Use/exercise-daily/<YYYY-MM-DD>/` as the default output directory. Create the date directory when missing. Use the local current date in `YYYY-MM-DD` format in the document title and heading. Name the test `topic-N-<slug>.html`, the raw exported learner answers `answers.txt`, and an explained correction report `correction.md` when correction storage is requested.

## `test`: Generate New Practice

Generate a fresh test whenever the user asks for `test`. By default produce 3 items in each of the five sections below (15 items total). Honor an explicit item count, Unit, topic, difficulty, or language preference. Use new wording and situations; do not simply copy the workbook sentences or reveal the original answer key.

### Source extraction

1. Inventory the supplied HTML with `rg --files`, then read the relevant Study Guide topic section and extract its prompts, blanks, options, `study` labels, target forms, and question IDs. Treat the Study Guide HTML as the topic index and scope map. Determine whether each number identifies a PDF book Unit, a Study Guide topic, or an exercise; do not assume that equal numbers refer to the same source scope.
2. Search the PDF for the matching Unit/exercise and answer-key pages. Prefer the bundled helper for candidate pages:

   ```bash
   python3 /Users/admin/.codex/skills/english-learn/scripts/pdf_key_search.py \
     /path/to/book.pdf UNIT-OR-EXERCISE
   ```

   Read complete candidate pages with `pypdf` (or another structured extractor). Printed page numbers and PDF file indexes can differ. If extraction is garbled or the PDF is scanned, use OCR or a PDF viewer and state any remaining uncertainty.
3. For each book Unit mapped to a selected Study Guide topic, read the matching PDF explanation and corresponding source exercises. Randomly select a supported question pattern from that Unit, then rewrite it with new wording, names, situations, and values. Do not copy the workbook sentence, answer choices, or distinctive wording.
4. Infer the tested grammar only from the supplied material. Use the PDF's explanation and key to validate the target form, but paraphrase examples and create novel contexts. Keep acceptable alternatives in mind when writing prompts.
5. Balance the generated test across the mapped book Units and the five required sections. Do not let one Unit dominate unless the selected topic maps to only one Unit.

### Required five-part output

Print the test in this exact order, with clear section headings:

1. **New fill-in questions**: Give a sentence and a verb/word cue where appropriate. Make the required grammatical form unambiguous from context.
2. **Error-correction questions**: Give one sentence containing one target error. Ask the learner to rewrite it correctly. Do not mark the error or provide the correction.
3. **Chinese-to-English translation**: Give natural Chinese prompts that require the target grammar. Avoid word-for-word clues that reveal the answer.
4. **Meaning-contrast questions**: Present two forms or two short contexts and ask the learner to choose, explain the difference, or complete both. Use genuine contrasts from the source, not artificial distinctions.
5. **Personal-expression questions**: Ask open questions that require the learner to use the target grammar about their own life. Include enough context to elicit the intended construction but do not supply a model answer.

Do not print answers, a key, or detailed explanations in `test` mode unless the user explicitly asks for them. It is acceptable to include a brief instruction such as “请直接回答 1–15 题，我会按 `correct` 模式批改。” Label items continuously or with stable section/item IDs so a later correction pass can align answers. State the exact source namespace and mapping, such as `Study Guide Topic 10: Questions (Book Units 44–49)`, but do not reproduce copyrighted pages at length. Never title a test `Unit N` unless its scope is actually PDF book Unit N.

### Optional HTML test output

When the user requests HTML, create a standalone UTF-8 `.html` file for the generated test in addition to (or instead of) the chat rendering, according to the user's preference. The file must:

- contain the same five sections and item IDs as the test output, with no answer key;
- use an unambiguous document title and heading that identify `Book Unit`, `Study Guide Topic`, or `Exercise` correctly;
- use the dated directory and filenames `topic-N-<slug>.html`, `answers.txt`, and `correction.md` when storing the complete daily exercise set;
- include the generation date in the title and heading, for example `Study Guide Topic 10: Questions - 2026-08-23`;
- show any cross-source mapping near the heading, for example `Source scope: Book Units 44–49`;
- use a semantic `<form>` with a labeled input, textarea, or choice group for every item;
- include separate visible `Submit`, `Export Answers`, and reset buttons;
- make `Submit` copy every question and its current response to the clipboard without downloading a file. Use `navigator.clipboard.writeText` when available and a temporary textarea plus `document.execCommand('copy')` as a local-file fallback;
- make `Export Answers` download the same complete question-and-answer text as a UTF-8 plain-text file named `answers.txt`;
- serialize fields in item order with a stable, correction-friendly format such as `10.1 Question: ...` followed by `10.1 Answer: ...`, preserving multi-line responses and using `[blank]` for unanswered items;
- show a distinct success/status message after copy or export and keep the learner's entries on the page;
- avoid external dependencies, network calls, answer-key data, or hidden correct answers.

If the user asks for an exported answer file to be graded, accept the generated question-and-answer text format (including `Question:` and `Answer:` lines) as learner input and follow the normal `correct` workflow.

When the user asks to store or push answers with explanations, preserve the raw learner export as `answers.txt` and write the correction table, explanations, key takeaway, and final one-line summary to `correction.md` in the same dated directory.

### Test quality checks

- Every item must test a form or distinction actually supported by the supplied PDF/HTML.
- Avoid duplicate sentences and avoid copying distinctive workbook wording.
- Ensure each blank has one intended target answer or clearly state that multiple answers are accepted.
- Make personal-expression prompts answerable without specialized knowledge.
- Keep the difficulty appropriate to the source Unit; do not introduce unrelated advanced grammar.

## `correct`: Grade Learner Answers

Use this mode for the original workbook correction workflow.

1. Identify the supplied answer file and PDF. Locate the matching exercise HTML or source text when available so each answer can be aligned with its prompt. Treat the answer file as learner input; preserve it.
2. Search the PDF for the answer-key section and requested exercise number. Use `scripts/pdf_key_search.py` for candidate page discovery, then extract complete relevant page(s) with `pypdf` or another available structured PDF extractor. Do not rely on a guessed PDF page offset: printed page labels and file indexes can differ.
3. Parse the answer key into numbered items, including sub-items such as `8a`, `8b`, and alternatives separated by `/` or `or`. Parse the learner file in the same numbering scheme. Use the exercise HTML to resolve blanks, option letters, surrounding text, and intended tense or construction.
4. Compare answers case-insensitively and ignore harmless formatting differences (capitalization, surrounding whitespace, and contracted versus full forms when equivalent). Accept every alternative explicitly listed in the book key.
5. Distinguish statuses carefully:
   - `✅ Right`: matches the key or an explicitly accepted alternative.
   - `❌ Error`: incorrect grammar, wrong meaning, missing required word/form, or a mismatch that is not defensible in the sentence.
   - `⚠️ Note`: grammatical and plausible in context but not the book's target form, or a context-sensitive alternative not listed by the key. Explain that it is not counted as a strict key match.
6. Print the result in chat only unless the user explicitly asks for a file or HTML change. Define the icons, then print a Markdown table containing exercise/item number, status, learner answer, correct/key answer, and a concise explanation or note. Include every submitted item; do not silently omit correct answers. For long exercises, keep explanations short but specific.
7. Add a `Key takeaway` section after the table. Group errors into a few reusable grammar rules and examples. Finish with exactly one plain-language `One-line summary` as the final line; report the strict score and the main study focus there.

## Comparison Guidance

- The printed key is authoritative for the strict score, but English can permit forms the exercise does not target. Use `⚠️ Note` for a genuinely grammatical alternative instead of calling it ungrammatical. State both facts: why the learner's form can work and why the book expects another form.
- Explain the reason, not just the replacement. Name the rule and show the relevant local pattern, such as `when + present simple`, `modal + base verb`, `enjoy/mind + -ing`, `passive: be + past participle`, or `a/an + singular count noun`.
- For multiple-choice answers, show both the selected option and its word (for example, `B. to talk`). For article exercises, preserve `-` as “no article.”
- Count only `✅ Right` rows as strict matches. Report notes separately so the score is not misleading.
- If the PDF is scanned or extraction is garbled, use an available OCR/PDF viewer or inspect the relevant page image. Say so briefly if uncertainty remains; never invent an answer key.

## Output Rules by Mode

`test` output: five sections in the required order, questions only, no answer key unless requested.

`correct` output: icon legend, correction table with all items, `Key takeaway`, and exactly one final `One-line summary`.
