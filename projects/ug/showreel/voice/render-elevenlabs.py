#!/usr/bin/env python3
"""Render the UG showreel narration (lines.v2.json) with the ElevenLabs text-to-speech API.

Usage (run where api.elevenlabs.io is reachable; the build sandbox cannot reach it):

  export ELEVENLABS_API_KEY=...            # https://elevenlabs.io/app/settings/api-keys
  export ELEVENLABS_VOICE_ID=...           # the cast voice (or pass --voice)
  python render-elevenlabs.py --dry-run    # print every line, its settings and the time budget
  python render-elevenlabs.py --list-voices          # GET /v1/voices: name, labels, accent
  python render-elevenlabs.py --search-library "Ugandan"   # GET /v1/shared-voices
  python render-elevenlabs.py              # write <scene>-<n>.mp3 and manifest.json here
  python render-elevenlabs.py --cut short  # only the scenes of the short cut

Requires: requests. Optional: mutagen (exact durations; otherwise estimated from words).

Provenance of the HTTP contract used here (the build sandbox cannot reach the API, so nothing
below has been exercised against a live key):

First-hand, read in ElevenLabs' own skills repo (github.com/elevenlabs/skills, commit 44a05ea,
text-to-speech/SKILL.md and text-to-speech/references/voice-settings.md):
  - model ids eleven_v3 (70+ languages), eleven_multilingual_v2 (29), eleven_flash_v2_5.
  - voice_settings fields and ranges: stability 0.0-1.0 (default 0.5), similarity_boost 0.0-1.0
    (0.75), style 0.0-1.0 (0.0, v2+ and v3), speed 0.25-4.0 (1.0, REST), use_speaker_boost bool.
    The repo's own v3 example sends all of them with model_id eleven_v3.
  - language_code (ISO 639-1) works with eleven_v3; unsupported codes are ignored; not supported
    on eleven_multilingual_v2.
  - previous_text / next_text (request stitching) smooth tone across consecutive requests.
  - apply_text_normalization "auto" | "on" | "off".
  - output formats: mp3_44100_128 (default), mp3_44100_192 (Creator+), mp3_22050_32,
    pcm_16000/22050/24000, pcm_44100 (Pro+), wav_44100, opus_48000_64, ulaw_8000.
  - errors: 401 bad key, 422 bad parameters (voice_id, model_id), 429 rate limit.
  - the env var is ELEVENLABS_API_KEY.
  The repo shows the Python SDK, not raw HTTP; the REST paths below come from snippets.

From search snippets of the ElevenLabs docs (pages not opened):
  - POST /v1/text-to-speech/{voice_id}, header xi-api-key, JSON body {text, model_id,
    voice_settings, ...}; output_format is a query parameter (docs example mp3_22050_32).
  - GET /v1/voices -> {"voices": [{voice_id, name, category, labels{accent, gender, age,
    use_case}, description, preview_url, settings}]}.
  - GET /v1/shared-voices with search, accent, language, gender, age, page_size filters.
  - Product guide: v3 stability is presented as Creative 0.0 / Natural 0.5 / Robust 1.0 and
    similarity / speaker boost are hidden for v3. This contradicts the repo example; the script
    follows the repo (sends them) and offers --snap-stability.
  - Audio tags such as [calm] [excited] [whispers] [pause] are written inline in the text.
"""
import argparse
import json
import os
import re
import sys
import time

try:
    import requests
except ImportError:  # pragma: no cover
    sys.exit("pip install requests")

API = os.environ.get("ELEVENLABS_API_BASE", "https://api.elevenlabs.io")
HERE = os.path.dirname(os.path.abspath(__file__))
LINES = os.path.join(HERE, "lines.v2.json")

# Estimated speaking rate for the register in DIRECTION.md (words per second) plus a fixed
# lead-in; used only when mutagen is missing or in --dry-run. Real files are measured.
EST_WPS = 2.2
EST_LEAD = 0.35
TAG_RE = re.compile(r"\[[^\]]*\]\s*")


def load_lines(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def strip_tags(text):
    return re.sub(r"\s{2,}", " ", TAG_RE.sub("", text)).strip()


def estimate_seconds(text):
    words = len(strip_tags(text).split())
    # each [pause] adds roughly half a second in v3 (assumed; not measured)
    pauses = len(re.findall(r"\[pause", text))
    return round(EST_LEAD + words / EST_WPS + 0.5 * pauses, 2)


def measure_seconds(path, fallback_text):
    try:
        from mutagen import File as MutagenFile  # type: ignore
        info = MutagenFile(path)
        if info is not None and getattr(info, "info", None) and info.info.length:
            return round(float(info.info.length), 2)
    except Exception:
        pass
    return estimate_seconds(fallback_text)


def is_v3(model_id):
    return model_id.startswith("eleven_v3")


def snap_stability(value):
    """The product UI presents v3 stability as Creative 0.0 / Natural 0.5 / Robust 1.0
    (snippet), while voice-settings.md gives a continuous 0.0-1.0 range (first-hand). The
    script sends the value as written; --snap-stability rounds to the nearest preset in case an
    account rejects intermediates on v3."""
    return min((0.0, 0.5, 1.0), key=lambda s: abs(s - float(value)))


def voice_settings(el, model_id, snap=False):
    """Build voice_settings per text-to-speech/references/voice-settings.md (first-hand):
    stability, similarity_boost, style, speed, use_speaker_boost. The repo's own eleven_v3
    example sends all of these; a product-guide snippet says v3 ignores similarity and
    speaker boost. We send them and let v3 ignore what it ignores."""
    el = el or {}
    stability = float(el.get("stability", 0.5))
    if snap and is_v3(model_id):
        stability = snap_stability(stability)
    vs = {
        "stability": stability,
        "similarity_boost": float(el.get("similarity", 0.75)),
        "style": float(el.get("style", 0.0)),
        "use_speaker_boost": bool(el.get("speaker_boost", True)),
    }
    speed = float(el.get("speed", 1.0))
    if abs(speed - 1.0) > 1e-6:
        # speed 0.25-4.0 on REST (first-hand). Only sent when a line asks for it; the
        # script paces with punctuation and [pause] instead.
        vs["speed"] = speed
    return vs


def session_for(api_key):
    s = requests.Session()
    s.headers.update({"xi-api-key": api_key, "User-Agent": "ug-showreel-render/2"})
    return s


def tts(session, voice_id, text, model_id, vs, output_format, language_code=None,
        previous_text=None, next_text=None, retries=4):
    # REST path and the output_format query parameter: docs snippets, not exercised here.
    url = f"{API}/v1/text-to-speech/{voice_id}"
    body = {"text": text, "model_id": model_id, "voice_settings": vs}
    if language_code and model_id != "eleven_multilingual_v2":
        # SKILL.md (first-hand): language_code works with eleven_v3, unsupported codes are
        # ignored, and it is not supported on eleven_multilingual_v2.
        body["language_code"] = language_code
    if previous_text:
        body["previous_text"] = previous_text   # request stitching (first-hand, SKILL.md)
    if next_text:
        body["next_text"] = next_text
    for attempt in range(retries):
        r = session.post(url, params={"output_format": output_format}, json=body,
                         headers={"Accept": "audio/mpeg", "Content-Type": "application/json"},
                         timeout=120)
        if r.status_code == 200:
            return r.content
        if r.status_code in (429, 500, 502, 503, 504) and attempt < retries - 1:
            wait = 2 ** attempt
            print(f"  {r.status_code} from the API, retrying in {wait}s", file=sys.stderr)
            time.sleep(wait)
            continue
        raise SystemExit(f"text-to-speech failed {r.status_code}: {r.text[:500]}")


def list_voices(session):
    r = session.get(f"{API}/v1/voices", timeout=60)
    r.raise_for_status()
    voices = r.json().get("voices", [])
    print(f"{'voice_id':<24} {'name':<24} {'category':<12} accent / gender / age / use_case")
    for v in voices:
        lb = v.get("labels") or {}
        print(f"{v.get('voice_id',''):<24} {v.get('name','')[:23]:<24} {str(v.get('category',''))[:11]:<12} "
              f"{lb.get('accent','')} / {lb.get('gender','')} / {lb.get('age','')} / {lb.get('use_case','')}")
        if v.get("description"):
            print(f"{'':<24} {v['description'][:110]}")
    print(f"{len(voices)} voices")


def search_library(session, term, accent=None, language="en", page_size=30):
    params = {"search": term, "language": language, "page_size": page_size}
    if accent:
        params["accent"] = accent
    r = session.get(f"{API}/v1/shared-voices", params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    voices = data.get("voices", data if isinstance(data, list) else [])
    # Field names in the shared-voices response (public_owner_id, accent, descriptive, ...)
    # were not verified from snippets; print what is there rather than assume.
    for v in voices:
        keys = ["public_owner_id", "voice_id", "name", "accent", "gender", "age", "language",
                "descriptive", "use_case", "category"]
        print("  ".join(f"{k}={v.get(k)}" for k in keys if v.get(k) is not None))
        if v.get("description"):
            print(f"    {v['description'][:140]}")
    print(f"{len(voices)} shared voices for {term!r}"
          + (f" accent={accent!r}" if accent else "")
          + ". Add one to your voices in the ElevenLabs UI (or POST /v1/voices/add/"
            "{public_owner_id}/{voice_id}, not verified here) and pass its voice_id with --voice.")


def pick_scenes(data, cut, only):
    scenes = data["scenes"]
    if cut == "short":
        short = data.get("cuts", {}).get("short", [])
        scenes = [s for s in scenes if s["id"] in short]
    if only:
        scenes = [s for s in scenes if s["id"] in only]
    return scenes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lines", default=LINES, help="script file (default lines.v2.json)")
    ap.add_argument("--out", default=HERE, help="output directory (default: this folder)")
    ap.add_argument("--voice", default=os.environ.get("ELEVENLABS_VOICE_ID"), help="voice_id (or ELEVENLABS_VOICE_ID)")
    ap.add_argument("--model", default=None, help="model_id (default from lines.v2.json, eleven_v3)")
    ap.add_argument("--output-format", default=None, help="e.g. mp3_44100_128 (default from lines.v2.json)")
    ap.add_argument("--no-language-code", action="store_true", help="do not send language_code per line (default: en/sw/lg from lines.v2.json)")
    ap.add_argument("--no-stitch", action="store_true", help="do not send previous_text/next_text between the lines of a scene")
    ap.add_argument("--snap-stability", action="store_true", help="round stability to 0 / 0.5 / 1 on v3 (the UI's Creative / Natural / Robust)")
    ap.add_argument("--cut", choices=["long", "short"], default="long", help="render only the short cut's scenes")
    ap.add_argument("--scene", action="append", help="render only this scene id (repeatable)")
    ap.add_argument("--force", action="store_true", help="re-render files that already exist")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, call nothing, write nothing")
    ap.add_argument("--list-voices", action="store_true", help="list the voices on the account and exit")
    ap.add_argument("--search-library", metavar="TERM", help="search the public Voice Library and exit")
    ap.add_argument("--accent", default=None, help="accent filter for --search-library (value not verified; try ugandan, kenyan, african)")
    args = ap.parse_args()

    data = load_lines(args.lines)
    el_cfg = data.get("elevenlabs", {})
    model_id = args.model or el_cfg.get("model_id", "eleven_v3")
    output_format = args.output_format or el_cfg.get("output_format", "mp3_44100_128")
    # first-hand format table: mp3_*, pcm_* (raw, no header), wav_44100, opus_*, ulaw_*, alaw_*
    ext = {"mp3": "mp3", "wav": "wav", "pcm": "pcm", "opus": "opus", "ulaw": "ulaw", "alaw": "alaw"}.get(output_format.split("_")[0], "bin")
    lang_codes = el_cfg.get("language_codes", {})
    api_key = os.environ.get("ELEVENLABS_API_KEY")

    if args.list_voices or args.search_library:
        if not api_key:
            sys.exit("set ELEVENLABS_API_KEY")
        s = session_for(api_key)
        if args.list_voices:
            list_voices(s)
        if args.search_library:
            search_library(s, args.search_library, accent=args.accent)
        return

    speakers = data.get("speakers", {})
    scenes = pick_scenes(data, args.cut, args.scene)

    def voice_for(lang):
        # renderer's --voice / env wins; then speakers.<lang>.id; then speakers.en.id
        return args.voice or (speakers.get(lang) or {}).get("id") or (speakers.get("en") or {}).get("id")

    # ---- plan ----
    plan = []
    for sc in scenes:
        budget = sc.get("budget_seconds")
        total = 0.0
        texts = []
        for ln in sc["lines"]:
            t = ln.get("text_v3") or ln["text"]
            texts.append(t if is_v3(model_id) else strip_tags(t))  # v2/flash read tags as words
        for i, ln in enumerate(sc["lines"], 1):
            text_api = texts[i - 1]
            lang = ln.get("lang", "en")
            vs = voice_settings(ln.get("el"), model_id, args.snap_stability)
            est = estimate_seconds(text_api)
            total += est
            plan.append({"scene": sc["id"], "n": i, "line": ln, "text_api": text_api, "vs": vs,
                         "voice": voice_for(lang), "est": est, "file": f"{sc['id']}-{i}.{ext}",
                         "language_code": None if args.no_language_code else lang_codes.get(lang),
                         "previous_text": None if (args.no_stitch or i == 1) else strip_tags(texts[i - 2]),
                         "next_text": None if (args.no_stitch or i == len(texts)) else strip_tags(texts[i])})
        sc["_est_total"] = round(total, 2)
        sc["_over"] = bool(budget) and total > float(budget)

    if args.dry_run:
        print(f"model {model_id}  format {output_format}  voice {args.voice or '(from lines.v2.json / env)'}  cut {args.cut}")
        for sc in scenes:
            flag = "  OVER BUDGET" if sc["_over"] else ""
            print(f"\n[{sc['id']}] budget {sc.get('budget_seconds')}s  est {sc['_est_total']}s{flag}")
            for p in plan:
                if p["scene"] != sc["id"]:
                    continue
                ln = p["line"]
                lc = f"  language_code={p['language_code']}" if p["language_code"] else ""
                print(f"  {p['file']:<16} {ln.get('lang','en')}  ~{p['est']}s  voice={p['voice'] or '?'}{lc}  settings={json.dumps(p['vs'])}")
                print(f"      {p['text_api']}")
        over = [sc["id"] for sc in scenes if sc["_over"]]
        print("\n" + ("scenes over budget: " + ", ".join(over) if over else "all scenes within budget (estimated)"))
        return

    if not api_key:
        sys.exit("set ELEVENLABS_API_KEY (or use --dry-run)")
    missing = sorted({p["line"].get("lang", "en") for p in plan if not p["voice"]})
    if missing:
        sys.exit(f"no voice_id for {missing}: pass --voice, set ELEVENLABS_VOICE_ID, or fill speakers.<lang>.id in {os.path.basename(args.lines)}")

    os.makedirs(args.out, exist_ok=True)
    s = session_for(api_key)
    manifest = {"engine": f"elevenlabs/{model_id}", "model_id": model_id, "output_format": output_format, "scenes": []}
    for sc in scenes:
        files = []
        for p in plan:
            if p["scene"] != sc["id"]:
                continue
            path = os.path.join(args.out, p["file"])
            if os.path.exists(path) and not args.force:
                print(f"keep  {p['file']}")
            else:
                print(f"render {p['file']}  [{p['line'].get('lang','en')}]  {p['text_api']}")
                audio = tts(s, p["voice"], p["text_api"], model_id, p["vs"], output_format,
                            language_code=p["language_code"], previous_text=p["previous_text"], next_text=p["next_text"])
                with open(path, "wb") as f:
                    f.write(audio)
            files.append({
                "file": p["file"],
                "text": p["line"]["text"],            # clean text for captions; tags stay out
                "lang": p["line"].get("lang", "en"),
                "speaker": p["voice"],
                "seconds": measure_seconds(path, p["text_api"]),
            })
        manifest["scenes"].append({"id": sc["id"], "files": files})
        total = round(sum(f["seconds"] for f in files), 2)
        budget = sc.get("budget_seconds")
        warn = "  OVER BUDGET" if budget and total > float(budget) else ""
        print(f"  {sc['id']}: {total}s of {budget}s{warn}")

    with open(os.path.join(args.out, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)
    print("wrote manifest.json")


if __name__ == "__main__":
    main()
