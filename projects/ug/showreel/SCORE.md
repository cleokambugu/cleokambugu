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
| 3 | Pool, virtual stage (40 s) | The seats fill, the price falls: build; riser at 27.8 s; **the drop at 30 s** when UG manufactures the trip | `groove` → `full` @19 → riser → `drop` @30 | A |
| 4 | Drive / offers (25 s) | Driver's side; keeps the drop's energy without the lead | `full` | A |
| 5 | Rent and Signature (20 s) | Premium: skank off, endingidi-style lead carries the theme over the fleet | `groove`, lead on, skank off | A |
| 6 | Deliver (20 s) | The parcel: hand percussion heavier (congas ×1.3) | `full` | A |
| 7 | The Atlas, air/water/rail (30 s) | Lift: modulate up to B; second riser; drop with lead as the atlas opens | `groove` → `full` → riser → `drop` @16.3 | B |
| 8 | Explore / foresight (20 s) | Reflective; lead over sparse bed, then groove | `sparse`+lead → `groove` | B |
| 9 | Plug-ins / languages (20 s) | Back home to A; pluck call-and-response | `groove` | A |
| 10 | Stay on UG / teleport (15 s) | Full tilt into the close | `full` | A |
| 11 | One link / close (15 s) | Drums out at 8 s, pad + theme + lead; **final hit at 12.4 s** (log drum, pluck chord, shekere, boom) under the crest | `groove` → `outro` → fin | A |

## Cue sheet — short cut (60 s, one drop)

0 s pad + solo theme → 5 s `sparse` (clave, shaker, soft log) → 11.6 s riser (2.4 s, clap roll
accelerating) → **14 s impact + `drop`** → 40 s breakdown to `groove` → 50 s `outro` → 56 s final
hit → 60.5 s off. Verbs should land on the drop; the QR/install card on the final hit.

## Levels (what each layer set contains)

- `pad` — chord bed only (2 detuned saw pairs + sub sine through a slow-LFO lowpass), theme at half speed.
- `sparse` — + 3-2 clave, light shaker, shekere on the beats, log drum at 60%.
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
