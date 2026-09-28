#!/bin/bash
# Record a labelled oral-practice attempt using macOS AVFoundation and FFmpeg.
set -euo pipefail
umask 077

usage() {
  cat <<'EOF'
Usage: ./audio/record_oral.sh [options]

Record your microphone locally, then give Codex the printed WAV path.
Press Enter to start; press q (or Ctrl+C) to stop and save early.

Options:
  --lesson NUMBER       NCE lesson, 1–144 (default: diagnostic)
  --duration SECONDS    Maximum recording time, 1–300 (default: 90)
  --attempt NUMBER      Attempt number, 1–99 (default: 1)
  --device INDEX        Audio-device index from --list-devices (default: 0)
  --task TEXT           Question or task you are answering
  --mode MODE           practice, test, or read-aloud (default: practice)
  --output-dir PATH     Save attempts here (default: audio/recordings)
  --list-devices        List camera and microphone devices, then exit
  --yes                Start without the Enter prompt
  -h, --help            Show this help

Examples:
  ./audio/record_oral.sh
  ./audio/record_oral.sh --lesson 1 --mode test
  ./audio/record_oral.sh --lesson 31 --attempt 2 --duration 60 \
    --task 'Describe what two people are doing now.'
  ./audio/record_oral.sh --list-devices
  ./audio/record_oral.sh --lesson 1 --device 1

Microphone access: allow your terminal app in macOS System Settings >
Privacy & Security > Microphone if requested. Recording needs no API key.
EOF
}

fail() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

require_value() {
  [[ $# -ge 2 && -n "$2" ]] || fail "Missing value for $1. See --help."
}

check_number() {
  local value="$1" maximum="$2" label="$3" minimum="${4:-1}"
  [[ "$value" =~ ^[0-9]{1,3}$ ]] || fail "$label must be an integer between $minimum and $maximum."
  local number=$((10#$value))
  (( number >= minimum && number <= maximum )) || fail "$label must be between $minimum and $maximum."
}

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
output_dir="$script_dir/recordings"
lesson="diagnostic"
duration=90
attempt=1
device=0
task=""
mode="practice"
start_now=0
list_devices=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --lesson|--duration|--attempt|--device|--task|--mode|--output-dir)
      require_value "$@"
      case "$1" in
        --lesson) lesson="$2" ;;
        --duration) duration="$2" ;;
        --attempt) attempt="$2" ;;
        --device) device="$2" ;;
        --task) task="$2" ;;
        --mode) mode="$2" ;;
        --output-dir) output_dir="$2" ;;
      esac
      shift 2
      ;;
    --list-devices) list_devices=1; shift ;;
    --yes) start_now=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) fail "Unknown option: $1. See --help." ;;
  esac
done

if [[ "$lesson" != "diagnostic" ]]; then
  check_number "$lesson" 144 'Lesson'
  printf -v lesson '%03d' "$((10#$lesson))"
fi
check_number "$duration" 300 'Duration'
check_number "$attempt" 99 'Attempt'
check_number "$device" 999 'Device index' 0
duration=$((10#$duration))
attempt=$((10#$attempt))
device=$((10#$device))
case "$mode" in
  practice|test|read-aloud) ;;
  *) fail 'Mode must be practice, test, or read-aloud.' ;;
esac

[[ "$(uname -s)" == "Darwin" ]] || fail 'This recorder uses macOS microphones (AVFoundation).'
command -v ffmpeg >/dev/null 2>&1 || fail 'FFmpeg is missing. Install it with: brew install ffmpeg'

if (( list_devices )); then
  # AVFoundation exits nonzero after listing because no input was selected.
  device_output="$(ffmpeg -hide_banner -f avfoundation -list_devices true -i '' 2>&1 || true)"
  printf '%s\n' "$device_output"
  [[ "$device_output" == *'AVFoundation audio devices:'* ]] || fail 'FFmpeg could not list AVFoundation audio devices.'
  printf '\nUse the index under "AVFoundation audio devices" with --device.\n'
  exit 0
fi

command -v python3 >/dev/null 2>&1 || fail 'Python 3 is needed to validate and label the WAV file.'
printf 'Lesson: %s | Attempt: %s | Mode: %s | Maximum: %s seconds\n' "$lesson" "$attempt" "$mode" "$duration"
if [[ -n "$task" ]]; then
  printf 'Task: %s\n' "$task"
fi
if (( ! start_now )); then
  [[ -t 0 ]] || fail 'Run in an interactive terminal, or use --yes to skip the start prompt.'
  printf 'Press Enter to start recording (Ctrl+C here cancels)... '
  read -r _ || fail 'No start confirmation received.'
fi

mkdir -p -- "$output_dir"
output_dir="$(cd -- "$output_dir" && pwd)"
stamp="$(date '+%Y-%m-%d_%H-%M-%S')"
session_dir="$(mktemp -d "$output_dir/${stamp}_lesson-${lesson}_attempt-${attempt}_XXXXXX")"
partial="$session_dir/recording.partial.wav"
recording="$session_dir/recording.wav"
log_file="$session_dir/ffmpeg.log"
started_at="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
interrupted=0
trap 'interrupted=1' INT

printf '\nRecording microphone %s. Speak now. Press q or Ctrl+C to stop early.\n' "$device"
printf 'If it cannot start, check microphone access for your terminal app.\n'
# Keep FFmpeg attached to terminal input so q and Ctrl+C can finalise the WAV.
# 24 kHz mono PCM retains speech detail and stays below 15 MB at 300 seconds.
if ffmpeg -hide_banner -loglevel warning -nostats -n \
  -f avfoundation -i ":$device" -t "$duration" \
  -map 0:a:0 -ac 1 -ar 24000 -c:a pcm_s16le "$partial" 2>"$log_file"; then
  record_status=0
else
  record_status=$?
fi
trap - INT

if (( record_status != 0 )); then
  if ! (( interrupted && record_status == 255 )); then
    cat "$log_file" >&2
    fail "Recording failed (FFmpeg exit $record_status). Check --list-devices and microphone permission. Details: $log_file"
  fi
fi

# Only publish a finished recording after decoding its PCM frames successfully.
if ! python3 - "$partial" "$session_dir/session.json" "$lesson" "$attempt" \
  "$duration" "$device" "$mode" "$task" "$started_at" <<'PY'
import array
import json
from pathlib import Path
import sys
import wave

audio_path, metadata_path, lesson, attempt, limit, device, mode, task, started = sys.argv[1:]
try:
  with wave.open(audio_path, 'rb') as audio:
    rate = audio.getframerate()
    count = audio.getnframes()
    if audio.getnchannels() != 1 or audio.getsampwidth() != 2 or rate != 24000:
      raise ValueError('unexpected audio format')
    frames = audio.readframes(count)
    if len(frames) != count * 2:
      raise ValueError('incomplete audio data')
    seconds = count / rate
    if seconds < 0.25:
      raise ValueError('less than 0.25 seconds of audio; please record again')
    samples = array.array('h', frames)
    if sys.byteorder != 'little':
      samples.byteswap()
    peak = max(abs(value) for value in samples)
except (OSError, EOFError, ValueError, wave.Error) as exc:
  print(f'Audio validation failed: {exc}', file=sys.stderr)
  sys.exit(1)

metadata = {
  'audio_file': 'recording.wav',
  'lesson': int(lesson) if lesson != 'diagnostic' else 'diagnostic',
  'attempt': int(attempt),
  'mode': mode,
  'task': task,
  'started_at_utc': started,
  'duration_seconds': round(seconds, 3),
  'maximum_duration_seconds': int(limit),
  'audio_device_index': int(device),
  'sample_rate_hz': rate,
  'channels': 1,
  'format': 'PCM signed 16-bit WAV',
  'peak_amplitude': peak,
  'assessment_status': 'not assessed',
}
Path(metadata_path).write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Validated {seconds:.1f} seconds of audio.')
if peak < 100:
  print('The recording is silent or very quiet. Play it back and check the selected microphone before submitting.')
PY
then
  fail "No finished recording was saved. Partial audio and diagnostic log are in: $session_dir"
fi

mv -- "$partial" "$recording"
printf '\nSaved recording:\n%s\n\nTask details:\n%s/session.json\n' "$recording" "$session_dir"
printf '\nPlay it back:\n  afplay %q\n' "$recording"
printf '\nSend this message to Codex:\n'
printf 'Please transcribe and correct my oral test. Audio: %s\n' "$recording"
printf 'Read the adjacent session.json for the lesson, task, and attempt.\n'
printf 'Explain language corrections, assess pronunciation only from audible evidence, and give me a fresh retest.\n'
