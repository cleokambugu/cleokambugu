#!/usr/bin/env python3
"""Real end-to-end ASR test — proves the forward pass, not just the plumbing.

Unlike test_transcribe.py (which needs no model or network), this runs the actual
Whisper pipeline on real speech. It is opt-in because it needs a provisioned
model; it SKIPS cleanly when one isn't available, so it never breaks a plain
`python test_transcribe.py` run.

What it does:
  1. Requires a CTranslate2 model dir in $WHISPER_MODEL_DIR (else SKIP).
     Provision one with:  tools/transcribe/provision_model.sh   (see README)
  2. Downloads a small public-domain speech clip (JFK) from raw.githubusercontent.com,
     which is on the Trusted allowlist (else SKIP if unreachable).
  3. Runs transcribe.py on it and asserts the known words come back.

Run:
    export WHISPER_MODEL_DIR=./models/int8_tiny
    python tools/transcribe/test_asr_integration.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import transcribe  # noqa: E402

JFK_URL = "https://raw.githubusercontent.com/ggerganov/whisper.cpp/master/samples/jfk.wav"
EXPECTED = "ask not what your country"


def _skip(reason: str) -> int:
    print(f"SKIP  real-ASR integration test — {reason}")
    return 0


def main() -> int:
    model_dir = os.environ.get("WHISPER_MODEL_DIR")
    if not model_dir or not Path(model_dir).is_dir():
        return _skip("set $WHISPER_MODEL_DIR to a CTranslate2 model dir "
                     "(see tools/transcribe/provision_model.sh)")

    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "jfk.wav"
        try:
            with urlopen(JFK_URL, timeout=60) as resp:  # noqa: S310 (trusted, pinned URL)
                wav.write_bytes(resp.read())
        except Exception as exc:  # noqa: BLE001
            return _skip(f"could not fetch speech sample ({exc})")

        rc = transcribe.main([str(wav), "--language", "en", "--out-dir", tmp])
        assert rc == 0, f"transcribe.main returned {rc}"

        text = (Path(tmp) / "jfk.txt").read_text().lower()
        assert EXPECTED in text, f"expected {EXPECTED!r} in transcript, got: {text!r}"

    print("ok    real ASR — JFK sample transcribed correctly")
    print("\nReal-ASR integration test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
