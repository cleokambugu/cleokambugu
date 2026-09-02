# Voice direction for the UG showreel

Client note: "not Ugandan, still robotic; speech is tonality, a story of what this solves."
Script: `lines.v2.json`. Renderer: `render-elevenlabs.py`.

Provenance. **(first-hand)**: ElevenLabs' own skills repo, `elevenlabs/skills` commit `44a05ea`,
`text-to-speech/SKILL.md` and `text-to-speech/references/voice-settings.md`. **(snippet)**:
search snippets of ElevenLabs docs, which this sandbox cannot open. **(assumed)**: our working
assumption, to check with an API key. Where they disagree, both are stated
and the repo is authoritative.

## The story

The long cut (4:35, twelve scenes) is one argument in four movements. The narrator is the
friend at the function who already knows the smart price, not an announcer.

| Movement | Scenes | What the voice is doing |
| --- | --- | --- |
| **Problem** | opening, problem | Naming the evening everyone knows: three apps, still asking the boda man. Amused, never mocking. |
| **Promise** | ride, pool, drive | Turning the corner. Pool is the idea UG owns, and the voice leans in. |
| **Proof** | rent, deliver, atlas, explore, plugins | Showing it in real shillings. Matter-of-fact, unembarrassed about money. |
| **Invitation** | rail, link | Slowing, warming, landing the positioning line, goodbye in Luganda. |

The short cut (1:26) keeps the four beats: problem in opening, promise in ride, the owned idea
in pool, breadth in atlas, invitation in link. Lines are shared, so those scenes are written
to the **short** durations (opening 16 s, ride and atlas 18.75 s, pool 20 s, link 12.5 s).

## Scene by scene

Ugandan English runs 2.0 to 2.3 words a second; lines are budgeted near 1.8, and the score
ducks 8 dB under the voice, so nobody pushes: a pushed read is what sounds robotic. "Breathe"
is a full stop or `[pause]` on v3, never a comma.

| Scene | Tonality | Pace | Breathe | The listener feels |
| --- | --- | --- | --- | --- |
| opening | Low, calm; the four verbs as four full stops, not a list | slow | after "Kampala." and before "UG." | "My city; someone is about to say what I already know." |
| problem | Wry recognition; "banange" a shared sigh, not a complaint | medium | after "boda man." | Seen, without blame. |
| ride | Turns the corner; steady on "Book on UG" | medium | before "The button" | Relief: one screen, nobody sends me away. |
| pool | Lean in; pride in "ours"; lift on "drops"; "Twende" a full stop | medium, slower last line | before "Money in" | "Ah, this is the clever one." |
| drive | To drivers directly, respectful, no hype | medium | after "Once." | Dignity: I choose; the money is already there. |
| rent | A real Saturday; arithmetic like a friend splitting a bill | quick on the numbers | before "Or the Signature" | Aspiration without shame. |
| deliver | Plain, amused at how small the number is | medium | after "Jinja." | "That is it?" |
| atlas | Even list rhythm; firm on "Nothing faked" | steady | before "Four honest states" | Trust: everything on the table, labelled. |
| explore | Warm on "The Pearl", pointed on the two permit prices | medium | before "East African citizens" | Pride, and a fair deal. |
| plugins | Brisk, four beats matching the four captions | quicker | between products | Delight: it plugs into what I use. |
| rail | Slow, resolved; the Swahili line a promise, not a slogan | slow | before "Hakuna" | Safe: whatever I book finishes here. |
| link | Warmest read; positioning line, then goodbye | slow, final | before "Look the part" and "UG." | Invited, thanked, ready to install. |

## Casting

**Who.** A Ugandan, late twenties to mid-thirties, from Kampala: the young professional the
app is for. Gender open; audition one of each. Ugandan English with Luganda underneath: open
vowels, even syllable timing, a melody that rises through a thought and settles at the full
stop, unhurried consonants, light "r", final syllables fully voiced. Radio-literate (a Capital
FM or Sanyu evening presenter), not a newsreader. Not a generic "African accent": not
Nigerian, South African or Nairobi Sheng. "Tugende", "Weebale", "boda", "Jinja", "kwanjula"
must land as Kampala says them.

**Three ways to get it, best first.**

1. **A Ugandan voice actor, cloned with consent.** Cast a real actor; pay a session and a
   licence that names synthetic use. Record 30+ minutes of clean studio read, including every
   line of `lines.v2.json` and a page of Luganda and Swahili words, then make a Professional
   Voice Clone. Needs Creator plan or above, and the actor must pass the spoken voice captcha
   in person **(snippet)**. That session also yields the 34 lines read for real, which beats
   any render; the clone is for iterating afterwards.
2. **A Voice Library voice with East African English.** Search, in order: "Ugandan", "Uganda", "Kampala", "East African", "Kenyan", "Swahili", "African
   English". The library API filters by `search`, `accent`, `language`, `gender`, `age`
   **(snippet)**; whether "ugandan" exists as an accent value is **(assumed)**, so search
   free text too. Snippets showed Malawian and Nigerian voices, no confirmed Ugandan one;
   expect to shortlist Kenyan or Tanzanian English. `render-elevenlabs.py --search-library
   "Ugandan"` prints candidates.
3. **Voice Design from a prompt.** Model `eleven_ttv_v3`, preview text 100 to 1000
   characters, three previews per generation **(snippet)**. The full prompt and the preview
   text (the opening and ride lines, so candidates are judged on the actual script) are in
   `lines.v2.json` under `elevenlabs.voice_design_prompt` and `voice_design_preview_text`.

**Settings.** Model `eleven_v3`, fallback `eleven_multilingual_v2` (ignores tags); stability
0.0 to 1.0, lower means more range; `speed` 0.25 to 4.0; `language_code` honoured on v3 with
unknown codes ignored; `previous_text`/`next_text` stitching; output `mp3_44100_128` — all
**(first-hand)**. We sit at stability 0.5, 0.0 for the pool opener and the link close, speed
1.0, pacing with punctuation and `[pause]`. Contradiction: the repo's v3 example sends
`similarity_boost` and `use_speaker_boost` **(first-hand)**; a product-guide snippet says v3
has neither. The script follows the repo. Tags `[excited]`, `[calm]`, `[whispers]`, `[laughs]`,
`[sigh]`, `[pause]`, `[rushed]`, `[drawn out]` are documented **(snippet)**; `[warm]` is
**(assumed)**, so if a take ignores it, use `[calm]`. Swahili is a v3 language, Luganda was not
visible **(snippet)**: the same voice speaks the Luganda line; if "Weebale" misfires, respell
it in `text_v3` only. Details and every uncertain field: the `*_note` keys in `lines.v2.json`.

**Review checklist: five listening tests, scored 1 to 5, on a phone speaker.**

1. **Place test.** Play the problem scene cold to three Kampala listeners. Do they place the
   voice in Uganda before "boda man"? "Nigerian?" or "South African?" fails.
2. **Money test.** The rent arithmetic: a friend splitting a bill, or a bank reading terms?
   No sales lift on the number.
3. **Turn test.** Pool: the smile on "ours", the plain "Money in", the landed "Twende", in
   one take with no seams.
4. **Same-room test.** Opening and link back to back: same person, same room, same mic
   distance? If it drifts, raise stability.
5. **Duck test.** Under the score at minus 8 dB: every word intelligible, nothing pushed.
   Tie-break: does it breathe before "UG."?
