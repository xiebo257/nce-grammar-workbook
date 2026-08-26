#!/usr/bin/env python3
"""Find likely answer-key pages for one or more exercise numbers in a searchable PDF."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from pypdf import PdfReader


def parse_exercises(value: str) -> list[str]:
    parts = re.split(r"[,\s]+", value.strip())
    exercises: list[str] = []
    for part in parts:
        if not part:
            continue
        exercises.extend(piece for piece in part.split("-") if piece)
    return exercises


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\x00", " ")).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("exercises", help="Exercise number(s), e.g. 30-31 or 33 34")
    parser.add_argument("--context", type=int, default=700, help="Characters to print per match")
    args = parser.parse_args()

    if not args.pdf.is_file():
        print(f"PDF not found: {args.pdf}", file=sys.stderr)
        return 2

    wanted = parse_exercises(args.exercises)
    if not wanted:
        print("No exercise numbers supplied", file=sys.stderr)
        return 2

    reader = PdfReader(str(args.pdf))
    patterns = {
        exercise: re.compile(rf"(?<!\d){re.escape(exercise)}(?!\d)")
        for exercise in wanted
    }
    found = 0

    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        normalized = compact(text)
        lowered = normalized.lower()
        if "key to" not in lowered and "answer" not in lowered:
            continue
        for exercise, pattern in patterns.items():
            match = pattern.search(normalized)
            if not match:
                continue
            # Answer-key blocks normally place the first item immediately after
            # the exercise number (for example, ``33 2a car``). This excludes
            # prose references such as ``Additional exercises 33-34`` and unit
            # headings such as ``UNIT 33.1``.
            answer_start = re.search(
                rf"(?<![\d.]){re.escape(exercise)}\s+[1-9](?!\d)", normalized
            )
            if not answer_start:
                continue
            match = answer_start
            # Unit pages contain the same numbers. Prefer explicit additional-
            # exercise key pages and answer blocks located later on a page.
            score = 0
            if "additional exercises" in lowered:
                score += 4
            if "key to additional exercises" in lowered:
                score += 2
            if "key to exercises" in lowered:
                score += 1
            if answer_start:
                score += 2
            if match.start() >= len(normalized) * 0.55:
                score += 2
            if score < 3:
                continue
            start = max(0, match.start() - 120)
            end = min(len(normalized), match.start() + args.context)
            print(f"PDF file page {page_index} | exercise {exercise}")
            print(normalized[start:end])
            print()
            found += 1

    if not found:
        print("No candidate answer-key pages found. Extract the PDF text or inspect page images manually.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
