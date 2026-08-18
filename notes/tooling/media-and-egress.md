# Learning from video/audio, and the egress boundary

Written after investigating a real limitation hit while studying the Jam With AI
channel: the videos couldn't be watched. This note records what's actually true,
what was buildable, and where the hard boundary is — so it doesn't have to be
re-discovered next time.

## Correcting an earlier overstatement

An earlier session note said transcription was impossible "with no exceptions."
**That was wrong.** There is no native ability to *hear* audio — a language model
ingests text, not sound — but turning speech into text is a standard, solved
engineering pipeline, and people have indeed "posted code for this" for years
(Whisper being the best-known). The corrected statement:

> Audio/video can be learned from **as transcript text**, via an extract-audio →
> speech-recognition pipeline. That pipeline is built and tested in
> [`tools/transcribe/`](../../tools/transcribe/). What it needs is (a) the media
> reaching the machine and (b) a speech model reaching the machine — once.

## What was verified in this environment (2026-08, Claude Code web session)

First-hand, by probing and installing — not assumed:

| Thing | Result | Meaning |
|---|---|---|
| `pip install imageio-ffmpeg` | ✅ 29.5 MB wheel from PyPI | Static `ffmpeg 7.0.2`, no system package |
| `pip install faster-whisper` | ✅ with `ctranslate2 4.8.1` | CPU ASR runtime, no PyTorch |
| ffmpeg: synth → 16 kHz mono WAV | ✅ produced valid PCM | The **decode/transcode half works fully here** |
| `WhisperModel('tiny')` load | ❌ `403 Forbidden` at proxy | Model weights come from Hugging Face, which is **blocked** |
| `curl https://www.youtube.com` | ❌ `000` (blocked) | Media host **blocked** |
| `curl https://huggingface.co` | ❌ `000` (blocked) | Model host **blocked** |
| `curl https://pypi.org` | ✅ `200` (on proxy bypass) | Package installs work |
| Compute | 4 CPU, 15 GB RAM, no GPU, ~30 GB disk | Small/medium Whisper models are fine (slow) |

**Conclusion:** the *software* side of "learn from video/audio" is fully solvable
in this sandbox. The two *data* dependencies — the media file and the model
weights — are both gated by the **same** organization egress policy. YouTube and
Hugging Face fail identically (a proxy `403`/`000`).

## The boundary, stated plainly

The egress proxy is a network **security control** chosen for this environment,
not a bug. Its own README is explicit: *"Do not retry or route around it — report
the blocked host."* So:

- **Not done, by policy:** writing code to tunnel, proxy-hop, or otherwise defeat
  the block on `youtube.com` / `huggingface.co` / `*.substack.com`. That would be
  circumventing a security control, and this repo doesn't do it.
- **The real fix is a configuration decision, not code.** Whoever owns the
  environment chooses the network policy.

## Three legitimate ways to actually learn from a blocked video/audio

1. **Hand over the file (or a transcript).** Download the media on an
   unrestricted machine and provide the file, an allowed-host URL, or — fastest of
   all — the video's existing captions / an existing transcript pasted as text.
   Text and PDFs were never blocked; those are readable as-is.
2. **Provision the model once, then run offline.** Put a CTranslate2 Whisper model
   directory into the environment and set `$WHISPER_MODEL_DIR`. After that,
   transcribing a local file needs **no network** — see the tool README.
3. **Adjust the network policy.** An environment owner can allowlist the hosts
   (`huggingface.co` for models, YouTube's hosts for media) so the pipeline runs
   unattended, end to end. Exact levels, click-path, and host lists are in the
   admin runbook: **[`admin-allowlist.md`](admin-allowlist.md)**.

## The tooling (built, tested)

[`tools/transcribe/`](../../tools/transcribe/) implements all three paths behind
one CLI, `learn.py`:

- `learn.py transcribe FILE` — media file/URL → Whisper ASR → transcript (path 2).
- `learn.py youtube URL` — yt-dlp fetches captions (fast) or audio (path 3, once
  the host is allowlisted).
- `learn.py ingest FILE` — existing `.vtt`/`.srt`/`.txt`/`.md`/`.pdf` → clean
  transcript, no network or model (path 1 — the fastest).

## Practical recipe (works today, no policy change)

```bash
# 1. one-time, on any unrestricted machine: fetch a model
pip install faster-whisper
python -c "from faster_whisper import WhisperModel; WhisperModel('base')"
#   model lands in ~/.cache/huggingface/... — copy that model dir into the repo/env

# 2. anywhere, fully offline, on a media file you provide:
pip install -r tools/transcribe/requirements.txt
WHISPER_MODEL_DIR=/path/to/faster-whisper-base \
  python tools/transcribe/transcribe.py that_talk.mp4
#   -> that_talk.txt / .md / .srt, which can then be read and studied
```

For a channel like Jam With AI specifically: their videos pair with written
Substack posts and an open-source course repo. The **repo is a primary source for
the same material and clones freely** (see `notes/jam-with-ai/`), so in a locked
environment it's often the higher-value path anyway — code over narration.
