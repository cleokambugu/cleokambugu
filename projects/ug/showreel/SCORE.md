# UG showreel score — design note

Generative WebAudio score for `showreel/sound.html`. No samples, no fetches: everything is
oscillators, filtered noise and a synthetic convolution reverb, scheduled on the AudioContext
clock. Engine: `ug-score.js` (`window.UGScore.create(ctx, destGain)`).

**Tempo 114 BPM, 4/4, 16th grid with 17% swing on the off-16ths (21% on the shakers).**
Home key A minor; the theme is A minor pentatonic (A C D E G). Chord bed: Am7 · Fmaj7 · Cmaj7 · G,
one chord a bar in the groove, one every two bars in the opening.

## Wiring into the showreel

```js
// in audio.start(), after `master` exists:
score = UGScore.create(ac, master);   // master is the existing gain -> ac.destination
score.play('long');                   // or 'short' for the 60 s cut
// in enterScene(i):  score.cue(i);
// around voice.say(): score.duck(true) before, score.duck(false) on utterance 'end'
// on finish/pause:    score.stop()  /  ac.suspend() as today
```

`cue(i)` switches the scene program at the next 16th and re-bases the scene clock, so the
in-scene hits (the lock flash at 10.55 s in the opening, the drop at 30 s in Pool) land where
the canvas draws them. `duck(true)` drops the music 8 dB (gain 0.4) with a 60 ms time constant.
The existing bed (`oscA/oscB/sub/third` + the 96 BPM kick/shaker in `tick()`) should be removed
or its `bedGain` left at 0; two tempos fighting is the one thing that would sound amateur.

## Cue sheet — long cut (4:35, twelve scenes as in `SCENES`)

| # | Scene (dur) | Musical intent | Level / layers | Key |
|---|---|---|---|---|
| 0 | Opening, map assembles (20 s) | Cinematic dawn: pad breathes, the UG theme plucked slowly and alone; riser from 8 s; **impact on the U+G lock at 10.6 s**; groove enters under "Ride. Pool. Rent. Deliver." | `pad` → riser → `groove` @10.6 → `full` @15.5 | A |
| 1 | The problem (20 s) | Three apps, hesitation: thinner, darker, whole tone down; the crest at 11.4 s pulls it home | `sparse` (G) → `groove` (A) @11.4 | G → A |
| 2 | Ride, compare desk (30 s) | Purposeful street groove; guitar skank enters with the quotes; claps when Book on UG buttons land | `groove`+skank → `full` @12 | A |
| 3 | Pool, virtual stage (40 s) | Breakdown to Rhodes and shaker as the stage opens; the seats fill, the price falls: build; riser at 27.8 s; **the drop at 30 s** when UG manufactures the trip | `break` → `groove` @8.4 → `full` @19 → riser → `drop` @30 | A |
| 4 | Drive / offers (25 s) | Driver's side; keeps the drop's energy without the lead | `full` | A |
| 5 | Rent and Signature (20 s) | Premium: skank off, endingidi-style lead carries the theme over the fleet | `groove`, lead on, skank off | A |
| 6 | Deliver (20 s) | The parcel: hand percussion heavier (congas ×1.3) | `full` | A |
| 7 | The Atlas, air/water/rail (30 s) | Lift: modulate up to B; second riser; drop with lead as the atlas opens | `groove` → `full` → riser → `drop` @16.3 | B |
| 8 | Explore / foresight (20 s) | Reflective; lead over sparse bed, then groove | `sparse`+lead → `groove` | B |
| 9 | Plug-ins / languages (20 s) | Back home to A; pluck call-and-response | `groove` | A |
| 10 | Stay on UG / teleport (15 s) | Full tilt into the close | `full` | A |
| 11 | One link / close (15 s) | Drums out at 8 s, pad + theme + lead; **final hit at 12.4 s** (log drum, pluck chord, shekere, boom) under the crest | `groove` → `outro` → fin | A |

## Cue sheet — short cut (86 s, two drops)

0 s `pad` (Rhodes + solo theme) → 5.8 s riser → **8.4 s impact, `groove`** (the UG lock) → 16 s
`full` with skank → 34.75 s `break` (Rhodes + shaker) → 41.05 s `groove` → 47.5 s riser with fill →
**49.75 s impact + `drop`** (the Stage) → 54.75 s `full` in B with lead → 62.7 s riser → **64.9 s
impact + `drop`** (the Atlas lift) → 73.5 s `groove` back in A → 78 s `outro` → **83.8 s final
hit** (reverse riser from 81.9 s) → 86.5 s off. Verbs land on the first drop; the QR/install card
on the final hit.

## Levels (what each layer set contains)

- `pad` — Rhodes whole-bar chords over the dark pad (v2: triangles + sub through a slow-LFO lowpass), theme at half speed.
- `break` — (v2) the breakdown: Rhodes, shaker and the half-speed theme, nothing else.
- `sparse` — + 3-2 clave, light shaker, shekere on the beats, rim, log drum at 60%.
- `groove` — + kick on 1 and 3 (ghost on the "a" of 3), congas, closed hat on the off-8ths, full log drum, theme at tempo.
- `full` — + claps on 2 and 4, 16th hat ghosts, guitar skank on every "and".
- `drop` — kick four-on-the-floor, open hat on the "and" of 4, log drum +15%, lead on, pad pulled back.
- `outro` — pad, half-speed theme, lead, half shekere.

Per-entry overrides (`lead`, `skank`, `conga`, `key`) let a scene bend a level without a new one.

## What makes it read as Ugandan / East African

Rhythm, not timbre, is doing the work; a Kampala listener locks onto these before the sounds:

- **Log drum on the "and" of 2** (step 6 of 16, velocity 1.0) with the pickup on the "e" of 1
  (step 3) and the tail on the "and" of 3 and 4 (steps 10, 12, 14). Second bar adds the "a" of 2
  and the "a" of 4 (steps 13, 15) so the two-bar phrase breathes. Pitches move root → 5th → 4th
  → 3rd of the bar's chord, in the 40–90 Hz octave (A1 = 55 Hz), synthesised as a sine with a
  2.6× pitch drop over 45 ms plus a triangle for the 2nd harmonic so phones still hear it. The
  whole harmonic bus (pad, log, pluck, skank) is sidechained to the kick (dip to 0.32 in 12 ms,
  back in 300 ms) — the amapiano pump. In `groove` the kick sits on 1 and 3 only, the way the
  Pretoria records leave the log drum to carry the bass; four-on-the-floor is saved for the drops.
- **Shaker 16ths with swing**: every 16th, accent cycle 1 / .35 / .6 / .45, off-16ths pushed 21%
  late (≈28 ms at 114). This is the shuffle that separates amapiano and Ugandan dance records
  from straight house.
- **3-2 son clave** (steps 0, 3, 6, 10, 12) on a woodblock-ish sine pair, the afrobeats spine.
  The UG theme is written *on the clave*: the first bar's notes fall on exactly those five
  steps, so melody and clave are one gesture. Bars 3-4 answer an octave up, quieter.
- **Shekere** on the four beats with the "pre-hit" on the "and" of 4 and the "a" of 2, built as
  two bursts 17 ms apart (the bead net then the gourd). **Congas** play a tumbao: heel ghosts on
  1 and "and" of 1, slap on 2, open tones on the "and" and "a" of 4.
- **Guitar skank on every off-8th** (steps 2, 6, 10, 14): three saws through a tight 2.1 kHz
  bandpass, 130 ms decay, chord tones an octave up — the kidandali/dancehall chop that runs under
  the Kampala radio sound.
- **Pentatonic pluck** (adungu / kalimba territory): triangle + octave sine + a 12 ms click,
  lowpass closing 5.2 kHz → 900 Hz in 180 ms, 0.7 s decay, a little reverb. A minor pentatonic
  throughout; the modulation to B for the Atlas keeps the same shape a tone higher.
- **Endingidi-style lead**: a sawtooth through a nasal bandpass (1.1 kHz, Q 3.2), 5.6 Hz vibrato
  at ±14 cents, slow 90 ms attack, playing the theme at half speed, legato — the one-string fiddle
  drone-and-wail that says village and city at once.
- The harmonic bed is deliberately plain (i · VI · III · VII) so the percussion reads as the lead.

## What a real production replaces

- **Log drum and kick**: a sampled or Serum-style log drum with proper saturation and layered
  sub; today's sine-with-pitch-drop is the shape, not the weight.
- **Engalabi and hand drums**: sampled engalabi (the long Ganda drum) and real congas/shekere,
  multi-velocity, with room mics. Noise-burst percussion has no wood, skin or bead in it.
- **Guitar**: a session guitarist for the skank and a proper kidandali run (the fast pentatonic
  lead lines) — the single element synthesis reads most obviously as fake.
- **Adungu and endingidi**: a played adungu for the theme and a real endingidi player for the
  lead; buzz, bow noise and tuning drift are the point of those instruments.
- **Licensing a track**: the honest commercial move is a licensed instrumental or a commissioned
  cue from a Ugandan Gen Z producer or artist working in the amapiano/dancehall/kidandali
  crossover lane (the type of act that fills Kampala's Friday line-ups), cleared through their
  management. No artist has been approached or has agreed to anything; this note only describes
  the type of act the brief calls for.
- **Narration**: a Ugandan voice actor replacing `speechSynthesis`, mixed against the ducked bed.

## Honest limits of the synthesis

- Karplus-Strong plucks were tried and dropped: WebAudio clamps any feedback DelayNode to one
  render quantum (128 samples ≈ 2.9 ms), so the string model cannot sound above ~340 Hz — below
  the theme's register. The pluck is therefore an enveloped oscillator, which is cleaner but
  less "stringy".
- Timbres are caricatures: the log drum has no distortion stage, the congas have no skin
  resonance, the hats are white noise. It reads correctly at showreel volume on laptop speakers;
  on a club system it will sound thin.
- Level changes happen on the next 16th, not on a bar line, so a cue() that lands mid-bar
  changes texture mid-phrase; risers and impacts are scheduled to the second, which is what the
  canvas needs. The drop is placed at absolute scene seconds, so if a scene's `dur` changes the
  program table in `LONG` must move with it.
- Everything runs through a glue compressor and a brick-wall stage with the output trimmed to
  0.38; the offline render peaks at 0.36 and sits around −19 dBFS RMS in the drops, quiet enough
  for the narration to sit on top without further ducking of the host `master`.
- Swing is a single global value; real amapiano drummers swing hats and shakers differently
  from the log drum, and push the log drum a few ms late — worth doing by ear with a producer.

(The three limits above describe v1; v2 below addresses the level, the swing and most of the
timbre points. The Karplus-Strong limit still stands.)

## v2 — what changed, and why it reads less robotic

Client note on v1: *"the sound is an extra layer of roboticness; something else that speaks to
Gen Z, millennials and young professionals would be helpful."* v2 keeps the public API
(`create / play / cue / stop / duck / tick`), the tempo, key, patterns and every hit time in the
programs (UG lock 10.6 / 8.4 s, Stage drop 30 s into Pool / 49.75 s, Atlas lift 16.3 s into
Atlas / 64.9 s, final hits 12.4 s into Close / 83.8 s), and rebuilds the sound around them.
The real-track path (a produced cue, ElevenLabs or a commissioned Kampala producer) is in
`music/BRIEF.md`; the pages and `build-video.js` prefer `music/<cut>.mp3` when it exists. The
file is 28.8 KB.

**Nothing is on the grid any more.** v1 played every hit at the same velocity on a 16th grid with
one swing value — the definition of a drum machine. v2 (`H()`, `V()`, `SWING`, `SHKSW`, `rr()`
at the top of `ug-score.js`):

- every hit is offset by a seeded random ±2–8 ms (kick tightest at ±2.5, claps and the ad-lib
  loosest at ±4–8); the log drum is pushed 5 ms late on top of that, the way producers nudge it;
- velocities jitter 4–15 % around accent patterns; the shaker accent cycle alternates per bar
  (`SHK`) and lifts into every fourth bar; ghost hats sit at 30 % ± 30 %;
- swing is a curve per 16th, not a number: 0 / 17 / 2 / 14 % of a 16th for the kit, 0 / 23 / 5 /
  19 % for the shakers, so the "e" and "a" push differently from the "and";
- round-robin timbres: each voice cycles 3–4 variants (kick pitch 158/168/178 Hz, hat sizzle
  7.4/8.0/8.7 kHz, clap count 4–5 and burst spacing 7–13 ms randomised, clave ±1.2 % pitch, conga
  ±3 %, shaker band 5.8–7.2 kHz), and every noise burst plays back at 0.9–1.1× rate.

**A kit, not noise bursts.** Kick = sine body sweeping to 44 Hz + a triangle beater click + a
3 kHz "air" burst. Clap = four or five bandpassed bursts at irregular spacing plus a longer
roomy burst sent to the plate. Hats decay with velocity (12–72 ms), open hat on the "and" of 4
on the drops. A rimshot (sine 790–860 Hz + 3.6 kHz snap) on the "a" of 2 and 4. Shaker on its
own swing curve, accented hits get the second "shh"; shekere as before; congas panned across
the field. The drum bus runs through a light tanh (drive 1.25).

**The log drum has weight.** Sine with a 2.4× pitch drop plus a triangle 2nd harmonic, driven
hot into a tanh waveshaper (drive 2.4) and then lowpassed at 400 Hz — the saturation is what
puts it on a phone speaker. Each log hit dips the pad + Rhodes bus by up to 28 % for 170 ms
(`G.pump`), and every kick dips the whole harmonic bus to .34 (.26 on the four-on-the-floor
drops) — two sidechains, the way an amapiano mix pumps.

**Chords move and sound like an instrument.** The raw-saw pad is gone. The bed is a
Rhodes-style FM electric piano (`epNote`: sine carrier, 1:1 modulator with a velocity-shaped
index that decays over 140 ms for the bark, a 7:1 tine that dies in 30 ms, 4.3 Hz tremolo on
the bus, 7 ms strum, notes spread across the stereo field). It comps whole-bar chords in
`pad` / `break` / `outro` and syncopated stabs (1, "and" of 2, "a" of 3, "and" of 4, with odd-bar
variations) in the groove. Each chord has two voicings (`VOIC`) that alternate every four bars,
so the top line moves by step: Am7 (A E G C E → E A C E G), Fmaj7 (F C F A E → F A C E A),
Cmaj7 (C G B E G → E G B D E), G(add9) (G D A B D → B D G B D). A dark pad (triangles + sub,
420 Hz lowpass with a slow LFO) sits under it. The supersaw (six saws at ±19 cents, panned)
exists only on the drops: its filter opens from 500 to 2400 Hz when a `drop` level arrives.

**Call and response.** Bars 1–2 of every four-bar phrase are the pluck motif (the UG theme on
the clave). Bars 3–4 answer an octave up — except on the drops, where the answer is a
vocal-like "hey" (`adlib`: a breath burst, then a sawtooth through three formant bandpasses
gliding 560→400 / 1800→2200 / 2600→2800 Hz, pitch falling 10 % over 130 ms, ±4 % pitch
jitter, on the positions in `ADL`). One "hey" also marks each drop impact and the final hit.

**Space.** A plate-style convolution (18 ms pre-delay, 2.1 s, bright early reflections darkening
along the tail, highpassed at 260 Hz on return) on claps, Rhodes, the ad-lib, pluck, lead and
supersaw; a tempo-synced dotted-8th delay (395 ms, 36 % feedback, lowpassed 2.6 kHz, panned
right) on the pluck, lead, skank and ad-lib.

**Bus.** mix → glue compressor (−12 dB, 2:1, knee 10, 15 / 250 ms) → makeup → limiter (−2 dB,
8:1, 2 / 80 ms) → tanh soft-clip (1.4) → trim .7. Measured on the short cut, post-chain (RMS,
left channel): intro −17.4 dBFS, groove −13.2, breakdown −19.2, drop −12.3, peaks ≤ .70 — a
7 dB range between the breakdown and the drop, which is what a listener hears as "dynamics".
v1 sat at −19 dBFS with peaks .36 everywhere. Lesson recorded for next time: the first v2 pass
came out at −9.4 dBFS in *every* section because WebAudio's `DynamicsCompressorNode` applies
automatic makeup gain, so a low threshold plus a hard limiter flattens everything; the fix was
measuring each bus solo pre-dynamics (scratch tool `diag.js`), balancing there (log drum ~2 dB
over the kit, ad-lib ×2.4, reverb/delay returns up), then setting the glue at −12 dB / 2:1.

**Arrangement.** Every riser now carries a fill: the rising bandpass sweep and clap roll from
v1, plus a reverse-noise swell that cuts dead on the hit, an 8-hit rim roll over the last two
beats and three falling toms (200 / 160 / 125 Hz). A new `break` level (Rhodes + shaker + the
half-speed theme) opens Pool in the long cut (0–8.4 s) and sits at 34.75–41.05 s in the short
cut, so both drops arrive out of a hole. The final hit is preceded by a 1.9 s reverse-noise
riser, scheduled ahead of the `fin` entry (`pre[]` in `fireOnce`), and the finale adds a full
Rhodes chord and a "hey". Program edits are level changes only — one entry renamed and one
added per cut; no hit time moved.

**Testing** (`scratchpad/sound/test-score.js`, Playwright + headless Chromium, the same
OfflineAudioContext + suspend/resume-every-50-ms pattern as `build-video.js`, `cue(i)` at the
twelve scene offsets on the long cut): both cuts render without exceptions (long 275 s in 72 s,
short 86 s in 20 s), every section has non-zero RMS (long cut −12.7 to −14.7 dBFS per scene,
peak .73; short cut −12.7 to −14.7 per section, peak .72; per-scene figures average several
levels, the 7 dB range above is per level), peaks below .98; a 20 s WAV of the short cut's
Stage drop (44–64 s) is written for listening.

**What is still synthesis.** The "hey" is a formant caricature, not a voice; the Rhodes has no
key noise; the congas have no skin. It now reads as a produced beat at showreel volume on
laptop and phone speakers, which is what the fallback has to do. For the real thing, follow
`music/BRIEF.md`.
