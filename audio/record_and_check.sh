#!/bin/bash
# Record audio from Mac microphone, then run phoneme-level pronunciation check.
#
# Usage:
#   ./record_and_check.sh [duration_seconds] [expected_text_file]
#
# Defaults: 120 seconds, lesson69_expected.txt
# Press Ctrl+C to stop early.

set -e

DURATION=${1:-120}
AUDIO_DIR="$(cd "$(dirname "$0")" && pwd)"
RECORDING="$AUDIO_DIR/my_recording.mp3"
EXPECTED=${2:-"$AUDIO_DIR/lesson69_expected.txt"}

echo "============================================"
echo "  录音 + 音素级口语纠错"
echo "============================================"
echo ""
echo "参考文本: $EXPECTED"
echo "录音时长: ${DURATION} 秒（提前结束按 Ctrl+C）"
echo ""
echo "--- 要朗读的句子 ---"
cat "$EXPECTED"
echo "---------------------"
echo ""
echo "按 Enter 开始录音..."
read -r

echo ""
echo "🔴 录音中... (剩余 ${DURATION}s)"
echo "   对着麦克风朗读句子，读完按 Ctrl+C 可提前结束"
echo ""

# Record using ffmpeg + avfoundation (Mac microphone)
ffmpeg -y -f avfoundation -i ":0" -t "$DURATION" \
    -acodec libmp3lame -ab 128k -ar 44100 \
    "$RECORDING" 2>&1 | grep -E "time=|Stream|Output" || true

echo ""
echo "✅ 录音完成: $RECORDING"
echo ""

# Run phoneme-level speech check
echo "开始音素识别 + 纠错..."
echo ""
python3 "$AUDIO_DIR/check_phonemes.py" "$RECORDING" "$EXPECTED" 2>&1 | grep -v "RuntimeWarning\|warnings\|rzn_\|logits\|NotOpenSSL"
