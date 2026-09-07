# The voice: what actually exists, read first-hand

The brief was blunt: the narration sounds like a machine, it does not sound Ugandan, find an open
ElevenLabs equivalent or something better from the Eastern market, and make it human.

I cloned the five strongest candidates and read their code and licences rather than their
marketing. Here is what that settles, including the part that is not what anyone hoped.

## What was read, and how

`git clone --depth 1` of each repo, then the README, the licence file and the inference example.
No claim below comes from a search snippet; where I have not verified something first-hand it says
so.

| Engine | Licence (read) | Languages (read) | Voice cloning | Verdict for UG |
|---|---|---|---|---|
| **Chatterbox Multilingual V3** · `resemble-ai/chatterbox` | MIT | 23: ar da de el en es fi fr he hi it ja ko ms nl no pl pt ru sv **sw** tr zh | yes, from a ~10s reference | **the best general answer.** MIT, and the only one of the five with an African language |
| **CosyVoice 2** · `FunAudioLLM/CosyVoice` | Apache-2.0 | 9: zh en ja ko de es fr it ru, plus 18+ Chinese dialects | yes, zero-shot + cross-lingual | superb, and speaks no African language at all |
| **IndexTTS 2** · `index-tts/index-tts` | bilibili Model Use Licence (not OSI) | zh en ja es ar | yes, with emotion/duration control | strong, but a bespoke licence and no African language |
| **F5-TTS** · `SWivid/F5-TTS` | MIT | en zh in the released checkpoints; more via community fine-tunes | yes | fast and clean, wrong languages |
| **Spark-TTS SALT** · `SunbirdAI/salt` | model on Hugging Face, code Apache-2.0 | **Luganda, Acholi, Ateso, Lugbara, Runyankore, Swahili, Ugandan English** | fixed studio speakers | **the right answer for Uganda** |
| **Kokoro-82M** · reported, not cloned | Apache-2.0 (reported) | 6: en-us en-gb fr-fr it ja cmn | no | **no Ugandan language.** Running today on the founder's machine; a candidate for part of tier 4 only |

## The finding nobody wants

**No open model — Eastern, Western or otherwise — speaks Uganda's languages, except one, and it
was built in Kampala.**

The Chinese engines are the most technically impressive of the five. CosyVoice 2's cross-lingual
zero-shot cloning is genuinely ahead of the field and it is Apache-2.0. IndexTTS 2's emotion
control is remarkable. Neither can say a sentence in Luganda, Ateso, Lugbara, Acholi, Runyankore,
Lusoga, Rukonzo or Alur — the languages this app actually speaks. Nor can F5-TTS. Chatterbox
carries exactly one African language out of twenty-three.

The exception is **Sunbird AI**, a non-profit lab in Kampala. Their SALT work includes a
text-to-speech corpus of about 5,000 sentences **read by professional voice actors in a studio**
in English (Ugandan accent), English (Kenyan accent), Swahili, Luganda, Acholi, Ateso, Lugbara and
Runyankore, and a paper describing the models built on it —
*Multilingual Model and Data Resources for Text-To-Speech in Ugandan Languages*, Owomugisha,
Akera, Mwebaze and Quinn, AfricaNLP 2023. `constants.py` in that repo carries about seventy
African language codes; the ones UG needs — `lug ach teo lgg nyn cgg koo laj alz nyo ttj gwr rub
lsm adh swa` — are nearly all there.

So the answer to "find something better from the Eastern market" is: the Eastern market has the
better *engine*, and Kampala has the only *voice*. For a Ugandan product that is not a close call.

## Kokoro-82M, offered mid-build — where it does and does not fit

**Provenance: secondhand.** A parallel session set this up on the founder's Windows machine and
reported it here. Nothing below was verified from this sandbox: the service listens on
`127.0.0.1:5211` of *that* machine and the files sit on `E:/AI/voice/`, neither of which a Linux
container in the cloud can reach. The figures — Apache-2.0, 54 voices, 82M parameters, CPU
real-time at RTF 1.07, a 274 KB WAV returned over HTTP — are that session's measurements, not
ours. No weights were cloned and no output was heard here.

Taken at face value it is a good piece of engineering and it is free, against ElevenLabs at
$22–330/month. It still does not move the thing this file is about.

**It cannot touch tiers 1–3.** Kokoro speaks English, French, Italian, Japanese and Mandarin. It
has no Luganda, no Swahili, no Acholi, Ateso, Lugbara, Runyankore, Lusoga, Rukonzo or Alur, and no
voice cloning to borrow an accent with — the offering session says as much itself. Its English is
American and British. A Ugandan product narrated in an American accent is the exact failure the
founder's brief named, so the cascade above is unchanged where it matters.

**It is a real candidate for part of tier 4.** The visitor languages are the one place an engine
that speaks no Ugandan language is still the right tool, and Kokoro covers four of those eight —
French, Italian, Japanese, Mandarin — leaving Korean, German, Spanish and Russian to CosyVoice 2.
Against CosyVoice 2 it trades quality and cross-lingual cloning for a much easier operation: it is
already running, on a CPU, at real time, under Apache-2.0, with no weights to fetch past a proxy
that blocks Hugging Face. For fixed strings — the trip-rail steps, pickup directions, the handful
of lines a visitor hears — pre-rendering those four languages on the founder's machine and
committing the WAVs is a cheaper path to tier 4 than standing up a GPU.

That is a decision for the founder, not a default. Nothing here is wired up: the client
(`E:/AI/voice/voice-client.js`, `voiceAvailable()` / `speak()` with a cloud fallback) lives on the
Windows machine and this repo has no code that calls it. It should stay that way until someone has
listened to Kokoro saying a UG line and judged it good enough to ship, because this file's own
rule is that nobody should take a quality ranking from someone who has not heard the output.

## The answer underneath the answer

None of this makes a machine sound human, and the brief asked for human.

Every engine here, including the best of them, produces speech that a Ugandan ear identifies as
synthetic inside a sentence or two — not because of the accent, which cloning can carry, but
because of what is missing: breath in the wrong places, no smile, no weight shift on the word that
matters, no hesitation before a number. Presence is performance, and performance is a person.

**So the primary voice for UG is recorded humans, and the models are the fallback.** That is not a
compromise; it is the same logic the rest of this product runs on. The operational answer usually
beats the clever one. Casting, session plan, direction and rates are in `CASTING.md`.

## The cascade the reel actually uses

In order. The first one that has audio for a line wins, and the player says on screen which one it
is playing.

1. **`bank/`** — recorded human takes, named artist, with a release on file. The real voice.
2. **`rendered/`** — Sunbird Spark-TTS SALT for Ugandan languages and Ugandan English
   (`render.py`, already written against the notebook's prompt format).
3. **`cloned/`** — Chatterbox Multilingual, cloned from a Ugandan reference clip, for Swahili and
   for languages Sunbird does not cover (`render-chatterbox.py`). Cloning from a Ugandan voice is
   what keeps the accent honest; without a reference the output is American.
4. **`visitors/`** — CosyVoice 2 for the visitor languages: Chinese, Japanese, Korean, French,
   German, Italian, Spanish, Russian. This is where the Eastern engines genuinely win, and it is
   worth using them there. Kokoro-82M covers four of those eight on a CPU with no GPU to stand up
   and may be the cheaper way to fill this tier — see the Kokoro section above; unheard, so
   undecided.
5. **Browser speech synthesis** — labelled on screen as a placeholder, because it is one.

## What could not be done in this sandbox

`huggingface.co` and `api.sunbird.ai` are blocked by the egress proxy here, so no weights could be
downloaded and no audio rendered. The scripts are written and runnable; they need a machine with
network access and a GPU, or Colab. Blocked hosts are reported, not bypassed.

Everything in the table above was read from cloned source, with one exception: the Kokoro row
is secondhand, reported by another session and unverifiable from here. The audio quality claims are the one
thing I have **not** verified first-hand — I could not listen to any of these models, and nobody
should take a quality ranking from someone who has not heard the output.
