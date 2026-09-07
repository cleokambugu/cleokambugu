#!/usr/bin/env python3
"""Generate the UG showreel cues with the ElevenLabs Music API -> music/short.mp3, music/long.mp3.

Requires only `requests` and ELEVENLABS_API_KEY in the environment. Run where the network allows:

    python3 generate-elevenlabs.py --dry-run            # print the requests, write nothing
    python3 generate-elevenlabs.py                      # both cuts, composition-plan route
    python3 generate-elevenlabs.py --cut short --mode prompt

Endpoint and fields were verified first-hand in the ElevenLabs skills repository
(github.com/elevenlabs/skills, files music/references/api_reference.md and music/SKILL.md, cloned
2026-09-02) and match the public docs snippets for POST /v1/music:
  - POST https://api.elevenlabs.io/v1/music  with header  xi-api-key: <key>
  - JSON body: prompt (str) XOR composition_plan (object); music_length_ms (3000..600000, prompt mode
    only); model_id ("music_v2" is current; the API still defaults to music_v1); force_instrumental (bool)
  - output_format is a QUERY parameter: mp3_48000_192 is the v2 default; mp3_48000_240 / mp3_48000_320 exist
  - a music_v2 composition_plan is {"chunks": [ {text, duration_ms (3000..120000), positive_styles[],
    negative_styles[], context_adherence "low"|"medium"|"high"} ... ]}, up to 30 chunks, 3 s..10 min total
Fields marked UNCERTAIN below were not confirmable from the repository; see the comments.
"""
import argparse, json, os, sys, time

API = "https://api.elevenlabs.io/v1/music"
PLAN_API = "https://api.elevenlabs.io/v1/music/plan"   # UNCERTAIN: path of composition_plan.create (docs slug "create-composition-plan"); only used with --fetch-plan
HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- prompts (verbatim from BRIEF.md section 5)
PROMPT_SHORT = (
    "Instrumental amapiano with an Afro-house drop, Kampala style, 114 BPM, 4/4, A minor, 90 seconds. Warm, premium, "
    "street-smart; feels like sunrise over a city that is about to move. 0:00 intro: soft Rhodes electric piano chords "
    "(Am7, Fmaj7, Cmaj7, G add9, one chord per bar), continuous 16th-note shakers with swing, a single slow pentatonic "
    "pluck melody (adungu / kalimba tone), riser from 0:05. 0:08 impact hit and the groove enters: saturated amapiano log "
    "drum on the \"and\" of 2 with a pickup on the \"e\" of 1, kick on beats 1 and 3 only, 3-2 son clave, congas tumbao. "
    "0:16 full groove: layered claps on 2 and 4, hi-hats, rimshot, dancehall guitar skank on the off-beats. 0:34 breakdown: "
    "drums drop out, only Rhodes and shaker. 0:41 rebuild with a snare roll and three falling toms. 0:49 the drop: "
    "four-on-the-floor kick, sidechained supersaw chords opening up, one shouted male ad-lib \"hey!\" on the first beat, "
    "then the pluck melody answered by \"hey\" ad-libs. 0:54 modulate up a whole tone to B minor, keep the full groove, add "
    "an East African one-string fiddle lead. 1:04 second drop in B minor with the fiddle lead over it. 1:13 return to A "
    "minor, drums thin out. 1:18 outro with Rhodes, pluck theme and lead, reverse cymbal swelling into 1:23 final hit: big "
    "log drum note, low boom, pluck chord, one last \"hey\", ring out and silence. No lyrics, no singing, no rap, no vocal "
    "chops; the only voice is the short \"hey\" ad-lib. Mix: log drum and kick mono and in front, wide Rhodes and shakers, "
    "plate reverb on claps and Rhodes, dotted-eighth delay on the pluck and lead, glue compression, no clipping, no "
    "brightness harshness."
)
PROMPT_LONG = (
    "Instrumental amapiano with Afro-house drops, Kampala style, 114 BPM, 4/4, A minor, 4 minutes 35 seconds. Warm, "
    "premium, street-smart; the sound of a city that moves. 0:00 opening: soft Rhodes electric piano chords (Am7, Fmaj7, "
    "Cmaj7, G add9, one per bar), swung 16th-note shakers, one slow pentatonic pluck melody (adungu / kalimba tone), riser "
    "from 0:08. 0:10 impact hit, groove enters: saturated amapiano log drum on the \"and\" of 2 with a pickup on the \"e\" "
    "of 1, kick on 1 and 3 only, 3-2 son clave, congas tumbao; 0:15 layered claps on 2 and 4, hats, rimshot, dancehall "
    "guitar skank. 0:20 sparse and darker, a whole tone down to G minor, log drum soft; 0:31 back to A minor groove. 0:40 "
    "street groove with guitar skank, 0:52 full. 1:10 breakdown to Rhodes and shaker only; 1:18 groove returns; 1:29 full; "
    "1:37 snare roll and three falling toms. 1:40 the drop: four-on-the-floor, sidechained supersaw chords, one shouted "
    "male ad-lib \"hey!\" on beat 1, pluck melody answered by \"hey\" ad-libs. 1:50 full groove without lead. 2:15 premium "
    "section: no guitar skank, an East African one-string fiddle lead carries the melody over the groove. 2:35 full groove "
    "with heavier congas and hand percussion. 2:55 modulate up a whole tone to B minor, build, riser at 3:09. 3:11 second "
    "drop in B minor with the fiddle lead over it. 3:25 sparse and reflective in B minor with the lead, 3:35 groove. 3:45 "
    "back to A minor groove, pluck call-and-response. 4:05 full groove. 4:20 groove thinning, 4:28 outro with Rhodes, pluck "
    "theme and lead, reverse cymbal swelling into 4:32 final hit: big log drum note, low boom, pluck chord, one last "
    "\"hey\", ring out to the end. No lyrics, no singing, no rap, no vocal chops; the only voice is the short \"hey\" ad-lib. "
    "Mix: log drum and kick mono and in front, wide Rhodes and shakers, plate reverb on claps and Rhodes, dotted-eighth "
    "delay on the pluck and lead, glue compression on the bus, no clipping."
)

# ---------------------------------------------------------------- composition-plan sections (film-time structure from BRIEF.md)
STYLE = ["amapiano", "afro-house", "Kampala", "114 BPM", "A minor", "log drum bass", "Rhodes electric piano",
         "swung 16th shakers", "3-2 clave", "warm", "premium", "instrumental"]
NO = ["lyrics", "singing", "rap", "vocal chops", "autotune", "EDM supersaw lead", "trap hi-hats", "harsh brightness", "clipping"]
ADLIB = "the only voice is one short shouted male ad-lib \"hey!\""

def chunk(label, ms, text, plus=(), minus=(), adherence="high"):
    return {"text": "[%s]\n%s" % (label, text), "duration_ms": int(ms), "positive_styles": STYLE + list(plus),
            "negative_styles": NO + list(minus), "context_adherence": adherence}

# short: 90 000 ms generated; film uses 0..86 s. Hits: UG lock 8.4 s, Stage drop 49.75 s, Atlas lift 64.9 s.
SECTIONS_SHORT = [
    chunk("Intro", 8400, "Soft Rhodes chords Am7 Fmaj7 Cmaj7 Gadd9 one per bar, swung 16th shakers only, one slow pentatonic pluck melody, riser building into the hit at the end of this section.", ["intro", "sparse", "riser"], ["drums", "kick"]),
    chunk("UG lock groove", 7600, "Impact hit on the first beat. Log drum on the and of 2 with a pickup on the e of 1, kick on 1 and 3 only, 3-2 clave, congas tumbao, shakers.", ["groove", "impact hit", "congas"], ["four-on-the-floor"]),
    chunk("Full groove", 18750, "Add layered claps on 2 and 4, hi-hats, rimshot, dancehall guitar skank on the off-beats. Pluck theme answered an octave up.", ["claps", "guitar skank", "hi-hats"]),
    chunk("Breakdown", 6300, "Drums out. Only Rhodes chords and shaker, the theme held back.", ["breakdown", "quiet"], ["drums", "kick", "log drum"]),
    chunk("Rebuild", 8700, "Kick and log drum return, energy rising, snare roll over the last two beats and three falling toms, reverse cymbal into the drop.", ["build", "snare roll", "toms", "riser"]),
    chunk("Stage drop", 5000, "The drop on the first beat: four-on-the-floor kick, sidechained supersaw chords opening, one shouted male ad-lib hey on beat 1, pluck melody answered by hey ad-libs. " + ADLIB, ["drop", "four-on-the-floor", "supersaw chords", "ad-lib hey"]),
    chunk("Lift build", 10150, "Modulate up a whole tone to B minor, full groove, East African one-string fiddle lead, riser into the next drop.", ["B minor", "fiddle lead", "riser"]),
    chunk("Atlas lift", 8600, "Second drop in B minor, four-on-the-floor, supersaw chords, fiddle lead over it, hey ad-libs. " + ADLIB, ["drop", "B minor", "fiddle lead", "ad-lib hey"]),
    chunk("Back home", 10300, "Return to A minor, kick on 1 and 3, drums thinning to Rhodes, theme and lead; reverse cymbal swelling into the final hit.", ["outro", "A minor", "reverse cymbal"], ["four-on-the-floor"]),
    chunk("Final hit", 6200, "One big final hit on the first beat: log drum note, low boom, pluck chord, one last hey, ring out, then silence. " + ADLIB, ["final hit", "ring out", "silence"], ["drums continuing"]),
]
# long: 275 000 ms = 4:35. Hits: UG lock 10.6, Stage drop 100.0, Atlas lift 191.3, final hit 272.4 s.
SECTIONS_LONG = [
    chunk("Opening", 10600, "Soft Rhodes chords Am7 Fmaj7 Cmaj7 Gadd9, swung shakers only, one slow pentatonic pluck melody, riser building into the hit at the end.", ["intro", "sparse", "riser"], ["drums", "kick"]),
    chunk("UG lock groove", 9400, "Impact hit on the first beat, then the groove: log drum on the and of 2, kick on 1 and 3, 3-2 clave, congas; claps, hats and guitar skank join halfway.", ["impact hit", "groove", "claps"], ["four-on-the-floor"]),
    chunk("Problem", 20000, "Sparse and darker, a whole tone down to G minor, log drum soft, clave and shaker; halfway back up to A minor and the groove.", ["G minor", "sparse", "tension"], ["four-on-the-floor"]),
    chunk("Ride", 30000, "Street groove in A minor with guitar skank on the off-beats, kick on 1 and 3, log drum; claps and hats from the middle.", ["guitar skank", "groove"], ["four-on-the-floor"]),
    chunk("Pool build", 30000, "Breakdown to Rhodes and shaker, then the groove returns, then full; last two seconds a snare roll, three falling toms and a reverse cymbal into the drop.", ["breakdown", "build", "snare roll", "riser"]),
    chunk("Stage drop", 10000, "The drop on the first beat: four-on-the-floor, sidechained supersaw chords, shouted male ad-lib hey on beat 1, pluck melody answered by hey ad-libs. " + ADLIB, ["drop", "four-on-the-floor", "supersaw chords", "ad-lib hey"]),
    chunk("Drive", 25000, "Full groove, claps, hats, guitar skank, no lead.", ["groove", "claps"], ["fiddle"]),
    chunk("Rent", 20000, "Premium: no guitar skank, kick on 1 and 3, an East African one-string fiddle lead carries the melody over the groove.", ["fiddle lead", "premium", "smooth"], ["guitar skank", "four-on-the-floor"]),
    chunk("Deliver", 20000, "Full groove with heavier congas and hand percussion.", ["congas", "hand percussion"]),
    chunk("Atlas build", 16300, "Modulate up a whole tone to B minor, groove then full, riser, snare roll and toms into the drop.", ["B minor", "build", "riser"]),
    chunk("Atlas lift", 13700, "Second drop in B minor with the fiddle lead over four-on-the-floor and supersaw chords, hey ad-libs. " + ADLIB, ["drop", "B minor", "fiddle lead", "ad-lib hey"]),
    chunk("Explore", 20000, "Sparse and reflective in B minor with the fiddle lead, then the groove returns halfway.", ["B minor", "reflective", "fiddle lead"], ["four-on-the-floor"]),
    chunk("Plug-ins", 20000, "Back to A minor groove, pluck melody call-and-response.", ["A minor", "groove", "pluck"], ["four-on-the-floor"]),
    chunk("Stay", 15000, "Full groove, claps, hats, guitar skank.", ["groove", "claps", "guitar skank"]),
    chunk("Close", 15000, "Groove thinning, then Rhodes, pluck theme and lead; reverse cymbal swelling into one big final hit at 12.4 seconds into this section: log drum note, low boom, pluck chord, one last hey, ring out to the end. " + ADLIB, ["outro", "reverse cymbal", "final hit", "ring out"], ["drums continuing"]),
]
CUTS = {"short": (PROMPT_SHORT, SECTIONS_SHORT, 90000), "long": (PROMPT_LONG, SECTIONS_LONG, 275000)}


def body_for(cut, mode, model, instrumental):
    prompt, sections, ms = CUTS[cut]
    total = sum(c["duration_ms"] for c in sections)
    assert total == ms, "%s plan is %d ms, expected %d" % (cut, total, ms)
    body = {"model_id": model}
    if mode == "prompt":
        body["prompt"] = prompt
        body["music_length_ms"] = ms
        if instrumental:
            body["force_instrumental"] = True   # UNCERTAIN whether this also suppresses the "hey" ad-lib; off by default for that reason
    else:
        body["composition_plan"] = {"chunks": sections}   # UNCERTAIN: v2 plans may also accept top-level global-style fields; the repo documents only chunks
        # force_instrumental is documented as prompt-mode only, so it is not sent with a plan
    return body


def fetch_plan(session, cut, model, timeout):
    """Optional: ask the API for its own plan (POST /v1/music/plan, UNCERTAIN path), then replace its chunks with ours so any
    server-side top-level fields survive. Returns the merged plan or None."""
    prompt, sections, ms = CUTS[cut]
    r = session.post(PLAN_API, json={"prompt": prompt, "music_length_ms": ms, "model_id": model}, timeout=timeout)
    if r.status_code != 200:
        print("  plan endpoint returned %s: %s" % (r.status_code, r.text[:300]), file=sys.stderr)
        return None
    plan = r.json()
    plan["chunks"] = sections
    return plan


def generate(cut, args):
    import requests
    body = body_for(cut, args.mode, args.model, args.instrumental)
    out = os.path.join(args.out, cut + ".mp3")
    params = {"output_format": args.format}
    print("[%s] POST %s  params=%s  mode=%s  %d ms -> %s" % (cut, API, params, args.mode, CUTS[cut][2], out))
    if args.dry_run:
        print(json.dumps(body, indent=2)[:4000] + ("\n  ..." if len(json.dumps(body)) > 4000 else ""))
        return True
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        print("ELEVENLABS_API_KEY is not set", file=sys.stderr)
        return False
    s = requests.Session()
    s.headers.update({"xi-api-key": key, "accept": "audio/mpeg"})
    if args.mode == "plan" and args.fetch_plan:
        merged = fetch_plan(s, cut, args.model, args.timeout)
        if merged:
            body["composition_plan"] = merged
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, cut + ".request.json"), "w") as f:   # provenance for the licensing record
        json.dump({"endpoint": API, "params": params, "body": body, "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, f, indent=2)
    for attempt in range(1, 4):
        try:
            r = s.post(API, params=params, json=body, timeout=args.timeout, stream=True)
        except requests.RequestException as e:
            print("  attempt %d failed: %s" % (attempt, e), file=sys.stderr)
            time.sleep(5 * attempt)
            continue
        if r.status_code in (429, 500, 502, 503, 504):
            print("  attempt %d: HTTP %s, retrying" % (attempt, r.status_code), file=sys.stderr)
            time.sleep(10 * attempt)
            continue
        if r.status_code != 200:
            print("  HTTP %s: %s" % (r.status_code, r.text[:1000]), file=sys.stderr)
            return False
        ctype = r.headers.get("content-type", "")
        if not (ctype.startswith("audio/") or ctype == "application/octet-stream"):
            print("  unexpected content-type %s: %s" % (ctype, r.text[:500]), file=sys.stderr)   # compose returns raw audio; only /detailed returns multipart/JSON
            return False
        n = 0
        with open(out, "wb") as f:
            for part in r.iter_content(65536):
                if part:
                    f.write(part)
                    n += len(part)
        if n < 10000:
            print("  file too small (%d bytes)" % n, file=sys.stderr)
            return False
        print("  wrote %s (%.1f MB). Conform in the edit so the first hit lands; see BRIEF.md section 5." % (out, n / 1e6))
        return True
    return False


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--cut", choices=["short", "long", "all"], default="all")
    p.add_argument("--mode", choices=["plan", "prompt"], default="plan", help="composition plan (timed sections, default) or the free-text prompt")
    p.add_argument("--model", default="music_v2")
    p.add_argument("--format", default="mp3_48000_192", help="output_format query parameter, e.g. mp3_48000_192 or mp3_48000_240")
    p.add_argument("--out", default=HERE, help="directory for short.mp3 / long.mp3 (default: this music/ folder)")
    p.add_argument("--instrumental", action="store_true", help="send force_instrumental=true (prompt mode; may remove the ad-lib)")
    p.add_argument("--fetch-plan", action="store_true", help="plan mode: fetch the API's own plan first and merge our chunks into it")
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--dry-run", action="store_true", help="print the request bodies and write nothing")
    args = p.parse_args()
    cuts = ["short", "long"] if args.cut == "all" else [args.cut]
    ok = all([generate(c, args) for c in cuts])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
