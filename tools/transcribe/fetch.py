#!/usr/bin/env python3
"""Fetch a video's captions (fast) or audio (for ASR) with yt-dlp.

This is the "an admin allowlisted the media host" path. It does two things,
preferring the cheap one:

1. **Subtitles / captions** — if the video has subtitles or auto-captions,
   download just those (no video, no audio, no ASR). This is by far the fastest
   way to "learn from a video": you get the text directly.
2. **Audio** — if there are no usable captions, download bestaudio so
   ``transcribe.py`` can run speech recognition over it.

It supports a single video, or a playlist/channel URL with ``--max`` to cap how
many items are taken.

Requires ``yt-dlp`` (pip). Uses the static ffmpeg from ``imageio-ffmpeg`` so
there is no system ffmpeg dependency. If the media host is blocked by the
environment's network policy, yt-dlp surfaces that error unchanged — this tool
does not try to get around it (see notes/tooling/admin-allowlist.md).

Usage
-----
    python fetch.py "https://www.youtube.com/watch?v=VIDEO_ID"
    python fetch.py URL --mode subs --sub-langs en          # captions only
    python fetch.py URL --mode audio --out-dir ./downloads  # audio for ASR
    python fetch.py "PLAYLIST_OR_CHANNEL_URL" --max 5
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def ffmpeg_location() -> str | None:
    """Directory holding the bundled ffmpeg, for yt-dlp's --ffmpeg-location."""
    try:
        import imageio_ffmpeg
        return str(Path(imageio_ffmpeg.get_ffmpeg_exe()).parent)
    except Exception:  # noqa: BLE001 - yt-dlp still works without it for many formats
        return None


def build_ydl_opts(
    out_dir: str,
    mode: str = "auto",
    sub_langs: str = "en.*",
    max_items: int | None = None,
    ffmpeg_dir: str | None = None,
) -> dict:
    """Build the yt-dlp options dict. Pure function so it can be unit-tested.

    :param mode: 'subs' (captions only), 'audio' (bestaudio), or 'auto'
        (captions if present, else audio).
    :param sub_langs: comma/space list of subtitle language globs, e.g. 'en.*'.
    """
    if mode not in ("subs", "audio", "auto"):
        raise ValueError(f"mode must be subs|audio|auto, got {mode!r}")

    langs = [s for s in sub_langs.replace(",", " ").split() if s]
    want_subs = mode in ("subs", "auto")
    want_audio = mode in ("audio", "auto")

    opts: dict = {
        "outtmpl": {"default": os.path.join(out_dir, "%(title).200B [%(id)s].%(ext)s")},
        "restrictfilenames": True,
        "ignoreerrors": True,
        "noprogress": True,
        "quiet": True,
        "writesubtitles": want_subs,
        "writeautomaticsub": want_subs,
        "subtitleslangs": langs if want_subs else [],
        "subtitlesformat": "vtt",
    }

    # Captions-only means we never fetch the media stream at all.
    if mode == "subs":
        opts["skip_download"] = True
    else:
        opts["format"] = "bestaudio/best" if want_audio else "best"
        opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "0"}
        ]

    if max_items is not None:
        opts["playlistend"] = int(max_items)
    if ffmpeg_dir:
        opts["ffmpeg_location"] = ffmpeg_dir

    return opts


def fetch(url: str, out_dir: str, mode: str = "auto", sub_langs: str = "en.*",
          max_items: int | None = None) -> list[str]:
    """Run yt-dlp for ``url`` and return the files it produced under ``out_dir``."""
    try:
        import yt_dlp
    except ImportError as exc:  # pragma: no cover - guidance path
        raise SystemExit(
            "Missing dependency 'yt-dlp'. Install with:\n"
            "    pip install -r tools/transcribe/requirements.txt"
        ) from exc

    os.makedirs(out_dir, exist_ok=True)
    before = set(os.listdir(out_dir))
    opts = build_ydl_opts(out_dir, mode, sub_langs, max_items, ffmpeg_location())

    eprint(f"Fetching ({mode}): {url}")
    with yt_dlp.YoutubeDL(opts) as ydl:
        code = ydl.download([url])
    if code != 0:
        eprint(
            "yt-dlp reported errors. If the host is blocked by this environment's\n"
            "network policy, allowlist it (see notes/tooling/admin-allowlist.md);\n"
            "this tool does not bypass a blocked host."
        )

    produced = sorted(set(os.listdir(out_dir)) - before)
    return [os.path.join(out_dir, name) for name in produced]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch captions (fast) or audio from a video URL with yt-dlp.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("url", help="A video, playlist, or channel URL.")
    parser.add_argument("--mode", choices=["auto", "subs", "audio"], default="auto",
                        help="subs=captions only (fastest), audio=for ASR, auto=subs else audio.")
    parser.add_argument("--sub-langs", default="en.*",
                        help="Subtitle language globs (e.g. 'en.*' or 'en,es'). Default: en.*")
    parser.add_argument("--max", type=int, default=None,
                        help="For playlists/channels: max items to take.")
    parser.add_argument("--out-dir", default="downloads", help="Where to save files.")
    args = parser.parse_args(argv)

    files = fetch(args.url, args.out_dir, args.mode, args.sub_langs, args.max)
    if not files:
        eprint("No files produced.")
        return 1

    subs = [f for f in files if f.endswith((".vtt", ".srt"))]
    print("Fetched:")
    for f in files:
        print(f"  {f}")
    if subs:
        print("\nNext: turn captions into a clean transcript:")
        print(f"    python tools/transcribe/ingest.py \"{subs[0]}\"")
    else:
        print("\nNext: transcribe the audio:")
        print(f"    python tools/transcribe/transcribe.py \"{files[0]}\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
