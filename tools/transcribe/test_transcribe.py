#!/usr/bin/env python3
"""Tests for the transcription pipeline that need no ASR model and no network.

These exercise everything except the neural forward pass: real ffmpeg audio
extraction, subtitle/markdown/text generation, timestamp formatting, and URL
detection. The model step is covered separately by actually running the CLI once
a model is provisioned (see README).

Run:
    pip install -r tools/transcribe/requirements.txt
    python tools/transcribe/test_transcribe.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import transcribe  # noqa: E402
import ingest  # noqa: E402
import fetch  # noqa: E402


def _synth_media(path: str, seconds: int = 2) -> None:
    """Make a small real media file with ffmpeg (a sine tone in an AAC container)."""
    cmd = [
        transcribe.ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
        "-c:a", "aac", path,
    ]
    subprocess.run(cmd, check=True)


def test_srt_timestamp() -> None:
    assert transcribe.srt_timestamp(0) == "00:00:00,000"
    assert transcribe.srt_timestamp(1.5) == "00:00:01,500"
    assert transcribe.srt_timestamp(3661.25) == "01:01:01,250"
    print("ok  srt_timestamp")


def test_is_url() -> None:
    assert transcribe.is_url("https://example.com/a.mp3")
    assert transcribe.is_url("http://example.com/a.mp3")
    assert not transcribe.is_url("/home/user/a.mp3")
    assert not transcribe.is_url("a.mp3")
    print("ok  is_url")


def test_extract_audio_real_ffmpeg() -> None:
    """Real decode path: arbitrary media -> 16 kHz mono PCM WAV."""
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "clip.m4a"
        wav = Path(tmp) / "out.wav"
        _synth_media(str(src))
        transcribe.extract_audio(str(src), str(wav))
        assert wav.is_file() and wav.stat().st_size > 1000
        # Confirm ffmpeg produced the exact format Whisper wants.
        probe = subprocess.run(
            [transcribe.ffmpeg_exe(), "-hide_banner", "-i", str(wav)],
            capture_output=True, text=True,
        )
        assert "16000 Hz" in probe.stderr and "mono" in probe.stderr, probe.stderr
    print("ok  extract_audio (real ffmpeg, 16 kHz mono)")


def test_write_outputs() -> None:
    """Subtitle/markdown/text generation from fake ASR segments."""
    segments = [
        SimpleNamespace(start=0.0, end=1.2, text=" Hello there."),
        SimpleNamespace(start=1.2, end=3.4, text=" This is a test transcript."),
    ]
    info = SimpleNamespace(language="en", language_probability=0.99, duration=3.4)
    with tempfile.TemporaryDirectory() as tmp:
        stem = Path(tmp) / "lecture"
        out = transcribe.write_outputs(stem, iter(segments), info, "lecture.mp4")

        txt = out["txt"].read_text()
        assert txt.strip() == "Hello there. This is a test transcript."

        srt = out["srt"].read_text()
        assert "1\n00:00:00,000 --> 00:00:01,200\nHello there." in srt
        assert "2\n00:00:01,200 --> 00:00:03,400\nThis is a test transcript." in srt

        md = out["md"].read_text()
        assert "# Transcript — lecture.mp4" in md
        assert "`en`" in md and "→" in md
    print("ok  write_outputs (.txt/.md/.srt)")


def test_output_names_survive_dotted_stem() -> None:
    """Regression: a stem like 'talk.en' must not have '.en' eaten by with_suffix."""
    info = SimpleNamespace(language="en", language_probability=0.9, duration=1.0)
    seg = [SimpleNamespace(start=0.0, end=1.0, text=" hi")]
    with tempfile.TemporaryDirectory() as tmp:
        stem = Path(tmp) / "talk.en"
        out = transcribe.write_outputs(stem, iter(seg), info, "talk.en.mp4")
        assert out["txt"].name == "talk.en.txt", out["txt"].name
        out2 = ingest.write_outputs(stem, "hi", "talk.en.vtt")
        assert out2["txt"].name == "talk.en.txt", out2["txt"].name
    print("ok  output names survive dotted stem")


def test_parse_srt() -> None:
    srt = (
        "1\n00:00:00,000 --> 00:00:01,200\nHello there.\n\n"
        "2\n00:00:01,200 --> 00:00:03,400\nThis is a test.\n"
    )
    assert ingest.parse_srt(srt) == ["Hello there.", "This is a test."]
    print("ok  parse_srt")


def test_parse_vtt_and_dedupe_rolling() -> None:
    # Auto-caption style: each cue repeats the tail and adds new words, with tags.
    vtt = (
        "WEBVTT\n\n"
        "00:00:01.000 --> 00:00:03.000\n<c>hello and welcome</c>\n\n"
        "00:00:03.000 --> 00:00:05.000\nhello and welcome to the\n\n"
        "00:00:05.000 --> 00:00:07.000\nwelcome to the talk\n"
    )
    cues = ingest.parse_vtt(vtt)
    assert cues == ["hello and welcome", "hello and welcome to the", "welcome to the talk"]
    assert ingest.dedupe_rolling(cues) == "hello and welcome to the talk"
    # Header/NOTE blocks are ignored and tags stripped.
    assert "WEBVTT" not in " ".join(cues)
    print("ok  parse_vtt + dedupe_rolling")


def test_subtitle_to_text() -> None:
    assert ingest.subtitle_to_text("1\n00:00:00,000 --> 00:00:01,000\nA b c\n", "srt") == "A b c"
    print("ok  subtitle_to_text")


def _mini_pdf(message: str = "Hello PDF") -> bytes:
    """Assemble a valid single-page PDF with a correct xref table."""
    content = f"BT /F1 24 Tf 20 100 Td ({message}) Tj ET\n".encode()
    bodies = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]"
        b"/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>",
        b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>",
        b"<</Length %d>>\nstream\n%sendstream" % (len(content), content),
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for n, body in enumerate(bodies, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % n + body + b"\nendobj\n"
    xref_pos = len(out)
    out += b"xref\n0 %d\n" % (len(bodies) + 1)
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<</Root 1 0 R/Size %d>>\nstartxref\n%d\n%%%%EOF\n" % (len(bodies) + 1, xref_pos)
    return bytes(out)


def test_pdf_to_text_real() -> None:
    """Extract text from a real single-page PDF via pypdf."""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "mini.pdf"
        p.write_bytes(_mini_pdf("Hello PDF"))
        text = ingest.pdf_to_text(str(p))
        assert "Hello PDF" in text, repr(text)
    print("ok  pdf_to_text (real pypdf extraction)")


def test_build_ydl_opts() -> None:
    subs = fetch.build_ydl_opts("/out", mode="subs", sub_langs="en.*,es")
    assert subs["skip_download"] is True
    assert subs["writesubtitles"] and subs["writeautomaticsub"]
    assert subs["subtitleslangs"] == ["en.*", "es"]
    assert "format" not in subs

    audio = fetch.build_ydl_opts("/out", mode="audio", max_items=5)
    assert audio.get("skip_download") is not True
    assert audio["format"] == "bestaudio/best"
    assert audio["playlistend"] == 5
    assert any(pp["key"] == "FFmpegExtractAudio" for pp in audio["postprocessors"])

    try:
        fetch.build_ydl_opts("/out", mode="bogus")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for bad mode")
    print("ok  build_ydl_opts")


if __name__ == "__main__":
    test_srt_timestamp()
    test_is_url()
    test_extract_audio_real_ffmpeg()
    test_write_outputs()
    test_output_names_survive_dotted_stem()
    test_parse_srt()
    test_parse_vtt_and_dedupe_rolling()
    test_subtitle_to_text()
    test_pdf_to_text_real()
    test_build_ydl_opts()
    print("\nAll pipeline tests passed (ASR forward pass excluded — see README).")
