#!/usr/bin/env python3
"""Generate the first 48 lesson pages from the supplied lesson photographs.

The OCR is used to make the photographed text searchable, while the original
photographs remain linked below every section for checking diagrams and blanks.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OCR = Path("/tmp/nce-ocr.json")
PHOTO_MAP = Path("/tmp/nce-map.json")


def source_lines(value: str) -> list[str]:
    """Keep readable English OCR lines and discard camera/bleed-through noise."""
    # The source pages contain Chinese glosses and show-through from the
    # reverse side. This compact vocabulary set lets us keep real English
    # prompts while dropping isolated reverse-page gibberish.
    common = set('''a an and answer are any ask at behind be book but can case chair clean coffee come complete do door
    dont exercise find first for from give grammar have he her here how i if in is it its lesson like listen make me
    more my new no now of on one open or our out over page practice read rewrite room sam she some source that the their
    them there these this those three to two use very vocabulary want water we what where which who with write yes you
    your am was were will going doing work working please thank thanks one two four five six seven eight nine ten eleven
    twelve thirteen fourteen fifteen twenty hundred thousand million tea cups cup kettle teapot behind front words
    dialogue question questions sentences sentence numbers grammar exercise exercises '''.split())
    result: list[str] = []
    seen: set[str] = set()
    for raw in value.replace("\x0c", "\n").splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if not line or line.startswith("==="):
            continue
        ascii_line = re.sub(r"[^A-Za-z0-9.,!?;:'()/%+&\- ]", "", line)
        letters = re.findall(r"[A-Za-z]", ascii_line)
        if len(letters) < 2:
            continue
        # Chinese annotations and reverse-page bleed-through often leave only
        # one or two isolated OCR characters. Keep normal English sentences,
        # labels, numbered prompts, and vocabulary entries.
        if len(ascii_line.strip()) < 3:
            continue
        tokens = re.findall(r"[A-Za-z]+", ascii_line.lower())
        common_hits = len(set(tokens) & common)
        structural = bool(re.match(r"^(lesson\b|new word|new words|notes on|written exercises|dialogue|vocabulary|numbers|a |b |c )", ascii_line, re.I))
        if re.search(r"\d", ascii_line) and len(tokens) <= 1:
            continue
        if len(tokens) == 1 and tokens[0] not in common and not re.match(r"^(sam|penny|bob|george|ann|christine|dan|susan|jane|amy|tim|jack|sally|steven|helen|tony|emma|paul|sophie|anna|louise|mr|mrs|miss)$", tokens[0]):
            continue
        if structural:
            pass
        elif "/" in ascii_line and common_hits >= 1:
            pass
        elif len(tokens) >= 2 and common_hits == 0:
            continue
        if not structural and "/" not in ascii_line and len(tokens) >= 3 and common_hits < 2:
            continue
        key = ascii_line.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(ascii_line)
    return result


def title_for(main: str, number: int) -> str:
    for line in main.splitlines()[:12]:
        match = re.search(r"Lesson\s+\d+\s+(.+)", line, re.I)
        if match:
            title = re.sub(r"[^A-Za-z0-9 .,!?/'-]", "", match.group(1)).strip(" .")
            if title:
                return title
    return f"Photo lesson {number}"


def block(lines: list[str]) -> str:
    if not lines:
        return '<p class="missing">No readable OCR line was available; use the source photograph below.</p>'
    return "\n".join(f"<p>{html.escape(line)}</p>" for line in lines)


def page(number: int, images: list[str], ocr: dict[str, str]) -> str:
    main, practice, grammar = (ocr.get(name, "") for name in images)
    title = title_for(main, number)

    def image_class(index: int) -> str:
        if (28 <= number <= 40 and index == 3) or (number == 48 and index == 2):
            return "rotate-180"
        if (number == 2 and index == 2) or (number == 6 and index in (1, 2)) or (number == 9 and index in (1, 2)) or (number == 10 and index == 1):
            return "rotate-90"
        return ""

    image_markup = "\n".join(
        f'''          <figure class="source-photo {image_class(index)}">
            <a href="images/{html.escape(name)}" target="_blank" rel="noopener noreferrer">
              <img src="images/{html.escape(name)}" loading="lazy" alt="Lesson {number} source photograph {index}">
            </a>
            <figcaption>Source photograph {index} — open full size</figcaption>
          </figure>'''
        for index, name in enumerate(images, 1)
    )
    previous = f'<a class="lesson-previous" href="lesson-{number - 1:03d}.html" rel="prev">Previous lesson</a>' if number > 1 else '<button class="lesson-previous" disabled>Previous lesson</button>'
    following = f'<a class="lesson-next" href="lesson-{number + 1:03d}.html" rel="next">Next lesson</a>' if number < 144 else '<button class="lesson-next" disabled>Next lesson</button>'
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Lesson {number}: {html.escape(title)} | NCE Grammar Practice 1</title>
  <link rel="stylesheet" href="photo-lessons.css">
  <link rel="stylesheet" href="lesson-navigation.css">
</head>
<body>
  <main class="page">
    <header class="lesson-header">
      <p class="series">NCE Grammar Practice 1 · photographed source edition</p>
      <h1>Lesson {number}: {html.escape(title)}</h1>
      <p class="source-note">Transcribed from the three supplied photographs. Use the source images at the bottom to check illustrations, handwriting, and answer blanks.</p>
    </header>
    <article>
      <section class="lesson-section" aria-labelledby="content-heading">
        <p class="section-number">01</p>
        <h2 id="content-heading">Lesson content</h2>
        <div class="transcript">{block(source_lines(main))}</div>
        <label class="response-label" for="lesson-content-answer">Your lesson notes</label>
        <textarea id="lesson-content-answer" data-answer="content" rows="4" aria-label="Your lesson notes"></textarea>
      </section>
      <section class="lesson-section" aria-labelledby="practice-heading">
        <p class="section-number">02</p>
        <h2 id="practice-heading">Practice</h2>
        <div class="transcript">{block(source_lines(practice))}</div>
        <label class="response-label" for="practice-answer">Write your practice answers</label>
        <textarea id="practice-answer" data-answer="practice" rows="7" aria-label="Write your practice answers"></textarea>
      </section>
      <section class="lesson-section" aria-labelledby="grammar-heading">
        <p class="section-number">03</p>
        <h2 id="grammar-heading">Grammar exercise</h2>
        <div class="transcript">{block(source_lines(grammar))}</div>
        <label class="response-label" for="grammar-answer">Write your grammar exercise answers</label>
        <textarea id="grammar-answer" data-answer="grammar" rows="10" aria-label="Write your grammar exercise answers"></textarea>
      </section>
      <section class="source-gallery" aria-labelledby="source-heading">
        <h2 id="source-heading">Source photographs</h2>
        <p class="source-note">Each image is the original supplied file. Select an image to open its full-size version.</p>
        <div class="photo-grid">
{image_markup}
        </div>
      </section>
    </article>
    <nav class="lesson-navigation" aria-label="Lesson navigation">
      {previous}
      <button type="button" id="submit-answers">Submit</button>
      <button type="button" id="download-answers">Download answers</button>
      <span class="lesson-progress">Lesson {number} of 144</span>
      {following}
    </nav>
  </main>
  <script src="photo-lessons.js"></script>
  <script src="lesson-navigation.js"></script>
</body>
</html>
'''


def main() -> None:
    ocr = json.loads(OCR.read_text())
    mapping = json.loads(PHOTO_MAP.read_text())
    for entry in mapping:
        number = entry["lesson"]
        if number > 48:
            continue
        target = ROOT / f"lesson-{number:03d}.html"
        target.write_text(page(number, entry["images"], ocr), encoding="utf-8")


if __name__ == "__main__":
    main()
