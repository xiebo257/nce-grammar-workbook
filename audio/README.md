# Record an oral-practice attempt

From the repository root on your Mac:

```sh
./audio/record_oral.sh --lesson 1 --mode test
```

Press **Enter** to start. Speak into your microphone. Press **q** or **Ctrl+C** to stop early and save, or let the 90-second limit finish the recording. Ctrl+C at the initial Enter prompt cancels without recording.

FFmpeg and Python 3 are required. FFmpeg is already available on the Mac where this script was added. On another Mac, install it with `brew install ffmpeg` if needed. Allow microphone access for the terminal application in **System Settings → Privacy & Security → Microphone** when prompted.

## Choose the microphone

```sh
./audio/record_oral.sh --list-devices
./audio/record_oral.sh --lesson 1 --device 1
```

Choose an index from **AVFoundation audio devices**, not the video-device list. Index `0` is the default selection; list the devices to check which physical microphone that represents on your Mac. Recheck after connecting or disconnecting a headset.

## Label your task and retry

```sh
./audio/record_oral.sh --lesson 31 --mode test --duration 60 \
  --task 'Describe where two people are and what they are doing now.'

./audio/record_oral.sh --lesson 31 --mode test --attempt 2 --duration 60 \
  --task 'Retest: describe two different people and their current activities.'
```

Use `--mode read-aloud` if you read from a script. Use `--mode test` for an independent attempt and `--mode practice` for rehearsal. The default is `practice`; running without `--lesson` labels the recording `diagnostic`. A duration from 1 to 300 seconds is supported. See all options with `--help`.

For your first diagnostic:

```sh
./audio/record_oral.sh --mode test --duration 90 \
  --task 'Introduce yourself; describe nearby objects; say what you are doing and going to do; describe an ability and a preference; ask two questions.'
```

Keep it simple and speak without a full written script. The [oral-test plan](../nce1/teaching-plan/oral-practice-and-tests.md) explains what we will assess.

## Send the result for correction

Each attempt creates a unique folder below `audio/recordings/`, containing:

- `recording.wav`: the actual speech, saved as 24 kHz mono, 16-bit PCM.
- `session.json`: lesson, attempt, mode, task, actual duration, and recording details.
- `ffmpeg.log`: diagnostic information if the microphone or recording fails.

The script checks that audio frames can be decoded before reporting success. It also flags silence or extremely low levels; this is a simple signal check, not a test of speech quality or pronunciation. Play back the result using the `afplay` command it prints. If it is empty, very quiet, or using the wrong input, choose another microphone and record again.

Copy the final message printed by the script into our chat. It includes the absolute WAV path, so I can find both the recording and its task details. If you are chatting from another computer, attach the audio and include the task instead; that computer may not have access to the local path.

I can then process the submitted recording, correct the language, and give you a fresh speaking task. Pronunciation and fluency feedback require listening to the actual audio; a generated transcript alone is insufficient. I will identify any audio-access limitation before claiming to assess those skills. See the [correction procedure](../nce1/teaching-plan/oral-practice-and-tests.md) for the report format.

Recording is local and needs no API key. The script does not automatically upload, transcribe, or grade speech. If subsequent transcription uses an external API, its credentials and availability are checked at that step. Recordings and their metadata are ignored by Git, so attempts stay local by default.

The script can be run from any working directory by using its absolute path. Use `--output-dir PATH` to choose another recording folder, or `--yes` to start immediately without the Enter prompt. With `--yes`, the microphone starts as soon as FFmpeg opens the device.
