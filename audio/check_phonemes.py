#!/usr/bin/env python3
"""
Phoneme-level pronunciation checker.

Uses wav2vec2 (vitouphy/wav2vec2-xls-r-300m-timit-phoneme) to recognize
actual phonemes from your recording, and g2p_en to generate expected
IPA phonemes from the reference text. Then aligns and compares them
to pinpoint specific pronunciation errors.

Usage:
    python3 check_phonemes.py <recording.mp3> <expected_text_file.txt>

Example:
    python3 check_phonemes.py my_recording.mp3 lesson69_expected.txt
"""

import sys
import os
import re
import difflib
import time

# Use Chinese mirror for HuggingFace
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# ARPABET (g2p_en output) → IPA (wav2vec2 model output) mapping
ARPABET_TO_IPA = {
    # Vowels
    "AA": "ɑ", "AE": "æ", "AH": "ə", "AO": "ɔ", "AW": "aʊ", "AY": "aɪ",
    "EH": "ɛ", "ER": "ɝ", "EY": "eɪ", "IH": "ɪ", "IY": "i",
    "OW": "oʊ", "OY": "ɔɪ", "UH": "ʊ", "UW": "u",
    # Consonants
    "B": "b", "CH": "ʧ", "D": "d", "DH": "ð", "DX": "ɾ", "F": "f",
    "G": "g", "HH": "h", "JH": "ʤ", "K": "k", "L": "l", "M": "m",
    "N": "n", "NG": "ŋ", "P": "p", "R": "ɹ", "S": "s", "SH": "ʃ",
    "T": "t", "TH": "θ", "V": "v", "W": "w", "Y": "j", "Z": "z",
    "ZH": "ʒ",
    # Special
    "": "",
    " ": " ",
}

PUNCT_RE = re.compile(r"[^\w\s'-]")


def text_to_phonemes(text: str) -> list[str]:
    """Convert English text to IPA phonemes using g2p_en."""
    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        from g2p_en import G2p
        g2p = G2p()
    # g2p outputs ARPABET symbols, with stress markers (0,1,2)
    arpabet_list = g2p(text)
    # Convert to IPA, strip stress numbers, filter spaces/punctuation
    result = []
    for symbol in arpabet_list:
        # Strip stress markers (e.g. "AH0" → "AH", "AE1" → "AE")
        base = re.sub(r"[0-2]$", "", symbol) if len(symbol) > 1 and symbol[-1] in "012" else symbol
        if base in ARPABET_TO_IPA:
            ipa = ARPABET_TO_IPA[base]
            if ipa and ipa != " ":
                result.append(ipa)
        elif symbol.strip() and symbol not in [",", ".", "?", "!", ":", ";"]:
            result.append(symbol.lower())
    return result


def audio_to_phonemes(audio_path: str, model, processor) -> list[str]:
    """Extract phonemes from audio using wav2vec2."""
    import torch
    import librosa

    audio, sr = librosa.load(audio_path, sr=16000)
    # Move input to same device as model
    device = next(model.parameters()).device
    input_tensor = torch.tensor(audio).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(input_tensor).logits
    predicted_ids = torch.argmax(logits, dim=-1)

    # Map IDs to phoneme tokens directly (not using decode which concatenates)
    # CTC: collapse repeated tokens, skip blank (|) and [PAD]
    vocab = processor.tokenizer.get_vocab()
    id_to_token = {v: k for k, v in vocab.items()}
    raw_ids = predicted_ids[0].tolist()

    # CTC decoding: collapse consecutive duplicates, skip blank/pad
    phonemes = []
    prev_id = None
    for tid in raw_ids:
        if tid == prev_id:
            continue  # collapse repeats
        prev_id = tid
        token = id_to_token.get(tid, "")
        if token in ("|", "[PAD]", "[UNK]", "", " "):
            continue
        phonemes.append(token)
    return phonemes


def load_model():
    """Load the wav2vec2 phoneme model."""
    import torch
    from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

    MODEL = "vitouphy/wav2vec2-xls-r-300m-timit-phoneme"
    processor = Wav2Vec2Processor.from_pretrained(MODEL)
    model = Wav2Vec2ForCTC.from_pretrained(MODEL)
    # Try to use MPS (Metal) for faster inference
    device = "cpu"
    if torch.backends.mps.is_available():
        model = model.to("mps")
        device = "mps"
    model.eval()
    print(f"  Model loaded on {device}")
    return model, processor


# IPA phoneme descriptions for human-readable output
PHONEME_NAMES = {
    "ɑ": "open back unrounded vowel (as in 'father')",
    "æ": "near-open front unrounded vowel (as in 'cat')",
    "ə": "schwa (as in 'about')",
    "ɔ": "open-mid back rounded vowel (as in 'thought')",
    "aʊ": "diphthong (as in 'now')",
    "aɪ": "diphthong (as in 'my')",
    "ɛ": "open-mid front unrounded vowel (as in 'bed')",
    "ɝ": "r-colored vowel (as in 'bird')",
    "eɪ": "diphthong (as in 'say')",
    "ɪ": "near-close front unrounded vowel (as in 'bit')",
    "i": "close front unrounded vowel (as in 'see')",
    "oʊ": "diphthong (as in 'go')",
    "ɔɪ": "diphthong (as in 'boy')",
    "ʊ": "near-close back rounded vowel (as in 'book')",
    "u": "close back rounded vowel (as in 'blue')",
    "b": "voiced bilabial stop",
    "ʧ": "voiceless postalveolar affricate (as in 'chair')",
    "d": "voiced alveolar stop",
    "ð": "voiced dental fricative (as in 'the')",
    "ɾ": "alveolar flap (as in 'butter')",
    "f": "voiceless labiodental fricative",
    "g": "voiced velar stop",
    "h": "voiceless glottal fricative",
    "ʤ": "voiced postalveolar affricate (as in 'judge')",
    "k": "voiceless velar stop",
    "l": "lateral approximant",
    "m": "bilabial nasal",
    "n": "alveolar nasal",
    "ŋ": "velar nasal (as in 'sing')",
    "p": "voiceless bilabial stop",
    "ɹ": "alveolar approximant (English r)",
    "s": "voiceless alveolar sibilant",
    "ʃ": "voiceless postalveolar sibilant (as in 'she')",
    "t": "voiceless alveolar stop",
    "θ": "voiceless dental fricative (as in 'think')",
    "v": "voiced labiodental fricative",
    "w": "labio-velar approximant",
    "j": "palatal approximant (as in 'yes')",
    "z": "voiced alveolar sibilant",
    "ʒ": "voiced postalveolar sibilant (as in 'measure')",
}


def compare_phonemes(expected: list[str], actual: list[str]) -> None:
    """Align and compare phoneme sequences, report mismatches."""
    print("=" * 60)
    print("PHONEME CHECK REPORT")
    print("=" * 60)

    matcher = difflib.SequenceMatcher(None, expected, actual)
    errors = []
    matches = 0
    total = len(expected)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            matches += (i2 - i1)
            continue
        exp_chunk = expected[i1:i2]
        act_chunk = actual[j1:j2]
        if tag == "replace":
            errors.append(("mispronounced", exp_chunk, act_chunk, i1))
        elif tag == "delete":
            errors.append(("missing", exp_chunk, [], i1))
        elif tag == "insert":
            errors.append(("extra", [], act_chunk, i1))

    accuracy = matches / total * 100 if total > 0 else 0
    print(f"\nPhoneme accuracy: {matches}/{total} ({accuracy:.1f}%)\n")

    if not errors:
        print("✓ Perfect! All phonemes matched.\n")
    else:
        print(f"Found {len(errors)} issue(s):\n")
        for idx, (kind, exp, act, pos) in enumerate(errors, 1):
            exp_str = " ".join(exp)
            act_str = " ".join(act) if act else "(nothing)"
            if kind == "mispronounced":
                # Find phoneme descriptions
                exp_desc = "; ".join(f"/{p}/ = {PHONEME_NAMES.get(p, '?')}" for p in exp)
                act_desc = "; ".join(f"/{p}/ = {PHONEME_NAMES.get(p, '?')}" for p in act)
                print(f"  {idx}. [Mispronounced] Expected: /{exp_str}/ → Heard: /{act_str}/")
                print(f"     Expected: {exp_desc}")
                print(f"     Heard:    {act_desc}")
            elif kind == "missing":
                desc = "; ".join(f"/{p}/ = {PHONEME_NAMES.get(p, '?')}" for p in exp)
                print(f"  {idx}. [Missing] You didn't produce: /{exp_str}/")
                print(f"     {desc}")
            elif kind == "extra":
                desc = "; ".join(f"/{p}/ = {PHONEME_NAMES.get(p, '?')}" for p in act)
                print(f"  {idx}. [Extra] You added: /{act_str}/")
                print(f"     {desc}")
            print()

    # Print full comparison
    print("-" * 60)
    print("Expected phonemes:", " ".join(expected))
    print("-" * 60)
    print("Your phonemes:    ", " ".join(actual))
    print("-" * 60)


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 check_phonemes.py <recording.mp3> <expected_text.txt>")
        print("Example: python3 check_phonemes.py my_recording.mp3 lesson69_expected.txt")
        sys.exit(1)

    audio_path = sys.argv[1]
    text_path = sys.argv[2]

    if not os.path.exists(audio_path):
        print(f"Error: audio file not found: {audio_path}")
        sys.exit(1)
    if not os.path.exists(text_path):
        print(f"Error: text file not found: {text_path}")
        sys.exit(1)

    with open(text_path, "r") as f:
        expected_text = f.read().strip()

    # Split text into individual sentences for per-sentence analysis
    sentences = [s.strip() for s in re.split(r"[.\n]+", expected_text) if s.strip()]

    print(f"Expected text: {expected_text}")
    print(f"Sentences: {len(sentences)}")
    print()

    # Generate expected phonemes
    print("Generating expected phonemes (g2p_en)...")
    expected_phonemes = text_to_phonemes(expected_text)
    print(f"Expected phonemes ({len(expected_phonemes)}): {' '.join(expected_phonemes)}")
    print()

    # Load model
    print("Loading wav2vec2 phoneme model...")
    t0 = time.time()
    model, processor = load_model()
    print(f"  Load time: {time.time()-t0:.1f}s")

    # Extract phonemes from audio
    print(f"\nTranscribing audio: {audio_path}")
    t1 = time.time()
    actual_phonemes = audio_to_phonemes(audio_path, model, processor)
    t2 = time.time()
    print(f"  Inference: {t2-t1:.2f}s")
    print(f"  Actual phonemes ({len(actual_phonemes)}): {' '.join(actual_phonemes)}")
    print()

    # Compare
    compare_phonemes(expected_phonemes, actual_phonemes)


if __name__ == "__main__":
    main()
