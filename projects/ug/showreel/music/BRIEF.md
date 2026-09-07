# UG showreel — music brief (the real-track path)

Written by the three of us: a Kampala producer (works with Gen Z acts in amapiano, Afro-house,
kidandali-pop and Ugandan dancehall), a music supervisor who clears tracks for adverts, and the
WebAudio engineer who built `../ug-score.js`. It answers the client's note on the current
generative score — *"the sound is an extra layer of roboticness; something else that speaks to
Gen Z, millennials and young professionals would be helpful"* — for a Ugandan mobility app
(Ride. Pool. Rent. Deliver.) that is premium but street-smart, warm dark palette with yellow.

This file is the plan for when the network allows real audio. `generate-elevenlabs.py` next to
it turns the prompts below into `music/short.mp3` and `music/long.mp3`; the showreel pages and
`build-video.js` use those files when they exist and fall back to the synthesised score
(`ug-score.js` v2, see `../SCORE.md`) when they do not.

## 1. Why the current score reads as robotic (diagnosis, from the code)

Read first-hand in `ug-score.js` v1: every hit at the same velocity on a 16th grid with one
global swing value; a raw detuned-sawtooth pad; white-noise hats and claps with no room; a log
drum with no saturation; one filter shape per instrument for the whole piece; no pushes, fills,
breakdowns or human marks. The rhythm design was right (log drum on the "and" of 2, 3-2 clave,
swung shakers) — the *sound* around it was the giveaway. v2 of the synth fixes the mechanics
(see `../SCORE.md`, "v2"); a real production fixes the rest.

## 2. The sound we recommend for this audience

**One sentence:** Kampala amapiano with an Afro-house drop and a kidandali-pop heart — the
sound on the Friday line-ups and the Gen Z playlists in Uganda right now, mixed premium.

- **Tempo 112–116 BPM** (we use 114, the same as the synth). Amapiano and the Kampala club
  edits sit here; it also lets the 20–40 s scenes breathe. Do not go to Afro-house's 122–124
  for the whole cue; use that *energy* on the drops at 114.
- **Key: A minor**, pentatonic melody (A C D E G), moving up a whole tone to **B minor** for the
  Atlas section. Chord bed Am7 · Fmaj7 · Cmaj7 · G(add9), one chord a bar.
- **Rhythmic references, precisely:**
  - *Log drum* (the amapiano bass, 40–90 Hz, sampled or Serum-style with saturation): pickup
    on the "e" of 1, main hit on the "and" of 2, tail on the "and" of 3 and the "and" of 4;
    second bar adds the "a" of 2 and "a" of 4. Pitches root → 5th → 4th → 3rd of the bar's
    chord. Played a few ms *late* against the grid.
  - *Kick*: on 1 and 3 in the grooves (the log drum carries the bass, Pretoria-style);
    four-on-the-floor only on the two drops. Sidechain the chords and pad to it.
  - *Shakers*: continuous 16ths, swing 58–62 % (the "e" and "a" pushed late), accent cycle
    strong / soft / medium / soft; a real shaker or a good pack, never one sample repeated.
  - *3-2 son clave* on a wood/rim sound (1, "a" of 1, "and" of 2, "and" of 3, 4) — the
    melody is written *on* the clave so they read as one gesture.
  - *Claps* on 2 and 4 from the full groove onward, layered (a tight clap plus a roomy one),
    and a *rimshot* on the "a" of 2 and the "a" of 4.
  - *Congas / engalabi*: tumbao — heel ghosts on 1 and its "and", slap on 2, open tones on
    the "and" and "a" of 4. On the Deliver scene, heavier.
  - *Guitar skank* on every off-8th (kidandali / dancehall chop) in the street scenes (Ride,
    Drive, Stay); none under Rent/Signature, which is the premium beat.
  - *Fills*: an 8-hit rim/snare roll over the last two beats and three falling toms into each
    drop; a reverse cymbal (1.9 s) into the final hit.
- **Instrumentation:** log drum, sub, amapiano kit (kick, layered clap, hats with real decay
  differences, shakers, shekere, rim), congas/engalabi, a Rhodes-style electric piano comping
  the chords (whole-bar chords in the quiet sections, syncopated stabs in the groove), a
  pentatonic pluck for the theme (adungu / kalimba register, ~220–440 Hz), a supersaw pad that
  only opens on the drops, an endingidi-style fiddle lead (or a real one) on Rent and the
  Atlas, guitar skank.
- **Vocals: none, except an ad-lib.** One short male "hey!" / "eh!" as the answer to the
  pluck phrase on the drops and on the final hit. No lyrics, no hook, no rap, no vocal chops
  longer than a syllable. The ad-lib is the human stamp Gen Z listens for; a sung hook would
  fight the narration and date the film.
- **Mix intent:** warm and wide, not bright. Log drum and kick mono and in front; Rhodes and
  shakers panned; a plate on claps, Rhodes and the ad-lib; a dotted-8th delay on the pluck and
  the lead; glue compression on the bus; no hard clipping. It should feel expensive at low
  volume on a phone and still bounce in a car.

## 3. Reference-track archetypes

These are *types* of record, not any artist's work; nobody has been approached and no artist
is involved.

1. **The sunrise-to-street amapiano instrumental** — 112 BPM, soft electric-piano intro for
   eight bars with shakers only, the log drum enters on bar 9 and carries the bass on its own,
   kick on 1 and 3, a whistle or pluck melody in the pentatonic, claps from the second phrase,
   a two-bar drum-out before each new section. The blueprint for our opening, Ride and Rent.
2. **The Afro-house festival edit** — 122 BPM in its home form, but what we borrow is the drop:
   a filtered supersaw chord that opens over two bars, a four-on-the-floor kick under a
   syncopated bass, a big clap, one shouted ad-lib on the first beat of the drop, everything
   sidechained hard. The blueprint for the Stage drop and the Atlas lift, played at 114.
3. **The Kampala pop-dancehall crossover** — 100–105 BPM, guitar skank on the off-8ths, a
   kidandali-style pentatonic lead line, hand percussion and a "hey" call-and-response with the
   melody, the sound of the Kampala radio hour. The blueprint for the skank, the lead and the
   call-and-response; we lift the tempo to 114 so it locks with the amapiano frame.

## 4. Licensing note (music supervisor)

Three routes, in the order we would run them for this film:

| Route | Best for | Rights to secure | Watch-outs |
|---|---|---|---|
| **A. Commission a Kampala producer** (recommended for the final) | Authenticity; cue timed to the picture; stems for the edit | Work-for-hire *or* exclusive sync + master licence: worldwide, all media (web, social, paid social, events, broadcast optional), perpetuity for the showreel, 1–3 years for paid campaigns; written warranty that any sample pack / loop used is cleared; PRO registration (in Uganda, UPRS) so cue sheets can be filed | Indicative budget (estimate, not a quote): USD 300–1,500 for an emerging producer, more for a name; 1–2 weeks with two revision rounds; ask for a 90 s and a 4:35 conform, stems, and the ad-lib as a separate stem |
| **B. License from a library** (Artlist, Epidemic Sound, Musicbed or an African-focused catalogue; search "amapiano", "afro house", "log drum", "afrobeats instrumental") | Speed, low cost, clean paperwork | A licence tier that explicitly covers *paid advertising* and app-store / product video use, not just social; check whether the licence survives the end of a subscription | Not bespoke — the drops will not land on the UG lock, the Stage drop or the Atlas lift without an edit; someone else can use the same track |
| **C. Generate with ElevenLabs Music (or similar)** — this file's prompts + `generate-elevenlabs.py` | Today: a review track that can ship, timed by a composition plan | Commercial-use rights depend on the plan the file is generated under — read the current terms before it goes into paid media, keep the generation record (request JSON is saved beside each MP3), disclose AI origin where a platform requires it | Cultural authenticity is the risk: have the Kampala producer listen before it goes out; treat it as a temp track that is allowed to ship, not the destination |

Our recommendation: run **C now** (client review this week), commission **A** for the final
using the same brief and timestamps, so the film does not need re-editing when the real cue
arrives.

## 5. Prompts for ElevenLabs Music

Verified first-hand against the ElevenLabs skills repository, file
`music/references/api_reference.md` and `music/SKILL.md` (github.com/elevenlabs/skills, cloned
2026-09-02): `POST https://api.elevenlabs.io/v1/music` takes either `prompt` (+
`music_length_ms`, 3 000–600 000 ms) or a `composition_plan`; `model_id` should be `music_v2`;
`output_format` is a query parameter (`mp3_48000_192` default for v2, `mp3_48000_240` and
`mp3_48000_320` exist); a v2 plan is an ordered list of `chunks` (3 000–120 000 ms each, up to
30) with `text`, `duration_ms`, `positive_styles`, `negative_styles`, `context_adherence`. The
plan route is how the timed cues (UG lock, Stage drop, Atlas lift) get their timestamps; the
free-text prompt route is the fallback. The API does not promise sample-accurate section
boundaries (`respect_sections_durations` is a v1-only flag), so the generated file is conformed
in the edit: slip it so the first drop lands, and check the second.

### 5a. Short cut — 90 s generated, used as 86 s (`music/short.mp3`)

Structure (timestamps are film time; the UG lock at 8.4 s, the Stage drop at 49.75 s and the
Atlas lift at 64.9 s are the three hits that must land):

| Film time | Section | What happens |
|---|---|---|
| 0:00.0 | Intro | Rhodes chords in A minor, shakers only, the pentatonic pluck theme once, slowly; a riser from 0:05.8 |
| **0:08.4** | **UG lock** | Impact hit; log drum, kick on 1 and 3, clave and congas enter |
| 0:16.0 | Full groove | Claps on 2 and 4, hats, guitar skank on the off-8ths |
| 0:34.75 | Breakdown | Drums out: Rhodes and shaker only, theme held back |
| 0:41.0 | Rebuild | Kick and log drum back, rim roll and three toms into the drop |
| **0:49.75** | **Stage drop** | Four-on-the-floor, supersaw chords open, "hey!" on beat 1, pluck-and-"hey" call-and-response |
| 0:54.75 | Lift | Key up a whole tone to B minor, full groove, fiddle lead, riser from 1:02.7 |
| **1:04.9** | **Atlas lift** | Second drop in B minor, lead over it |
| 1:13.5 | Back home | A minor, kick on 1 and 3, thinning |
| 1:18.0 | Outro | Rhodes, theme, lead; reverse cymbal into the hit |
| **1:23.8** | **Final hit** | Log drum + boom + pluck chord + "hey"; tail to 1:26.5, then silence to 1:30 |

Prompt text (`PROMPT_SHORT` in `generate-elevenlabs.py`):

> Instrumental amapiano with an Afro-house drop, Kampala style, 114 BPM, 4/4, A minor, 90 seconds. Warm, premium, street-smart; feels like sunrise over a city that is about to move. 0:00 intro: soft Rhodes electric piano chords (Am7, Fmaj7, Cmaj7, G add9, one chord per bar), continuous 16th-note shakers with swing, a single slow pentatonic pluck melody (adungu / kalimba tone), riser from 0:05. 0:08 impact hit and the groove enters: saturated amapiano log drum on the "and" of 2 with a pickup on the "e" of 1, kick on beats 1 and 3 only, 3-2 son clave, congas tumbao. 0:16 full groove: layered claps on 2 and 4, hi-hats, rimshot, dancehall guitar skank on the off-beats. 0:34 breakdown: drums drop out, only Rhodes and shaker. 0:41 rebuild with a snare roll and three falling toms. 0:49 the drop: four-on-the-floor kick, sidechained supersaw chords opening up, one shouted male ad-lib "hey!" on the first beat, then the pluck melody answered by "hey" ad-libs. 0:54 modulate up a whole tone to B minor, keep the full groove, add an East African one-string fiddle lead. 1:04 second drop in B minor with the fiddle lead over it. 1:13 return to A minor, drums thin out. 1:18 outro with Rhodes, pluck theme and lead, reverse cymbal swelling into 1:23 final hit: big log drum note, low boom, pluck chord, one last "hey", ring out and silence. No lyrics, no singing, no rap, no vocal chops; the only voice is the short "hey" ad-lib. Mix: log drum and kick mono and in front, wide Rhodes and shakers, plate reverb on claps and Rhodes, dotted-eighth delay on the pluck and lead, glue compression, no clipping, no brightness harshness.

### 5b. Long cut — 4:35 (`music/long.mp3`)

| Film time | Scene | What happens |
|---|---|---|
| 0:00.0 | Opening | Rhodes + shaker + slow theme; riser from 0:08 |
| **0:10.6** | **UG lock** | Impact; log drum, kick 1 & 3, clave, congas; 0:15.5 claps, hats, skank |
| 0:20.0 | Problem | Sparse and a whole tone down (G minor); 0:31.4 back to A minor, groove |
| 0:40.0 | Ride | Groove with guitar skank; 0:52 full |
| 1:10.0 | Pool | Breakdown (Rhodes + shaker); 1:18.4 groove; 1:29 full; 1:37.8 riser, roll, toms |
| **1:40.0** | **Stage drop** | Four-on-the-floor, supersaw, "hey!" call-and-response |
| 1:50.0 | Drive | Full groove, no lead |
| 2:15.0 | Rent | Groove, no skank, fiddle lead carries the theme (premium) |
| 2:35.0 | Deliver | Full, hand percussion heavier |
| 2:55.0 | Atlas | Up to B minor; 3:01 full; 3:09 riser |
| **3:11.3** | **Atlas lift** | Second drop, B minor, lead |
| 3:25.0 | Explore | Sparse + lead (B minor); 3:35 groove |
| 3:45.0 | Plug-ins | Back to A minor, groove, pluck call-and-response |
| 4:05.0 | Stay | Full |
| 4:20.0 | Close | Groove; 4:28 outro (Rhodes, theme, lead); reverse cymbal |
| **4:32.4** | **Final hit** | Log drum + boom + pluck chord + "hey"; ring out to 4:35 |

Prompt text (`PROMPT_LONG`):

> Instrumental amapiano with Afro-house drops, Kampala style, 114 BPM, 4/4, A minor, 4 minutes 35 seconds. Warm, premium, street-smart; the sound of a city that moves. 0:00 opening: soft Rhodes electric piano chords (Am7, Fmaj7, Cmaj7, G add9, one per bar), swung 16th-note shakers, one slow pentatonic pluck melody (adungu / kalimba tone), riser from 0:08. 0:10 impact hit, groove enters: saturated amapiano log drum on the "and" of 2 with a pickup on the "e" of 1, kick on 1 and 3 only, 3-2 son clave, congas tumbao; 0:15 layered claps on 2 and 4, hats, rimshot, dancehall guitar skank. 0:20 sparse and darker, a whole tone down to G minor, log drum soft; 0:31 back to A minor groove. 0:40 street groove with guitar skank, 0:52 full. 1:10 breakdown to Rhodes and shaker only; 1:18 groove returns; 1:29 full; 1:37 snare roll and three falling toms. 1:40 the drop: four-on-the-floor, sidechained supersaw chords, one shouted male ad-lib "hey!" on beat 1, pluck melody answered by "hey" ad-libs. 1:50 full groove without lead. 2:15 premium section: no guitar skank, an East African one-string fiddle lead carries the melody over the groove. 2:35 full groove with heavier congas and hand percussion. 2:55 modulate up a whole tone to B minor, build, riser at 3:09. 3:11 second drop in B minor with the fiddle lead over it. 3:25 sparse and reflective in B minor with the lead, 3:35 groove. 3:45 back to A minor groove, pluck call-and-response. 4:05 full groove. 4:20 groove thinning, 4:28 outro with Rhodes, pluck theme and lead, reverse cymbal swelling into 4:32 final hit: big log drum note, low boom, pluck chord, one last "hey", ring out to the end. No lyrics, no singing, no rap, no vocal chops; the only voice is the short "hey" ad-lib. Mix: log drum and kick mono and in front, wide Rhodes and shakers, plate reverb on claps and Rhodes, dotted-eighth delay on the pluck and lead, glue compression on the bus, no clipping.

Both prompts are embedded verbatim as constants in `generate-elevenlabs.py`, and the same
tables are embedded as `SECTIONS_SHORT` / `SECTIONS_LONG` to build the composition plan (the
default route, `--mode plan`; `--mode prompt` sends the paragraph instead).

## 6. Mastering and delivery spec

- **Music-only deliverables** (`short.mp3`, `long.mp3`, plus 48 kHz / 24-bit WAV masters if
  the producer route is taken): **−14 LUFS integrated, −1.0 dBTP true peak** (YouTube, LinkedIn,
  Instagram and TikTok normalise around −14 LUFS; louder buys nothing and loses the transients
  of the log drum). Loudness range 6–9 LU: the breakdowns should be audibly quieter than the
  drops. Sub below 120 Hz mono; high-pass at 30 Hz; no more than ~3 dB of limiter gain
  reduction on the drops.
- **The mixed showreel** (`build-video.js`, music + narration): program **−14 LUFS integrated,
  −1.0 dBTP**; narration at −16 to −18 LUFS short-term on top of the bed; music ducked 8–10 dB
  under speech (the existing sidechain in `build-video.js` uses attack 40 ms / release 400 ms,
  which is right), and the same 0.4 (−8 dB) duck the browser player applies.
- **Files:** MP3 48 kHz ≥ 192 kbps for the browser pages (`mp3_48000_192` from the API;
  `mp3_48000_240` or `_320` if the plan allows); AAC 256 kbps in the MP4 mux; leave 1.5 s of
  tail after the final hit; no silence at the head (the film starts on the first chord).
- **Stems** (producer route): drums, log drum + sub, Rhodes/chords, pluck, lead, ad-libs, FX
  — so the edit can drop the lead under a line of narration without losing the groove.

## 7. Provenance

- Read first-hand: `../ug-score.js` (v1 and v2), `../SCORE.md`, `../build-video.js`,
  `../index.html` (the audio wiring), and the ElevenLabs skills repository files
  `music/references/api_reference.md` and `music/SKILL.md` (github.com/elevenlabs/skills).
- From search snippets only: the ElevenLabs docs pages for `POST /v1/music` (confirming
  `prompt`, `music_length_ms` 3 000–600 000, `model_id` default `music_v1`, `output_format`
  `auto`), which agree with the repository file.
- Not verified in this sandbox (blocked network): no audio was generated or listened to here;
  loudness-normalisation targets of the platforms are the team's working knowledge, not measured
  today. Genre and rhythm references are the producer's practice, not citations.
