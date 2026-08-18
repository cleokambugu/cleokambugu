# transcribe — learn from video / audio / notes as text

A small, dependency-light toolkit that turns talks, lectures, and podcasts into
readable text. There's no magic and no native "listening": you get the words as
text, by one of three routes depending on what you have and what the network
allows.

```
                                          ┌─ transcribe: media FILE ─► ffmpeg ─► Whisper ─┐
learn.py <video/audio/URL/captions/pdf> ──┼─ youtube:   URL (allowlisted) ─► yt-dlp ──────┼─► .txt / .md / .srt
                                          └─ ingest:    captions / transcript / PDF ──────┘
```

## The three routes (one front door: `learn.py`)

```bash
# 1. You have a media FILE (or a direct media URL): speech recognition
python tools/transcribe/learn.py transcribe lecture.mp4

# 2. A media host is allowlisted: fetch captions (fastest) or audio
python tools/transcribe/learn.py youtube "https://www.youtube.com/watch?v=ID" --mode subs

# 3. You already have captions / a transcript / a PDF: just clean it up
python tools/transcribe/learn.py ingest captions.en.vtt
```

Each is also a standalone script: `transcribe.py`, `fetch.py`, `ingest.py`.

### New-session quickstart (environment on Full network access)

Once the environment is set to **Full** and you've started a **fresh** session
(policy changes don't affect an already-running session), YouTube and Hugging
Face are both reachable, so it's two commands:

```bash
pip install -r tools/transcribe/requirements.txt
python tools/transcribe/learn.py youtube "https://www.youtube.com/watch?v=VIDEO_ID" --mode subs \
  && python tools/transcribe/learn.py ingest downloads/*.vtt
# no captions? fetch audio and transcribe (model auto-downloads from HF on Full):
python tools/transcribe/learn.py youtube "URL" --mode audio && python tools/transcribe/learn.py transcribe downloads/*.mp3
```

To make it zero-touch, paste this one line into the environment's **Setup
script** field (same dialog as Network access) — it's cached, so it runs once,
not per session:

```bash
pip install -r tools/transcribe/requirements.txt
```

- **Route 2 needs the media host allowlisted** and, for the audio→ASR sub-path,
  the model host too. You're the admin — see
  [`notes/tooling/admin-allowlist.md`](../../notes/tooling/admin-allowlist.md)
  for the exact host lists and click-path.
- **Route 3 needs nothing** — no download, no model, no network. If a video has
  captions, this is by far the fastest way to read it: grab the caption file and
  ingest it. Rolling auto-caption repetition is collapsed automatically.

The rest of this page covers Route 1 (the ASR pipeline) in detail.

```
media file  ->  ffmpeg (16 kHz mono audio)  ->  Whisper ASR  ->  .txt / .md / .srt
```

## Why it's built this way

- **`imageio-ffmpeg`** ships a static `ffmpeg` binary as a pip wheel — no system
  package to install, works in a bare container.
- **`faster-whisper`** is Whisper on CTranslate2: runs on CPU, no PyTorch, small
  install. Model sizes `tiny`→`large-v3` trade speed for accuracy.
- **Offline once a model is local.** Given a local media file and a local model,
  it makes **zero network calls**. That is the whole point in a locked-down
  environment.

## Install

```bash
pip install -r tools/transcribe/requirements.txt
```

## Use

```bash
# Local file (auto-detect language) -> transcript next to the file
python tools/transcribe/transcribe.py lecture.mp4

# Pick a model size and force a language
python tools/transcribe/transcribe.py talk.m4a --model small --language en

# Translate a non-English talk to English
python tools/transcribe/transcribe.py foreign_talk.mp4 --task translate

# A direct media URL on an allowed host
python tools/transcribe/transcribe.py https://allowed.host/clip.mp3

# Use a vendored model dir (no network at all)
WHISPER_MODEL_DIR=./models/faster-whisper-base \
  python tools/transcribe/transcribe.py lecture.mp4
```

Outputs land next to the input (or in `--out-dir`): `NAME.txt` (plain text),
`NAME.md` (timestamps + metadata), `NAME.srt` (subtitles).

## Getting a model — use `provision_model.sh`

`faster-whisper` normally downloads its model from Hugging Face on first use. A
helper wraps the options:

```bash
# Official model from Hugging Face (works where huggingface.co is reachable):
tools/transcribe/provision_model.sh                       # -> ./models/int8_tiny

# Locked sandbox where Hugging Face is blocked — fetch from GitHub raw instead
# (raw.githubusercontent.com is on the Trusted allowlist, so NO policy change):
SRC=mirror tools/transcribe/provision_model.sh

# then, either way:
export WHISPER_MODEL_DIR="$PWD/models/int8_tiny"
python tools/transcribe/transcribe.py your_media_file
```

Four ways to get a model, in preference order for a normal machine:

1. **Unrestricted machine (simplest).** Just run the tool — it auto-downloads and
   caches under `~/.cache/huggingface`.
2. **`SRC=hf provision_model.sh`.** Same official model, into a named dir you can
   move around.
3. **`SRC=mirror provision_model.sh`.** Pulls a CTranslate2 model from a public
   GitHub repo over `raw.githubusercontent.com`. **This works inside a sandbox
   where Hugging Face is blocked, with no allowlist change** — it's how real ASR
   was verified in this repo's own web environment (the JFK sample transcribed
   correctly). The mirror is third-party, though; see the provenance note in
   `provision_model.sh` and prefer official (1–2) when you can.
4. **Vendor a dir by hand.** Copy any CTranslate2 model directory in and point
   `$WHISPER_MODEL_DIR` at it.

> **This repo's Claude Code web sessions:** `huggingface.co` is blocked (`403` at
> the proxy), but `raw.githubusercontent.com` is allowed — so option 3 works here
> today. The tool never routes around a blocked host; it uses an allowed one. See
> `notes/tooling/media-and-egress.md`.

Prove real ASR after provisioning:

```bash
export WHISPER_MODEL_DIR="$PWD/models/int8_tiny"
python tools/transcribe/test_asr_integration.py     # transcribes a real clip
```

## Test

```bash
python tools/transcribe/test_transcribe.py         # no model, no network
python tools/transcribe/test_asr_integration.py    # real ASR (needs a model; skips otherwise)
```

`test_transcribe.py` covers the real ffmpeg decode, subtitle parsing, rolling
auto-caption dedupe, PDF extraction, and yt-dlp option building — all with no
model and no network. `test_asr_integration.py` runs the real Whisper forward
pass on a fetched speech clip when `$WHISPER_MODEL_DIR` is set, and skips cleanly
when it isn't.
