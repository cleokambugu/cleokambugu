#!/usr/bin/env python3
"""One front door for learning from video/audio/notes.

Three subcommands, three ways to get to readable text:

    # 1. You have a media FILE (or a direct media URL) -> speech recognition
    python learn.py transcribe lecture.mp4

    # 2. A media host is allowlisted -> fetch captions (fast) or audio
    python learn.py youtube "https://www.youtube.com/watch?v=VIDEO_ID"

    # 3. You already have captions / a transcript / a PDF -> clean it up
    python learn.py ingest captions.en.vtt

Each subcommand is also runnable as its own script (transcribe.py, fetch.py,
ingest.py); this is just a convenience wrapper. See README.md for the full story,
and notes/tooling/admin-allowlist.md for turning on host #2 as the admin.
"""

from __future__ import annotations

import sys

USAGE = __doc__


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0 if argv else 2

    command, rest = argv[0], argv[1:]
    if command == "transcribe":
        import transcribe
        return transcribe.main(rest)
    if command in ("youtube", "fetch"):
        import fetch
        return fetch.main(rest)
    if command == "ingest":
        import ingest
        return ingest.main(rest)

    print(f"Unknown command: {command!r}\n", file=sys.stderr)
    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    raise SystemExit(main())
