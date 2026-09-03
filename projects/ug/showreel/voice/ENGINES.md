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
   worth using them there.
5. **Browser speech synthesis** — labelled on screen as a placeholder, because it is one.

## What could not be done in this sandbox

`huggingface.co` and `api.sunbird.ai` are blocked by the egress proxy here, so no weights could be
downloaded and no audio rendered. The scripts are written and runnable; they need a machine with
network access and a GPU, or Colab. Blocked hosts are reported, not bypassed.

Everything in the table above was read from cloned source. The audio quality claims are the one
thing I have **not** verified first-hand — I could not listen to any of these models, and nobody
should take a quality ranking from someone who has not heard the output.
