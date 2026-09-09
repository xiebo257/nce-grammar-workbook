#!/usr/bin/env python3
"""
Phoneme-level pronunciation checker with word-level breakdown.

Uses wav2vec2 (vitouphy/wav2vec2-xls-r-300m-timit-phoneme) to recognize
actual phonemes from your recording, and g2p_en to generate expected
IPA phonemes from the reference text. Aligns and compares them per word
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

# Word-final plosives that are commonly unreleased (失爆)
# These are often not detected by ASR models even when correctly articulated
UNRELEASED_STOPS = {"t", "d", "k", "g", "p", "b"}

# IPA phoneme descriptions
PHONEME_NAMES = {
    "ɑ": "ɑ (as in father)", "æ": "æ (as in cat)", "ə": "ə schwa (as in about)",
    "ɔ": "ɔ (as in thought)", "aʊ": "aʊ (as in now)", "aɪ": "aɪ (as in my)",
    "ɛ": "ɛ (as in bed)", "ɝ": "ɝ r-colored (as in bird)", "eɪ": "eɪ (as in say)",
    "ɪ": "ɪ (as in bit)", "i": "i (as in see)", "oʊ": "oʊ (as in go)",
    "ɔɪ": "ɔɪ (as in boy)", "ʊ": "ʊ (as in book)", "u": "u (as in blue)",
    "b": "b voiced stop", "ʧ": "ʧ (as in chair)", "d": "d voiced stop",
    "ð": "ð (as in the)", "ɾ": "ɾ flap (as in butter)", "f": "f fricative",
    "g": "g voiced stop", "h": "h (as in he)", "ʤ": "ʤ (as in judge)",
    "k": "k voiceless stop", "l": "l lateral", "m": "m nasal",
    "n": "n nasal", "ŋ": "ŋ (as in sing)", "p": "p voiceless stop",
    "ɹ": "ɹ English r", "s": "s (as in see)", "ʃ": "ʃ (as in she)",
    "t": "t voiceless stop", "θ": "θ (as in think)", "v": "v fricative",
    "w": "w (as in we)", "j": "j (as in yes)", "z": "z (as in zoo)",
    "ʒ": "ʒ (as in measure)",
}


def text_to_phonemes_by_word(text: str) -> list[tuple[str, list[str]]]:
    """Convert text to (word, [ipa_phonemes]) pairs using g2p_en."""
    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        from g2p_en import G2p
        g2p = G2p()

    # Split into words, keeping track of positions
    words = PUNCT_RE.sub("", text).split()
    result = []
    for word in words:
        arpabet_list = g2p(word)
        phonemes = []
        for symbol in arpabet_list:
            base = re.sub(r"[0-2]$", "", symbol) if len(symbol) > 1 and symbol[-1] in "012" else symbol
            if base in ARPABET_TO_IPA:
                ipa = ARPABET_TO_IPA[base]
                if ipa and ipa != " ":
                    phonemes.append(ipa)
            elif symbol.strip() and symbol not in [",", ".", "?", "!", ":", ";", " "]:
                phonemes.append(symbol.lower())
        result.append((word, phonemes))
    return result


def audio_to_phonemes(audio_path: str, model, processor) -> list[str]:
    """Extract phonemes from audio using wav2vec2."""
    import torch
    import librosa

    audio, sr = librosa.load(audio_path, sr=16000)
    device = next(model.parameters()).device
    input_tensor = torch.tensor(audio).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(input_tensor).logits
    predicted_ids = torch.argmax(logits, dim=-1)

    vocab = processor.tokenizer.get_vocab()
    id_to_token = {v: k for k, v in vocab.items()}
    raw_ids = predicted_ids[0].tolist()

    # CTC decoding: collapse consecutive duplicates, skip blank/pad/space
    phonemes = []
    prev_id = None
    for tid in raw_ids:
        if tid == prev_id:
            continue
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
    device = "cpu"
    if torch.backends.mps.is_available():
        model = model.to("mps")
        device = "mps"
    model.eval()
    print(f"  Model loaded on {device}")
    return model, processor


def compare_phonemes_by_word(
    word_phonemes: list[tuple[str, list[str]]],
    actual: list[str],
) -> None:
    """Compare phonemes using global alignment, then map errors to words."""

    # Build flat expected sequence with word boundaries
    expected = []
    word_spans = []  # (word, start_idx, end_idx)
    for word, phs in word_phonemes:
        start = len(expected)
        expected.extend(phs)
        end = len(expected)
        word_spans.append((word, phs, start, end))

    print("=" * 60)
    print("PHONEME CHECK REPORT")
    print("=" * 60)

    # Show expected per-word breakdown
    print("\nExpected pronunciation per word:")
    for word, phs, _, _ in word_spans:
        ph_str = " ".join(phs) if phs else "(empty)"
        print(f"  {word:<12} → /{ph_str}/")

    # Global alignment
    matcher = difflib.SequenceMatcher(None, expected, actual)
    matches = 0
    total = len(expected)

    # Collect opcodes and map to words
    # For each word, track what was matched and what errors occurred
    word_results = []
    for word, phs, ws, we in word_spans:
        word_results.append({
            "word": word, "expected": phs, "matched": [], "missing": [],
            "extra": [], "mispronounced": [],
        })

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            matches += (i2 - i1)
            # Map matched phonemes to words
            for idx in range(i1, i2):
                for wi, (word, phs, ws, we) in enumerate(word_spans):
                    if ws <= idx < we:
                        word_results[wi]["matched"].append(expected[idx])
                        break
        elif tag == "replace":
            # Mispronounced: expected[i1:i2] → actual[j1:j2]
            exp_chunk = expected[i1:i2]
            act_chunk = actual[j1:j2]
            for idx in range(i1, i2):
                for wi, (word, phs, ws, we) in enumerate(word_spans):
                    if ws <= idx < we:
                        act_idx = idx - i1
                        exp_p = exp_chunk[idx - i1]
                        if act_idx < len(act_chunk):
                            act_p = act_chunk[act_idx]
                            word_results[wi]["mispronounced"].append((exp_p, act_p))
                        else:
                            # More expected than actual → rest is missing
                            word_results[wi]["missing"].append(exp_p)
                        break
        elif tag == "delete":
            # Missing: expected[i1:i2] not found in actual
            exp_chunk = expected[i1:i2]
            for idx in range(i1, i2):
                for wi, (word, phs, ws, we) in enumerate(word_spans):
                    if ws <= idx < we:
                        local_idx = idx - ws
                        word_results[wi]["missing"].append(phs[local_idx])
                        break
        elif tag == "insert":
            # Extra: actual[j1:j2] has no corresponding expected
            act_chunk = actual[j1:j2]
            # Attribute to the word that precedes the insertion point
            for wi, (word, phs, ws, we) in enumerate(word_spans):
                if i1 < we and i1 >= ws:
                    for p in act_chunk:
                        word_results[wi]["extra"].append(p)
                    break
            else:
                # If no word found, attribute to last word
                if word_results:
                    for p in act_chunk:
                        word_results[-1]["extra"].append(p)

    accuracy = matches / total * 100 if total > 0 else 0
    print(f"\nPhoneme accuracy: {matches}/{total} ({accuracy:.1f}%)")
    print()

    # Print errors grouped by word
    total_errors = sum(
        len(r["missing"]) + len(r["extra"]) + len(r["mispronounced"])
        for r in word_results
    )
    if total_errors == 0:
        print("✓ Perfect! All phonemes matched.\n")
    else:
        print(f"Found {total_errors} issue(s), grouped by word:\n")
        error_num = 0
        for wr in word_results:
            n_errs = len(wr["missing"]) + len(wr["extra"]) + len(wr["mispronounced"])
            if n_errs == 0:
                continue
            exp_str = " ".join(wr["expected"]) if wr["expected"] else "(empty)"
            matched_str = " ".join(wr["matched"]) if wr["matched"] else "—"
            print(f"  ┌─ \"{wr['word']}\"  expected: /{exp_str}/  matched: /{matched_str}/")

            for exp_p, act_p in wr["mispronounced"]:
                error_num += 1
                print(f"  │  #{error_num} [Mispronounced] /{exp_p}/ → /{act_p}/")
                print(f"  │       Expected: /{exp_p}/ = {PHONEME_NAMES.get(exp_p, '?')}")
                print(f"  │       Heard:    /{act_p}/ = {PHONEME_NAMES.get(act_p, '?')}")

            for p in wr["missing"]:
                error_num += 1
                is_unreleased = p in UNRELEASED_STOPS
                print(f"  │  #{error_num} [Missing] /{p}/")
                print(f"  │       /{p}/ = {PHONEME_NAMES.get(p, '?')}")
                if is_unreleased:
                    print(f"  │       ⚠️  可能是失爆（unreleased stop）")
                    print(f"  │       练习时尝试更清晰地释放尾音 /{p}/")

            for p in wr["extra"]:
                error_num += 1
                print(f"  │  #{error_num} [Extra] /{p}/")
                print(f"  │       /{p}/ = {PHONEME_NAMES.get(p, '?')}")

            print(f"  └─")
            print()

    # Print full sequence comparison
    print("-" * 60)
    print("Expected:", " ".join(expected))
    print("Actual:  ", " ".join(actual))
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

    print(f"Expected text: {expected_text}")
    print()

    # Generate expected phonemes per word
    print("Generating expected phonemes (g2p_en)...")
    word_phonemes = text_to_phonemes_by_word(expected_text)
    total_expected = sum(len(phs) for _, phs in word_phonemes)
    print(f"  Words: {len(word_phonemes)}, Phonemes: {total_expected}")
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
    print(f"  Detected phonemes: {len(actual_phonemes)}")
    print()

    # Compare with word-level breakdown
    compare_phonemes_by_word(word_phonemes, actual_phonemes)


if __name__ == "__main__":
    main()
