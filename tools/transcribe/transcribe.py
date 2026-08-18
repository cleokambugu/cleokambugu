#!/usr/bin/env python3
"""Turn a video/audio file into a readable transcript.

The pipeline is the standard, well-worn one:

    media file  ->  ffmpeg (extract 16 kHz mono audio)  ->  Whisper ASR  ->  text

It is deliberately dependency-light: the only two Python packages are
``imageio-ffmpeg`` (ships a static ffmpeg binary, so there is no system ffmpeg to
install) and ``faster-whisper`` (CTranslate2 Whisper — runs on CPU, no PyTorch).
Both install cleanly from PyPI.

Once a model is present locally, this runs FULLY OFFLINE on a local file: no
network at all. That property is the whole point in a locked-down environment.

Usage
-----
    python transcribe.py LECTURE.mp4
    python transcribe.py talk.m4a --model small --language en
    python transcribe.py foreign_talk.mp4 --task translate      # -> English
    python transcribe.py https://allowed.host/clip.mp3          # direct media URL
    WHISPER_MODEL_DIR=./models/faster-whisper-base python transcribe.py x.wav

Outputs, next to the input (or under --out-dir): ``NAME.txt`` (plain text),
``NAME.md`` (timestamps + metadata), and ``NAME.srt`` (subtitles).

Model provisioning
------------------
faster-whisper auto-downloads its model from Hugging Face on first use. Where
Hugging Face is reachable that just works. Where it is blocked (some sandboxes,
this repo's web-session environment included), you must supply the model from an
allowed source instead — point ``--model`` or ``$WHISPER_MODEL_DIR`` at a local
CTranslate2 model directory. See tools/transcribe/README.md for the three ways to
get one. This script never tries to defeat a network policy; if the model cannot
be reached it fails with an actionable message.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

AUDIO_SAMPLE_RATE = 16_000  # what Whisper expects


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def ffmpeg_exe() -> str:
    """Locate the static ffmpeg binary bundled by imageio-ffmpeg."""
    try:
        import imageio_ffmpeg
    except ImportError as exc:  # pragma: no cover - guidance path
        raise SystemExit(
            "Missing dependency 'imageio-ffmpeg'. Install with:\n"
            "    pip install -r tools/transcribe/requirements.txt"
        ) from exc
    return imageio_ffmpeg.get_ffmpeg_exe()


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https")


def fetch_url(url: str, dest_dir: str) -> str:
    """Download a direct media URL to a local file.

    This handles direct links to a media file on an *allowed* host. It is not a
    site scraper: it will not extract media from YouTube or other streaming
    pages, and it does not attempt to bypass a blocked host — a blocked URL
    surfaces the proxy's own error verbatim.
    """
    name = os.path.basename(urlparse(url).path) or "download.bin"
    dest = os.path.join(dest_dir, name)
    eprint(f"Downloading {url}")
    try:
        req = Request(url, headers={"User-Agent": "transcribe.py"})
        with urlopen(req) as resp, open(dest, "wb") as fh:  # noqa: S310 (trusted CLI input)
            while chunk := resp.read(1 << 20):
                fh.write(chunk)
    except Exception as exc:  # noqa: BLE001 - report and stop
        raise SystemExit(
            f"Could not download {url}\n"
            f"  reason: {exc}\n"
            "  If this host is blocked by a network policy, that is not something\n"
            "  this tool works around. Download the file elsewhere and pass the\n"
            "  local path instead, or ask an admin to allowlist the host."
        ) from exc
    return dest


def extract_audio(media_path: str, wav_path: str) -> None:
    """Decode any audio/video file to 16 kHz mono PCM WAV via ffmpeg."""
    cmd = [
        ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y",
        "-i", media_path,
        "-vn",                       # drop any video stream
        "-ac", "1",                  # mono
        "-ar", str(AUDIO_SAMPLE_RATE),
        "-c:a", "pcm_s16le",
        wav_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(
            f"ffmpeg failed to read '{media_path}'.\n{proc.stderr.strip()}\n"
            "  Is the file a valid audio/video file?"
        )


def load_model(model: str, compute_type: str):
    """Load a faster-whisper model by name or local directory.

    A local directory (or $WHISPER_MODEL_DIR) is used as-is with no network. A
    bare name (e.g. 'base') triggers faster-whisper's Hugging Face download,
    which only succeeds where that host is reachable.
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:  # pragma: no cover - guidance path
        raise SystemExit(
            "Missing dependency 'faster-whisper'. Install with:\n"
            "    pip install -r tools/transcribe/requirements.txt"
        ) from exc

    model_dir = os.environ.get("WHISPER_MODEL_DIR")
    source = model_dir or model
    local = Path(source).is_dir()
    eprint(f"Loading model: {source}  ({'local dir' if local else 'name'}, compute_type={compute_type})")
    try:
        return WhisperModel(source, device="cpu", compute_type=compute_type)
    except Exception as exc:  # noqa: BLE001 - the important, honest failure path
        hint = ""
        if not local:
            hint = (
                "\n  The model was requested by name, so faster-whisper tried to\n"
                "  download it from Hugging Face. If that host is blocked here you\n"
                "  will see a 403/Proxy error above. Supply a local model instead:\n"
                "      WHISPER_MODEL_DIR=/path/to/faster-whisper-base python transcribe.py ...\n"
                "  See tools/transcribe/README.md for how to obtain one."
            )
        raise SystemExit(f"Could not load Whisper model '{source}'.\n  reason: {exc}{hint}") from exc


def srt_timestamp(seconds: float) -> str:
    td = timedelta(seconds=seconds)
    total_ms = int(td.total_seconds() * 1000)
    h, rem = divmod(total_ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_outputs(stem: Path, segments, info, source_name: str) -> dict[str, Path]:
    """Write .txt, .md and .srt. Consumes the segment generator once."""
    txt_path = stem.with_suffix(".txt")
    md_path = stem.with_suffix(".md")
    srt_path = stem.with_suffix(".srt")

    plain_lines: list[str] = []
    md_lines = [
        f"# Transcript — {source_name}",
        "",
        f"- Detected language: `{info.language}` (p={info.language_probability:.2f})",
        f"- Duration: {timedelta(seconds=int(info.duration))}",
        "",
        "> Machine transcription (Whisper). Treat as a draft — verify quotes against the audio.",
        "",
    ]

    with open(srt_path, "w", encoding="utf-8") as srt:
        for i, seg in enumerate(segments, start=1):
            text = seg.text.strip()
            plain_lines.append(text)
            start, end = srt_timestamp(seg.start), srt_timestamp(seg.end)
            md_lines.append(f"**[{start[:-4]} → {end[:-4]}]** {text}")
            srt.write(f"{i}\n{start} --> {end}\n{text}\n\n")

    txt_path.write_text(" ".join(plain_lines).strip() + "\n", encoding="utf-8")
    md_path.write_text("\n".join(md_lines).strip() + "\n", encoding="utf-8")
    return {"txt": txt_path, "md": md_path, "srt": srt_path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Transcribe a local (or allowed-URL) audio/video file to text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", help="Path to an audio/video file, or a direct media URL.")
    parser.add_argument("--model", default="base",
                        help="Model name (tiny/base/small/medium/large-v3) or a local model dir. "
                             "Default: base. Overridden by $WHISPER_MODEL_DIR.")
    parser.add_argument("--language", default=None, help="Force language code (e.g. en). Default: auto-detect.")
    parser.add_argument("--task", choices=["transcribe", "translate"], default="transcribe",
                        help="'translate' outputs English regardless of source language.")
    parser.add_argument("--compute-type", default="int8",
                        help="CTranslate2 compute type (int8 is best for CPU). Default: int8.")
    parser.add_argument("--out-dir", default=None, help="Directory for outputs. Default: alongside input.")
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory() as tmp:
        # Resolve input to a local media file.
        if is_url(args.input):
            media_path = fetch_url(args.input, tmp)
            base_name = Path(urlparse(args.input).path).name or "transcript"
        else:
            media_path = args.input
            if not os.path.isfile(media_path):
                eprint(f"Input file not found: {media_path}")
                return 2
            base_name = os.path.basename(media_path)

        # Decode -> 16 kHz mono wav.
        wav_path = os.path.join(tmp, "audio16k.wav")
        extract_audio(media_path, wav_path)

        # Transcribe.
        model = load_model(args.model, args.compute_type)
        eprint("Transcribing… (CPU; larger models are slower)")
        segments, info = model.transcribe(
            wav_path, language=args.language, task=args.task, vad_filter=True,
        )

        out_dir = Path(args.out_dir) if args.out_dir else Path(media_path).resolve().parent
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = out_dir / Path(base_name).stem
        outputs = write_outputs(stem, segments, info, base_name)

    print("Wrote:")
    for kind, path in outputs.items():
        print(f"  {kind}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
