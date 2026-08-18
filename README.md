# cleokambugu

Notes and things I'm learning.

> ℹ️ This file renders on the public GitHub profile page at
> [github.com/cleokambugu](https://github.com/cleokambugu). Worth rewording to taste before
> merging — the placeholder above is deliberately minimal rather than a guess at how you'd
> introduce yourself.

## Notes

- **[Jam With AI](notes/jam-with-ai/)** — production RAG and agentic system design, distilled
  from the [Jam With AI](https://www.youtube.com/@jam-with-ai) project's open-source course.
  - [Curriculum map](notes/jam-with-ai/curriculum.md) — the Mother of AI project's six phases
    and its seven-week RAG syllabus
  - [Production RAG playbook](notes/jam-with-ai/production-rag-playbook.md) — fourteen
    engineering patterns pulled from the course source, from hybrid retrieval and chunking
    strategy through agent guardrails, tracing, and cache key design
- **[Tooling](notes/tooling/)** — environment notes.
  - [Learning from video/audio, and the egress boundary](notes/tooling/media-and-egress.md)
  - [Admin runbook: allowlist media & model hosts](notes/tooling/admin-allowlist.md)

## Tools

- **[transcribe](tools/transcribe/)** — learn from video/audio/notes as text, via one CLI
  (`learn.py`) with three routes: **transcribe** a media file (ffmpeg + Whisper, CPU-only,
  offline once a model is present), **youtube** to fetch captions/audio with yt-dlp once a
  host is allowlisted, or **ingest** existing captions/transcripts/PDFs with no network at
  all. `provision_model.sh` pulls a model from GitHub raw so real ASR runs even in a locked
  sandbox with no policy change. Tested — including a real end-to-end ASR run.
