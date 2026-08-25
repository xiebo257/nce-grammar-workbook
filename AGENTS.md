# Repository Guidelines

## Project Structure & Module Organization

This repository is a static collection of interactive English grammar workbooks.

- `nce1/` contains 144 zero-padded lesson pages (`lesson-001.html` through `lesson-144.html`), a preface, and shared navigation CSS/JavaScript.
- `grammar/Essential Grammar in Use/unit/` contains the unit lesson pages. Shared assets live one level above it.
- `grammar/Essential Grammar in Use/additional-exercises/` contains grouped exercises plus shared `exercise.css` and `exercise.js`.
- `grammar/Essential Grammar in Use/exercise-daily/YYYY-MM-DD/` stores dated questions, answers, and corrections.
- `grammar/Essential Grammar in Use/error/` contains generated review and error summaries.
- PDF files are source/reference material. Avoid replacing or duplicating these large binaries unless the change requires it.

## Build, Test, and Development Commands

There is no package installation or application build step. Serve the repository root so browser storage and linked assets behave consistently:

```sh
python3 -m http.server 8000
```

Then open `http://localhost:8000/nce1/lesson-001.html` or the page being changed. Check shared JavaScript syntax with:

```sh
node --check nce1/lesson-navigation.js
node --check "grammar/Essential Grammar in Use/additional-exercises/exercise.js"
```

`build-study-guide-html.mjs` regenerates the study-guide HTML from a sibling Markdown source; confirm that source is available before running it.

## Coding Style & Naming Conventions

Use two-space indentation in HTML, CSS, and JavaScript. Preserve the surrounding file's quote style, terminate JavaScript statements with semicolons, and prefer `const`/`let` over `var` in shared scripts. Keep markup semantic and accessible: retain labels, `aria-*` attributes, keyboard focus styles, and valid previous/next relationships. Name lesson files with three digits and daily work with ISO dates. Put reusable behavior in shared assets instead of copying it into every lesson; avoid unrelated bulk reformatting of content-heavy HTML.

## Testing Guidelines

No automated test framework or coverage threshold is configured. Manually test changed pages at desktop and mobile widths. Verify previous/next links, displayed lesson counts, answer persistence after reload, submit/copy behavior, downloads, and a clean browser console. When adding lessons, confirm neighboring links and preserve the expected 144 `nce1` lesson files.

## Commit & Pull Request Guidelines

History follows Conventional Commits, for example `fix(nce1): restore lesson 9 exercises` and `feat(essential-grammar): add study guide unit 15`. Use `feat`, `fix`, `refactor`, or `chore` with a focused scope such as `nce1`, `essential-grammar`, or `english-learn`.

Pull requests should identify affected lessons or exercise sets, cite the reference pages used, summarize manual browser checks, and include before/after screenshots for visual changes. Keep generated outputs and their source changes together when regeneration is possible.
