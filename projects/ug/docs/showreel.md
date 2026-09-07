# The showreel

Four cuts from one source, and four downloadable films.

| Cut | File | Length | What plays |
| --- | --- | --- | --- |
| Long, silent | `showreel/index.html` | 4:35, twelve scenes | Captions only. Auto-plays. |
| Long, with sound | `showreel/sound.html` | 4:35 | The generative score, narration, captions. |
| Short, silent | `showreel/short.html` | 1:26, five scenes | Opening, the desk, the Virtual Stage, the Atlas, one link. |
| Short, with sound | `showreel/short-sound.html` | 1:26 | Score with one drop on the UG lock and one in the Stage. |

`index.html` is the source; `node build.js` writes the other three (they differ by two constants).
`index.html?cut=short&sound=1` plays any combination from the one file.

## The voice

The founder's note on the first sound cut: robotic, not Ugandan. It was the browser's built-in
speech synthesis. The fix has two halves:

1. **Rendered Ugandan voices.** `voice/lines.json` is the narration master (Ugandan English
   register, two lines in Swahili and Luganda). `voice/render.py` renders every line with Sunbird
   AI's open Spark-TTS SALT model (Kampala non-profit; Ugandan-accented English plus six local
   languages, studio speakers), following the SALT repository's own inference notebook, which was
   cloned and read. The showreel fetches `voice/manifest.json` at start and plays the files when
   they exist. They are not in the repo yet because Hugging Face is blocked from the build
   sandbox; rendering is one command on a laptop or Colab, documented in `voice/README.md`.
2. **A labelled fallback.** Until then the sound cuts use the browser voice, preferring an
   African English voice where the browser has one (Edge ships Kenyan, Tanzanian, Nigerian and
   South African English), and the HUD says "placeholder voice" so nobody mistakes it for the
   product's voice.

## The voice-over, with ElevenLabs

The founder's second note: the browser voice is still robotic and not Ugandan, and a voice-over
is tonality and story, not just words. The voice team's answer lives in `voice/`:

- `DIRECTION.md`: the story arc (problem, promise, proof, invitation), per-scene tonality, pace
  and breath, casting (a Ugandan English voice with Luganda-inflected warmth), three ways to
  obtain it in ElevenLabs ranked by quality, and a five-point listening checklist for choosing
  between candidates.
- `lines.v2.json`: the voice-over script with Eleven v3 audio tags and per-line settings.
- `render-elevenlabs.py`: renders every line through the ElevenLabs text-to-speech API and writes
  the same `manifest.json` the reel and the video builder consume. Needs `ELEVENLABS_API_KEY`
  and a voice id; run it where ElevenLabs is reachable.

ElevenLabs is **not reachable from this build sandbox**: there is no connector or key in the
session and the API host is blocked by the egress proxy, so nothing here was rendered or
auditioned. The contract the script follows was read first-hand from ElevenLabs' own skills
repository (`elevenlabs/skills` on GitHub: `text-to-speech/SKILL.md`,
`text-to-speech/references/voice-settings.md`, `music/references/api_reference.md`); voice
library contents come from search snippets only. The ElevenLabs connector in the claude.ai
directory manages voice agents, not text-to-speech, so the render is a script, not a tool call.

## The music

A panel of three (a Kampala amapiano and kidandali producer, a film composer, a WebAudio
engineer) designed the score; `SCORE.md` is their cue sheet and design note. It is synthesised
in the browser by `ug-score.js`: 114 BPM, a log drum on the "and" of two under a sidechained bus,
shakers in swung sixteenths, a 3-2 son clave, congas, an off-beat guitar skank for the
kidandali chop, a pentatonic "UG theme" pluck written on the clave positions, an endingidi-style
lead, a pad and risers. The long cut has a program per scene and hits the UG lock and the Stage
drop where the canvas draws them; the short cut is one 86-second piece with two lifts. The music
ducks 8 dB under narration.

What a real production replaces: sampled engalabi and congas, a session guitarist, real adungu
and endingidi players, or a licensed cue from a Ugandan Gen Z producer (nobody has been
approached; no artist is implied).

The founder's second note called the synth bed "an extra layer of roboticness". The music team's
answer is in `music/`: `BRIEF.md` (the sound for Gen Z, millennials and young professionals,
licensing options, ElevenLabs Music prompts and composition plans with the UG lock, the Stage
drop and the Atlas lift at their timestamps, a mastering spec) and `generate-elevenlabs.py`,
which writes `music/long.mp3` and `music/short.mp3`. When those files exist the reel plays them
instead of the score and the video builder muxes them in. The in-browser score was also rewritten
(v2 in `SCORE.md`) with humanised timing, layered drums, a Rhodes-style electric piano, sidechain,
reverb and delay, so the fallback is far less mechanical.

## The films

`node build-video.js` renders the cuts to MP4 through headless Chromium, frame by frame, with the
same engine rendering the score offline, and muxes them with ffmpeg:

| File | Contains |
| --- | --- |
| `dist/ug-showreel-long-silent.mp4` | 4:35, captions, no audio track |
| `dist/ug-showreel-long-sound.mp4` | 4:35, score; narration mixes in once `voice/` is rendered |
| `dist/ug-showreel-short-silent.mp4` | 1:26, captions |
| `dist/ug-showreel-short-sound.mp4` | 1:26, score |

The browser's placeholder voice cannot be captured to a file, so the films carry the music and
the captions until the Ugandan voice files exist; the build script mixes `voice/*.wav` in at
each scene's start with the music ducked under it, with no code change. Video files are not
committed; they are built artefacts and are delivered alongside the repo.

## Provenance

Read first-hand: `SunbirdAI/salt` (the inference notebook and its speaker ids). From search
snippets only: the Hugging Face model cards for `Sunbird/spark-tts-salt`, `sunbird-lug-tts` and
USOAL's Orpheus fine-tunes, and the 2025–2026 Kampala charts (kidandali, Lugaflow, Ugandan
dancehall and Afro-pop, amapiano crossing over) that shaped the musical brief. Where the notebook
and the model card disagree (the English speaker id), the model card is authoritative and
`lines.json` waits for it rather than guessing.
