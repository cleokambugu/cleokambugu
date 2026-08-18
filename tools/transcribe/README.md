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

## Getting a model (the one thing that needs network — once)

`faster-whisper` normally downloads its model from Hugging Face on first use.
Three ways to get one, depending on your environment:

1. **Unrestricted machine (simplest).** Just run the tool — it downloads the
   model automatically and caches it under `~/.cache/huggingface`. Do this once
   on any normal laptop/server.
2. **Vendor the model, point `$WHISPER_MODEL_DIR` at it.** Copy a CTranslate2
   Whisper model directory (the folder containing `model.bin`, `config.json`,
   `tokenizer.json`, `vocabulary.txt`) into the environment and set the env var.
   No network needed at run time. This is how you use it inside a sandbox where
   Hugging Face is blocked.
3. **Allowlist the host.** If you control the environment's network policy, allow
   `huggingface.co` (and its CDN) so option 1 works in place. See
   [Claude Code on the web — network policies](https://code.claude.com/docs/en/claude-code-on-the-web).

> **Note for this repo's Claude Code web sessions:** `huggingface.co` is blocked
> by the egress policy here (a `403` at the proxy), exactly like the media hosts.
> So in a web session, use option 2 (hand over a model dir) or option 3 (an admin
> allowlists the host). The tool never tries to route around a blocked host — see
> `notes/tooling/media-and-egress.md`.

## Test

```bash
python tools/transcribe/test_transcribe.py
```

Covers the real ffmpeg decode and all output generation with no model and no
network. The ASR forward pass itself is exercised by running the CLI once a model
is provisioned.
