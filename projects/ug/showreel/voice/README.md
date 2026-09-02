# The voice of the showreel

The founder's note: the narration sounded robotic and not Ugandan. It was the browser's built-in
speech synthesis, which has no Ugandan voice. This folder is the fix: a pipeline that renders the
narration with a free, open Ugandan text-to-speech model, and a showreel that plays those files
when they exist and says plainly when it is falling back.

## What was found, and how

Read first-hand (cloned `SunbirdAI/salt` from GitHub and read
`notebooks/evaluation/spark-tts-inference-example.ipynb`): the prompt format
`<|task_tts|><|start_content|>{speaker}: {text}<|end_content|><|start_global_token|>`, the codec
(`unsloth/Spark-TTS-0.5B` BiCodec), generation parameters, and the speaker ids the notebook
lists: 241 Acholi, 242 Ateso, 243 Runyankore, 245 Lugbara, 246 Swahili, 248 Luganda (all
studio speakers from the SALT corpus). `render.py` follows that notebook line for line.

From search snippets only (the pages themselves are blocked from this sandbox):

- `Sunbird/spark-tts-salt` on Hugging Face: Spark-TTS 0.5B fine-tuned for seven languages
  spoken in Uganda, including **English with a Ugandan accent**. Sunbird AI is a Kampala
  non-profit and the model is open. This is the engine `render.py` uses.
- `Sunbird/sunbird-lug-tts` and `sunbird-lug-tts-commonvoice-female`: earlier Luganda-only
  voices trained on Mozilla Common Voice.
- **USOAL** (Uganda Open Source AI Lab) publishes Orpheus-3B fine-tunes for English, Luganda,
  Runyankole, Teso and Acholi on Hugging Face, built on Sunbird, Yogera and Common Voice data.
  A second option if a different timbre is wanted; the render script would need its own prompt
  format (not read first-hand, so not implemented).
- Commercial options with African English voices exist (ElevenLabs, HeyGen and the like); the
  brief asked for free and local, so they are not used.

Contradiction to note: the notebook's speaker list has no English id, while the model card says
the model speaks Ugandan English. The model card is authoritative for the shipped checkpoint;
`lines.json` therefore leaves the English speaker id as `null` to be filled from the card before
rendering rather than guessing a number.

## Why the files are not in the repo yet

The sandbox's egress proxy blocks `huggingface.co` and `api.sunbird.ai` (probed: no response), so
the model cannot be downloaded here and the audio cannot be rendered here. Blocked hosts are
reported, not bypassed. Rendering takes one command on a laptop or a Colab GPU:

```
cd projects/ug/showreel/voice
git clone https://github.com/SparkAudio/Spark-TTS
pip install -U transformers torch torchaudio soundfile huggingface_hub omegaconf einx einops
python render.py --check     # lines.json matches sound.html
python render.py             # writes opening-1.wav ... link-2.wav and manifest.json
```

Commit the WAVs (about 25 short files, 16 kHz mono) and `manifest.json`; the showreel picks them
up with no code change. Until then the sound cut uses the browser voice, preferring an African
English voice where the browser offers one (Edge ships Kenyan, Tanzanian, Nigerian and South
African English neural voices; Chrome does not), and shows "placeholder voice" in the HUD.

## The lines

`lines.json` is the master. The register is Ugandan English: direct, warm, no slang for its own
sake, with a Luganda or Swahili word where a Kampala voice would use one ("Tugende", "Twende",
"Weebale"). Two lines are wholly in Swahili and Luganda so the local-language speakers are heard.
The same text lives in `sound.html` as the fallback; `render.py --check` fails if they drift.

## The music

Separate from the voice: `../ug-score.js` is the generative soundtrack designed by the sound
panel (see `../SCORE.md`). It is synthesised in the browser, so it needs no files and no network.
