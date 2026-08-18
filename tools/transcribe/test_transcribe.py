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


if __name__ == "__main__":
    test_srt_timestamp()
    test_is_url()
    test_extract_audio_real_ffmpeg()
    test_write_outputs()
    print("\nAll pipeline tests passed (model step excluded — see README).")
