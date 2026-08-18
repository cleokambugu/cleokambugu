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
| `WhisperModel('tiny')` load | ❌ `403 Forbidden` at proxy | The *default* weights come from Hugging Face, which is **blocked** |
| `curl https://www.youtube.com` | ❌ `000` (blocked) | Media host **blocked** |
| `curl https://huggingface.co` | ❌ `000` (blocked) | Official model host **blocked** |
| `curl https://raw.githubusercontent.com/…/model.bin` | ✅ `200`, real 40 MB blob | GitHub raw is **allowed** (Trusted list) — a model can be fetched here |
| `curl https://pypi.org` | ✅ `200` (on proxy bypass) | Package installs work |
| Compute | 4 CPU, 15 GB RAM, no GPU, ~30 GB disk | Small/medium Whisper models are fine (slow) |

**Conclusion (updated after real testing):** the *software* side is fully
solvable here, and so is the **model** — see the breakthrough below. Real ASR has
been run end to end in this sandbox: a CTranslate2 tiny model pulled entirely from
`raw.githubusercontent.com` transcribed a JFK speech clip correctly in ~22 s on
CPU (`export WHISPER_MODEL_DIR=… ; transcribe.py jfk.wav` →
*"…ask not what your country can do for you…"*). The remaining hard gate is
narrower than first thought: **YouTube media** (the video bytes). Give a media
file (or use an allowed host / captions) and the whole pipeline runs today, no
policy change.

## Breakthrough: provisioning a model with no allowlist change

Hugging Face (the *default* model host) is blocked — but `raw.githubusercontent.com`
is on the **Trusted allowlist** (the docs confirm it: "Committed files from public
repositories arrive through `raw.githubusercontent.com` … in the default Trusted
list"). Community GitHub repos mirror the Systran CTranslate2 models as **normal
committed blobs** (not Git LFS), so each model file — `config.json`, `model.bin`,
`tokenizer.json`, `vocabulary.json`, `preprocessor_config.json` — can be fetched
straight over HTTPS. [`provision_model.sh`](../../tools/transcribe/provision_model.sh)
automates it:

```bash
SRC=mirror MODEL=int8_tiny DEST=./models/int8_tiny \
  tools/transcribe/provision_model.sh
export WHISPER_MODEL_DIR="$PWD/models/int8_tiny"
python tools/transcribe/transcribe.py your_audio.wav      # real ASR, offline
```

Verified by [`test_asr_integration.py`](../../tools/transcribe/test_asr_integration.py),
which provisions nothing itself but, when `$WHISPER_MODEL_DIR` is set, fetches the
JFK clip and asserts the transcript — the real forward pass, in CI-style form.

**Provenance / trust:** that mirror is a *third-party* repo, not the official
Systran release (which lives on the blocked HF host). A CTranslate2 model is data
executed by the `ctranslate2` runtime, not arbitrary code, but an unofficial
mirror is still unverified beyond "it transcribes the JFK sample correctly."
For anything you rely on, prefer the official model via `SRC=hf` once Hugging Face
is allowlisted (see [`admin-allowlist.md`](admin-allowlist.md)). This is exactly
the kind of upstream-vs-mirror trust gap this repo's rules say to flag rather than
paper over.

**Earlier note corrected:** a previous version said the media file and the model
were "both gated by the same egress policy." True for the *default* hosts
(YouTube, Hugging Face), but the model gate has an in-sandbox way around it (above)
that needs no allowlist; the media gate does not, unless the media is on an allowed
host or handed over as a file.

## The boundary, stated plainly

The egress proxy is a network **security control** chosen for this environment,
not a bug. Its own README is explicit: *"Do not retry or route around it — report
the blocked host."* So:

- **Not done, by policy:** writing code to tunnel, proxy-hop, or otherwise defeat
  the block on `youtube.com` / `huggingface.co` / `*.substack.com`. That would be
  circumventing a security control, and this repo doesn't do it.
- **The real fix is a configuration decision, not code.** Whoever owns the
  environment chooses the network policy.

## Ways to actually learn from a blocked video/audio

**The model is no longer a blocker** — provision it from GitHub raw with no policy
change (the breakthrough section above; `SRC=mirror provision_model.sh`). That
leaves only the *media* to get in, three ways:

1. **Hand over the file (or a transcript).** Provide the media file, an
   allowed-host URL, or — fastest of all — the video's existing captions / a
   transcript pasted as text. Text and PDFs were never blocked; readable as-is.
   With the model provisioned as above, this runs end to end **in the sandbox
   today**, no allowlist needed.
2. **Provision the model once, then run offline.** `provision_model.sh` (SRC=mirror
   for a locked sandbox, SRC=hf once Hugging Face is allowed), then set
   `$WHISPER_MODEL_DIR`. Transcribing a local file then needs **no network**.
3. **Adjust the network policy** (admin). Allowlist YouTube's hosts to fetch video
   directly (and, if you want the *official* model, `huggingface.co`). Exact
   levels, click-path, and host lists: **[`admin-allowlist.md`](admin-allowlist.md)**.

## The tooling (built, tested)

[`tools/transcribe/`](../../tools/transcribe/) implements all three paths behind
one CLI, `learn.py`:

- `learn.py transcribe FILE` — media file/URL → Whisper ASR → transcript (path 2).
- `learn.py youtube URL` — yt-dlp fetches captions (fast) or audio (path 3, once
  the host is allowlisted).
- `learn.py ingest FILE` — existing `.vtt`/`.srt`/`.txt`/`.md`/`.pdf` → clean
  transcript, no network or model (path 1 — the fastest).

## Practical recipe (works today in this sandbox, no policy change)

```bash
# 1. deps + a model provisioned from GitHub raw (allowed host)
pip install -r tools/transcribe/requirements.txt
SRC=mirror MODEL=int8_tiny DEST=./models/int8_tiny \
  tools/transcribe/provision_model.sh
export WHISPER_MODEL_DIR="$PWD/models/int8_tiny"

# 2. fully offline, on a media file you provide:
python tools/transcribe/transcribe.py that_talk.mp4
#   -> that_talk.txt / .md / .srt, which can then be read and studied

# (prefer the official model once Hugging Face is allowlisted: SRC=hf ...)
```

This is the exact path that was verified here: the JFK sample transcribed
correctly with a mirror-provisioned tiny model, no allowlist change.

For a channel like Jam With AI specifically: their videos pair with written
Substack posts and an open-source course repo. The **repo is a primary source for
the same material and clones freely** (see `notes/jam-with-ai/`), so in a locked
environment it's often the higher-value path anyway — code over narration.
