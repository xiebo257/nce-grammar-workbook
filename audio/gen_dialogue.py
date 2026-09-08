#!/usr/bin/env python3
"""
Generate multi-speaker dialogue audio from a text script.

Uses edge-tts (Microsoft Neural TTS) with different voices per speaker.

Dialogue format (one line per turn):
    SpeakerName: What they say.
    SpeakerName: Next line.

Or with explicit gender:
    [M] Tom: Hello!
    [F] Mary: Hi there!

Usage:
    python3 gen_dialogue.py <script.txt> [-o output.mp3]

Example:
    python3 gen_dialogue.py dialogue_sample.txt -o dialogue.mp3
"""

import asyncio
import edge_tts
import os
import re
import sys
import tempfile
import subprocess

# Voice pool (American English, neural voices)
MALE_VOICES = [
    "en-US-AndrewNeural",
    "en-US-BrianNeural",
    "en-US-ChristopherNeural",
    "en-US-EricNeural",
    "en-US-GuyNeural",
    "en-US-RogerNeural",
    "en-US-SteffanNeural",
]

FEMALE_VOICES = [
    "en-US-AvaNeural",
    "en-US-EmmaNeural",
    "en-US-AriaNeural",
    "en-US-JennyNeural",
    "en-US-MichelleNeural",
]

# Gender hints based on common English names
FEMALE_NAMES = {
    "mary", "jane", "susan", "kate", "ann", "anne", "lucy", "lily",
    "emma", "sarah", "jenny", "jennifer", "lisa", "karen", "michelle",
    "samantha", "victoria", "helen", "sue", "polly", "betty", "nora",
}

MALE_NAMES = {
    "tom", "jack", "john", "james", "bob", "bill", "william", "david",
    "mark", "peter", "paul", "eric", "steven", "michael", "richard",
    "ed", "eddie", "george", "frank", "joe", "jim", "ken", "roy",
}


def parse_dialogue(text: str) -> list[tuple[str, str, str]]:
    """Parse dialogue text into (speaker, gender, line) tuples.

    Format per line:
        [M] Name: text       (explicit gender)
        [F] Name: text       (explicit gender)
        Name: text           (infer gender from name)
    """
    lines = []
    for raw_line in text.strip().split("\n"):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        # Try [M]/[F] prefix
        gender_match = re.match(r"\[([MF])\]\s*(.+)", line)
        if gender_match:
            gender = gender_match.group(1)
            rest = gender_match.group(2)
        else:
            gender = None
            rest = line

        # Parse "Name: text" - allow periods, spaces in names (e.g. "Mr. Sawyer")
        colon_match = re.match(r"(.+?):\s+(.+)", rest)
        if colon_match:
            speaker = colon_match.group(1).strip()
            text_said = colon_match.group(2).strip()
        else:
            # Narrative text (no speaker) - skip or use narrator
            speaker = "Narrator"
            text_said = rest

        # Infer gender if not specified
        if not gender:
            name_lower = speaker.lower().split()[0]
            if name_lower in FEMALE_NAMES:
                gender = "F"
            elif name_lower in MALE_NAMES:
                gender = "M"
            else:
                gender = "M"  # default

        lines.append((speaker, gender, text_said))
    return lines


def assign_voices(dialogue: list[tuple[str, str, str]]) -> dict[str, str]:
    """Assign a unique TTS voice to each speaker based on gender."""
    voice_map = {}
    male_idx = 0
    female_idx = 0
    for speaker, gender, _ in dialogue:
        if speaker not in voice_map:
            if gender == "F":
                voice_map[speaker] = FEMALE_VOICES[female_idx % len(FEMALE_VOICES)]
                female_idx += 1
            else:
                voice_map[speaker] = MALE_VOICES[male_idx % len(MALE_VOICES)]
                male_idx += 1
    return voice_map


async def generate_dialogue(
    script_path: str,
    output_path: str,
) -> None:
    """Generate multi-speaker dialogue audio."""

    with open(script_path, "r") as f:
        text = f.read()

    dialogue = parse_dialogue(text)
    voice_map = assign_voices(dialogue)

    # Print voice assignment
    print("Voice assignment:")
    for speaker, voice in voice_map.items():
        gender = "Male" if voice in MALE_VOICES else "Female"
        print(f"  {speaker:<12} → {voice} ({gender})")
    print()

    # Generate audio for each line
    tmp_dir = tempfile.mkdtemp()
    audio_files = []

    for i, (speaker, gender, line) in enumerate(dialogue):
        voice = voice_map[speaker]
        tmp_path = os.path.join(tmp_dir, f"line_{i:03d}.mp3")

        print(f"  [{i+1}/{len(dialogue)}] {speaker}: {line[:50]}{'...' if len(line) > 50 else ''}")

        communicate = edge_tts.Communicate(line, voice, rate="+0%")
        await communicate.save(tmp_path)
        audio_files.append(tmp_path)

    print(f"\nConcatenating {len(audio_files)} segments...")

    # Create concat list for ffmpeg
    concat_file = os.path.join(tmp_dir, "concat.txt")
    with open(concat_file, "w") as f:
        for audio_path in audio_files:
            f.write(f"file '{audio_path}'\n")

    # Use ffmpeg to concatenate, adding small silence between lines
    # First, add 0.3s silence to end of each clip
    silenced_files = []
    for i, audio_path in enumerate(audio_files):
        silenced_path = os.path.join(tmp_dir, f"silence_{i:03d}.mp3")
        # Add 0.4s silence at end using apad
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", audio_path,
                "-af", "apad=pad_dur=0.4",
                "-acodec", "libmp3lame", "-ab", "128k",
                silenced_path,
            ],
            capture_output=True, check=True,
        )
        silenced_files.append(silenced_path)

    # Update concat file
    with open(concat_file, "w") as f:
        for audio_path in silenced_files:
            f.write(f"file '{audio_path}'\n")

    # Concatenate all
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-acodec", "libmp3lame", "-ab", "128k",
            output_path,
        ],
        capture_output=True, check=True,
    )

    # Cleanup
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\n✅ Dialogue audio saved: {output_path}")
    print(f"   Size: {size_mb:.2f} MB")
    print(f"   Speakers: {len(voice_map)}")
    print(f"   Lines: {len(dialogue)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 gen_dialogue.py <script.txt> [-o output.mp3]")
        sys.exit(1)

    script_path = sys.argv[1]
    output_path = "dialogue.mp3"

    if "-o" in sys.argv:
        idx = sys.argv.index("-o")
        output_path = sys.argv[idx + 1]

    if not os.path.exists(script_path):
        print(f"Error: script file not found: {script_path}")
        sys.exit(1)

    asyncio.run(generate_dialogue(script_path, output_path))
