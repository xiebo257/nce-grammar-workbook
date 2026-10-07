#!/usr/bin/env python3
"""
Parse NCE Book I HTML and generate dialogue audio for the first N lessons.

For each lesson:
- If lines have explicit speaker labels (e.g. "THE BOSS: ..."), use them
- If lines look like dialogue (short, question/answer), alternate Male/Female
- If lines are descriptive (long, narrative), use a Narrator voice

Usage:
    python3 gen_nce_lessons.py <input.html> <num_lessons> [-o output_dir]
"""

import asyncio
import edge_tts
import os
import re
import sys
import tempfile
import subprocess
import json
from html.parser import HTMLParser

# Voice pool
MALE_VOICES = ["en-US-AndrewNeural", "en-US-BrianNeural", "en-US-ChristopherNeural"]
FEMALE_VOICES = ["en-US-AvaNeural", "en-US-EmmaNeural", "en-US-JennyNeural"]
NARRATOR_VOICE = "en-US-GuyNeural"

# Female name hints
FEMALE_NAMES = {
    "mary", "jane", "susan", "kate", "ann", "anne", "lucy", "lily", "emma",
    "sarah", "jenny", "jennifer", "lisa", "karen", "michelle", "samantha",
    "victoria", "helen", "sue", "polly", "betty", "nora", "sophie", "naoko",
    "xiaohui", "penny", "amy", "sally", "nicola", "claire", "mum", "mrs",
    "miss", "jane", "mrs. price", "mrs. young", "mrs. smith",
}

MALE_NAMES = {
    "tom", "jack", "john", "james", "bob", "bill", "william", "david",
    "mark", "peter", "paul", "eric", "steven", "michael", "richard",
    "ed", "george", "frank", "joe", "jim", "ken", "roy", "robert",
    "hans", "chang-woo", "luming", "dave", "tim", "sir", "bob", "sam",
    "mr.", "mr. jackson", "mr. richards", "mr. sawyer", "the boss",
}


class NCEParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lessons = []
        self.current_lesson = None
        self.current_lines = []

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return
        if "Book I Lesson" in data:
            if self.current_lesson:
                self.lessons.append((self.current_lesson, self.current_lines))
            # Extract lesson number
            m = re.search(r"Lesson\s+(\d+)", data)
            self.current_lesson = m.group(1) if m else data
            self.current_lines = []
            # Check for text after the title (some lessons have title text)
            after = re.sub(r"Book I Lesson\s+\d+:?\s*", "", data).strip()
            if after:
                self.current_lines.append(after)
        elif self.current_lesson:
            self.current_lines.append(data)

    def close(self):
        super().close()
        if self.current_lesson:
            self.lessons.append((self.current_lesson, self.current_lines))


def is_dialogue_line(line: str) -> bool:
    """Check if a line looks like dialogue (short, has question/exclamation)."""
    return len(line) < 80 and ("?" in line or "!" in line or line.startswith(("Yes", "No", "Thank", "Sorry", "Here", "Come", "Look", "Give", "Shut", "Sit", "Whose", "Is ", "Are ", "Can ", "Do ", "What", "How", "Where", "Which", "There", "This", "My", "It", "She", "He", "We", "I", "The")))


def is_descriptive(line: str) -> bool:
    """Check if a line looks like narrative/description."""
    return len(line) > 60 and not line.endswith("?") and not line.endswith("!")


def assign_speakers(lines: list[str]) -> list[tuple[str, str]]:
    """Assign speakers to lines. Returns [(speaker, gender, line), ...]."""
    # Check for explicit speaker labels like "THE BOSS: ..." or "Bob: ..."
    has_labels = any(re.match(r"^[A-Z][A-Z .]+:\s", line) or re.match(r"^[A-Z][a-z]+:\s", line) for line in lines[:5])

    if has_labels:
        # Parse explicit labels
        result = []
        prev_speaker = None
        prev_gender = "M"
        for line in lines:
            m = re.match(r"(.+?):\s(.+)", line)
            if m:
                speaker = m.group(1).strip()
                text = m.group(2).strip()
                name_lower = speaker.lower().split()[0]
                if name_lower in FEMALE_NAMES or "MRS" in speaker.upper() or "MISS" in speaker.upper():
                    gender = "F"
                elif name_lower in MALE_NAMES or "MR" in speaker.upper() or "BOSS" in speaker.upper():
                    gender = "M"
                else:
                    gender = prev_gender
                prev_speaker = speaker
                prev_gender = gender
                result.append((speaker, gender, text))
            else:
                # Continuation of previous speaker
                if prev_speaker:
                    result.append((prev_speaker, prev_gender, line))
                else:
                    result.append(("Narrator", "M", line))
        return result

    # Check if lesson is mostly descriptive (narrative)
    desc_count = sum(1 for line in lines if is_descriptive(line))
    if desc_count > len(lines) * 0.5:
        # Mostly narrative → single narrator
        return [("Narrator", "M", line) for line in lines]

    # Dialogue: alternate Male/Female speakers
    result = []
    # Try to infer gender from names mentioned
    speakers = [("Speaker A", "M"), ("Speaker B", "F")]
    si = 0  # speaker index
    for line in lines:
        # Detect name in line to possibly switch speaker
        speaker, gender = speakers[si % 2]
        result.append((speaker, gender, line))
        si += 1  # alternate each line

    return result


def get_voice(speaker: str, gender: str, voice_map: dict) -> str:
    """Get or assign a voice for a speaker."""
    if speaker not in voice_map:
        if gender == "F":
            idx = len([v for v in voice_map.values() if v in FEMALE_VOICES])
            voice_map[speaker] = FEMALE_VOICES[idx % len(FEMALE_VOICES)]
        elif speaker == "Narrator":
            voice_map[speaker] = NARRATOR_VOICE
        else:
            idx = len([v for v in voice_map.values() if v in MALE_VOICES])
            voice_map[speaker] = MALE_VOICES[idx % len(MALE_VOICES)]
    return voice_map[speaker]


async def generate_lesson_audio(
    lesson_num: str,
    lines: list[str],
    output_dir: str,
) -> str:
    """Generate audio for one lesson."""
    # Clean up lines
    clean_lines = []
    for line in lines:
        # Fix encoding issues
        line = line.replace("\x97", "—")
        line = line.replace("She'sJapanese", "She's Japanese")
        # Remove lesson title prefixes that got mixed in
        line = re.sub(r"^(A new dress|Tired and thirsty|Mrs\. Smith's \w+|A fine day|Our village|Making a bookcase|Penny's bag|Hurry up!|A cup of coffee|How do you do)\s*", "", line)
        line = line.strip()
        if line:
            clean_lines.append(line)

    # Assign speakers
    dialogue = assign_speakers(clean_lines)

    # Assign voices
    voice_map = {}
    for speaker, gender, _ in dialogue:
        get_voice(speaker, gender, voice_map)

    # Generate audio for each line
    tmp_dir = tempfile.mkdtemp()
    audio_files = []

    for i, (speaker, gender, line) in enumerate(dialogue):
        voice = voice_map[speaker]
        tmp_path = os.path.join(tmp_dir, f"line_{i:03d}.mp3")
        communicate = edge_tts.Communicate(line, voice, rate="+0%")
        await communicate.save(tmp_path)
        audio_files.append(tmp_path)

    # Add silence between lines and concatenate
    silenced_files = []
    for audio_path in audio_files:
        silenced_path = audio_path.replace(".mp3", "_s.mp3")
        subprocess.run(
            ["ffmpeg", "-y", "-i", audio_path, "-af", "apad=pad_dur=0.3",
             "-acodec", "libmp3lame", "-ab", "128k", silenced_path],
            capture_output=True, check=True,
        )
        silenced_files.append(silenced_path)

    # Concat
    concat_file = os.path.join(tmp_dir, "concat.txt")
    with open(concat_file, "w") as f:
        for path in silenced_files:
            f.write(f"file '{path}'\n")

    output_path = os.path.join(output_dir, f"lesson_{lesson_num}.mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
         "-acodec", "libmp3lame", "-ab", "128k", output_path],
        capture_output=True, check=True,
    )

    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)

    size_kb = os.path.getsize(output_path) / 1024
    speakers_str = ", ".join(f"{s}({'M' if 'Male' in str(v) else 'F'})" for s, v in voice_map.items())
    print(f"  Lesson {lesson_num:>3}: {len(dialogue):2d} lines, {size_kb:.0f}KB, voices: {list(voice_map.values())}")

    return output_path


async def main():
    if len(sys.argv) < 3:
        print("Usage: python3 gen_nce_lessons.py <input.html> <num_lessons> [-o output_dir]")
        sys.exit(1)

    html_path = sys.argv[1]
    num_lessons = int(sys.argv[2])
    output_dir = "nce_audio"

    if "-o" in sys.argv:
        idx = sys.argv.index("-o")
        output_dir = sys.argv[idx + 1]

    os.makedirs(output_dir, exist_ok=True)

    # Parse HTML
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    parser = NCEParser()
    parser.feed(html)
    parser.close()

    lessons = parser.lessons[:num_lessons]
    print(f"Found {len(parser.lessons)} lessons, generating first {num_lessons}\n")

    # Generate audio for each lesson
    all_files = []
    for i, (num, lines) in enumerate(lessons):
        print(f"[{i+1}/{num_lessons}] Generating Lesson {num}...")
        try:
            path = await generate_lesson_audio(num, lines, output_dir)
            all_files.append(path)
        except Exception as e:
            print(f"  ERROR: {e}")

    # Combine all lessons into one file
    print(f"\nCombining {len(all_files)} lessons into single file...")
    concat_file = os.path.join(output_dir, "concat_all.txt")
    with open(concat_file, "w") as f:
        for path in all_files:
            f.write(f"file '{os.path.abspath(path)}'\n")

    combined_path = os.path.join(output_dir, f"nce_book1_lessons_1_{lessons[-1][0]}.mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
         "-acodec", "libmp3lame", "-ab", "128k", combined_path],
        capture_output=True, check=True,
    )
    os.remove(concat_file)

    size_mb = os.path.getsize(combined_path) / (1024 * 1024)
    print(f"\n✅ All lessons generated!")
    print(f"   Combined: {combined_path} ({size_mb:.1f} MB)")
    print(f"   Individual files in: {output_dir}/")


if __name__ == "__main__":
    asyncio.run(main())
