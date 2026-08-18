#!/usr/bin/env python3
"""Ingest material you already have into a clean, readable transcript.

This is the "hand me the material" path — the fastest of all, because it needs
no download, no model, and no network. Give it whatever you've got:

- **Subtitles / captions** (``.vtt``, ``.srt``) — e.g. YouTube's own captions, or
  the output of ``fetch.py``. Rolling auto-caption repetition is collapsed.
- **A transcript or notes** (``.txt``, ``.md``) — normalized and copied through.
- **A PDF** (``.pdf``) — text extracted with pypdf.

Output is a clean ``NAME.txt`` (plain text) and ``NAME.md`` (with a source
header), ready to read and study.

Usage
-----
    python ingest.py captions.en.vtt
    python ingest.py lecture.srt --out-dir notes/transcripts
    python ingest.py paper.pdf
    python ingest.py pasted_transcript.txt
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Inline caption tags like <00:00:01.000> and <c> / </c> used in YouTube VTT.
_TAG_RE = re.compile(r"<[^>]+>")
_TIMESTAMP_LINE_RE = re.compile(r"-->")


def strip_tags(text: str) -> str:
    return _TAG_RE.sub("", text)


def parse_srt(text: str) -> list[str]:
    """Return the text of each SRT cue, in order (indices/timestamps removed)."""
    cues: list[str] = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        # Drop a leading numeric index and the timestamp line.
        if lines and lines[0].strip().isdigit():
            lines = lines[1:]
        lines = [ln for ln in lines if not _TIMESTAMP_LINE_RE.search(ln)]
        cue = strip_tags(" ".join(lines)).strip()
        if cue:
            cues.append(cue)
    return cues


def parse_vtt(text: str) -> list[str]:
    """Return the text of each WebVTT cue, in order."""
    cues: list[str] = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.splitlines()
        # Skip header/metadata blocks.
        if lines and lines[0].strip().upper().startswith(("WEBVTT", "NOTE", "STYLE", "REGION")):
            continue
        text_lines: list[str] = []
        for ln in lines:
            if _TIMESTAMP_LINE_RE.search(ln):  # cue timing line (with optional settings)
                continue
            if ln.strip().isdigit():           # optional numeric cue identifier
                continue
            text_lines.append(ln)
        cue = strip_tags(" ".join(text_lines)).strip()
        if cue:
            cues.append(cue)
    return cues


def dedupe_rolling(cues: list[str]) -> str:
    """Collapse rolling/overlapping caption cues into flowing text.

    Auto-captions repeat the previous partial line plus new words on each cue.
    For every cue, strip the longest prefix that already matches the tail of what
    we've kept, then append only the genuinely new words. Exact duplicate cues
    contribute nothing.
    """
    out: list[str] = []
    for cue in cues:
        words = cue.split()
        if not words:
            continue
        max_ov = min(len(out), len(words))
        overlap = 0
        for k in range(max_ov, 0, -1):
            if out[-k:] == words[:k]:
                overlap = k
                break
        out.extend(words[overlap:])
    return " ".join(out)


def subtitle_to_text(text: str, fmt: str) -> str:
    cues = parse_vtt(text) if fmt == "vtt" else parse_srt(text)
    return dedupe_rolling(cues)


def pdf_to_text(path: str) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - guidance path
        raise SystemExit(
            "Missing dependency 'pypdf'. Install with:\n"
            "    pip install -r tools/transcribe/requirements.txt"
        ) from exc
    reader = PdfReader(path)
    parts = [(page.extract_text() or "").strip() for page in reader.pages]
    return "\n\n".join(p for p in parts if p)


def normalize_plaintext(text: str) -> str:
    """Tidy whitespace in an already-textual transcript without losing paragraphs."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def ingest_text(path: str) -> str:
    """Turn any supported file into clean transcript text."""
    suffix = Path(path).suffix.lower()
    if suffix == ".vtt":
        return subtitle_to_text(Path(path).read_text(encoding="utf-8", errors="replace"), "vtt")
    if suffix == ".srt":
        return subtitle_to_text(Path(path).read_text(encoding="utf-8", errors="replace"), "srt")
    if suffix == ".pdf":
        return normalize_plaintext(pdf_to_text(path))
    if suffix in (".txt", ".md", ""):
        return normalize_plaintext(Path(path).read_text(encoding="utf-8", errors="replace"))
    raise SystemExit(f"Unsupported file type: {suffix or '(none)'} — use .vtt/.srt/.txt/.md/.pdf")


def write_outputs(stem: Path, body: str, source_name: str) -> dict[str, Path]:
    # Append rather than with_suffix(), which would eat a dotted stem like "talk.en".
    txt_path = Path(f"{stem}.txt")
    md_path = Path(f"{stem}.md")
    txt_path.write_text(body.strip() + "\n", encoding="utf-8")
    md = (
        f"# Transcript — {source_name}\n\n"
        f"> Ingested from `{source_name}`. Verify quotes against the original.\n\n"
        f"{body.strip()}\n"
    )
    md_path.write_text(md, encoding="utf-8")
    return {"txt": txt_path, "md": md_path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Turn existing captions/transcript/PDF into a clean transcript.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", help="A .vtt/.srt/.txt/.md/.pdf file.")
    parser.add_argument("--out-dir", default=None, help="Output directory. Default: alongside input.")
    args = parser.parse_args(argv)

    if not Path(args.input).is_file():
        print(f"Input file not found: {args.input}", file=sys.stderr)
        return 2

    body = ingest_text(args.input)
    if not body:
        print("No text extracted (empty or image-only source).", file=sys.stderr)
        return 1

    out_dir = Path(args.out_dir) if args.out_dir else Path(args.input).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = out_dir / Path(args.input).stem
    outputs = write_outputs(stem, body, Path(args.input).name)

    print("Wrote:")
    for kind, path in outputs.items():
        print(f"  {kind}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
