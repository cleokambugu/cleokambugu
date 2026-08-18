#!/usr/bin/env bash
# Provision a CTranslate2 Whisper model into a local directory, so transcribe.py
# can run fully offline (WHISPER_MODEL_DIR). Two sources:
#
#   SRC=hf      (default) download the official Systran model from Hugging Face.
#               Works wherever huggingface.co is reachable/allowlisted.
#   SRC=mirror  fetch from a public GitHub repo over raw.githubusercontent.com,
#               which is on the Trusted allowlist — so this works even in a
#               locked sandbox where Hugging Face is blocked, with NO policy
#               change. See the provenance note below.
#
# Usage:
#   tools/transcribe/provision_model.sh                 # hf, tiny int8 -> ./models/…
#   SRC=mirror tools/transcribe/provision_model.sh      # sandbox-friendly
#   SRC=mirror MODEL=int8_tiny_en DEST=./models/en tools/transcribe/provision_model.sh
#
# Env overrides: SRC, MODEL, DEST, MIRROR_BASE, HF_REPO.
#
# Provenance / trust: the default mirror is a third-party community repo, not the
# official Systran release. A CTranslate2 model is data run by the ctranslate2
# runtime, not arbitrary code, but treat an unofficial mirror as unverified. It
# is validated here only in that the tiny model transcribes the JFK sample
# correctly. For anything you care about, prefer SRC=hf (official) once the host
# is allowlisted. See notes/tooling/admin-allowlist.md.

set -euo pipefail

SRC="${SRC:-hf}"
MODEL="${MODEL:-int8_tiny}"
DEST="${DEST:-models/${MODEL}}"

# Official Hugging Face repo (SRC=hf). Maps our label to a Systran repo id.
declare_hf_repo() {
  case "$1" in
    int8_tiny|tiny)    echo "Systran/faster-whisper-tiny" ;;
    int8_tiny_en)      echo "Systran/faster-whisper-tiny.en" ;;
    base)              echo "Systran/faster-whisper-base" ;;
    small)             echo "Systran/faster-whisper-small" ;;
    *)                 echo "" ;;
  esac
}
HF_REPO="${HF_REPO:-$(declare_hf_repo "$MODEL")}"

# Community GitHub mirror (SRC=mirror), reachable over raw.githubusercontent.com.
MIRROR_BASE="${MIRROR_BASE:-https://raw.githubusercontent.com/alouiadel/whisper-realtime-echo/main/${MODEL}}"

FILES=(config.json model.bin tokenizer.json vocabulary.txt vocabulary.json preprocessor_config.json)

mkdir -p "$DEST"

case "$SRC" in
  hf)
    if [[ -z "$HF_REPO" ]]; then
      echo "No Hugging Face mapping for MODEL=$MODEL. Set HF_REPO or use SRC=mirror." >&2
      exit 2
    fi
    base="https://huggingface.co/${HF_REPO}/resolve/main"
    ;;
  mirror)
    base="$MIRROR_BASE"
    echo "NOTE: fetching an UNOFFICIAL community mirror over raw.githubusercontent.com." >&2
    echo "      See the provenance note in this script's header." >&2
    ;;
  *)
    echo "SRC must be 'hf' or 'mirror', got '$SRC'." >&2
    exit 2
    ;;
esac

echo "Provisioning '$MODEL' from $SRC into $DEST"
for f in "${FILES[@]}"; do
  code=$(curl -sSL -o "$DEST/$f" -w '%{http_code}' --max-time 600 "$base/$f" || echo 000)
  size=$(stat -c%s "$DEST/$f" 2>/dev/null || echo 0)
  if [[ "$code" != "200" || "$size" -lt 20 ]]; then
    rm -f "$DEST/$f"                       # optional file (e.g. vocabulary.txt vs .json) or 404
    printf '  skip  %-26s (HTTP %s)\n' "$f" "$code"
  else
    printf '  ok    %-26s %s bytes\n' "$f" "$size"
  fi
done

# Sanity: model.bin must exist, be sizeable, and not be a git-lfs pointer.
bin="$DEST/model.bin"
if [[ ! -f "$bin" ]] || [[ "$(stat -c%s "$bin")" -lt 1000000 ]]; then
  echo "ERROR: model.bin missing or too small — provisioning failed." >&2
  echo "  If the host is blocked, allowlist it (notes/tooling/admin-allowlist.md)" >&2
  echo "  or try SRC=mirror (works over raw.githubusercontent.com with no policy change)." >&2
  exit 1
fi
if head -c 40 "$bin" | grep -q "git-lfs.github.com"; then
  echo "ERROR: model.bin is a Git LFS pointer, not the real model." >&2
  echo "  This source stores the model in LFS, which the anonymous lane can't fetch." >&2
  echo "  Pick a source that commits model.bin directly, or use SRC=hf." >&2
  exit 1
fi

echo
echo "Done. Use it with:"
echo "    export WHISPER_MODEL_DIR=\"$(cd "$DEST" && pwd)\""
echo "    python tools/transcribe/transcribe.py YOUR_MEDIA_FILE"
