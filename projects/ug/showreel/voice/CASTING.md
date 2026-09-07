# The voice bank: casting, session and direction

`ENGINES.md` establishes the technical position: the best open engines are Chinese, they are
excellent, and not one of them speaks a Ugandan language. The only model that does was built in
Kampala. And none of them — including the best — sounds like a person to a Ugandan ear.

So the primary voice is people. This is the plan for recording them, written so it can be handed
to a producer and executed without further instruction.

## Why this is the answer and not a fallback

Presence is not an accent. Cloning can carry an accent. What it cannot carry is what a listener is
actually responding to: the breath taken before a hard number, the smile you can hear on
*tugende*, the half-beat of hesitation that says the speaker is thinking rather than reciting, the
weight that lands on **one** word in a sentence because the speaker knows which word matters.

Those are performance decisions. A performer makes them. This is the same logic the rest of UG
runs on — the operationally hard answer usually beats the clever one — and it is the reason to do
it rather than an excuse for the cost.

## The cast

Fourteen lines of narration, five scenes. One voice carries the film; two others carry the
language versions. Cast for **warmth and authority together**: someone you would believe if they
told you a price.

| | Who | Register | Carries |
|---|---|---|---|
| **Lead** | Ugandan woman, 30s–40s, Kampala English with a Luganda first language | Warm, unhurried, dry humour held back. Not a radio-advert voice; a voice that has been in traffic. | English (Ugandan), Luganda |
| **Second** | Ugandan man, 40s–50s, Runyankore or Rutooro first language | Steadier, lower, the one who explains the money. | English, Runyankore, Rutooro |
| **Third** | Northern Ugandan, Acholi or Lugbara first language, any gender | Lighter, quicker, the corridor voice. | Acholi, Lugbara, Alur, Swahili |

Where to find them: Uganda's radio and voiceover scene is deep — Kampala station presenters, the
theatre companies at the National Theatre, the actors Sunbird themselves recorded for the SALT
corpus. Ask the Uganda Communications Commission's registered production houses. Budget UGX
300,000–600,000 per artist per half-day session at 2026 Kampala rates; more for a broadcast name,
and pay it rather than negotiating, because the whole point of this file is that we are buying
something a machine cannot give us.

**Consent and rights.** A written release per artist covering: the reel, the app, and any future
UG product; a named credit in the app; the right to withdraw the voice from *future* renders with
90 days' notice; and an explicit clause that **the recordings will not be used to train or clone a
synthetic voice**. That last one is not boilerplate. It is the difference between hiring a person
and harvesting one, and a product whose entire argument is about keeping promises cannot get it
wrong.

## The session

Half a day per artist. Quiet room, not a booth if a booth makes them formal — a carpeted office
with the air conditioning off is better than a dead booth with a nervous reader.

- **Microphone**: any large-diaphragm condenser at 20–30 cm, slightly off-axis to keep the
  plosives out. A Rode NT1 or an AT2035 into any interface is enough. 48 kHz, 24-bit, WAV.
- **Room**: soft. A duvet on a stand behind the reader beats an untreated "studio".
- **No compression, no EQ, no gate on the way in.** Capture flat; decide later.
- **Three takes of every line, minimum**, and one where they say it to a friend instead of to a
  microphone. That last one is usually the one you use.
- **Record the room tone** for thirty seconds. It is what makes the edit sound like a place.
- Keep the breaths. Cutting every breath out is the single most common way a human read starts
  sounding synthetic.

## Direction, line by line

The full script is in `lines.v2.json`. The intent behind each is in `DIRECTION.md`. What follows
is what to say to the artist in the room.

| Scene | Line | Direction |
|---|---|---|
| Opening | *UG. Ride. Pool. Rent. Deliver.* | Four words, four separate thoughts. Not a list. Land on each and let a beat fall between them. |
| Opening | *One app for every way to move in Uganda. Tugende.* | *Tugende* is not a tagline, it is what you say to a friend when you are both ready to leave. Throw it away. |
| Problem | *In Kampala we check three apps before every trip, and still ask the boda man.* | This is the laugh line. It is funny because it is true and everyone listening has done it. Do not push it — the recognition does the work. |
| Ride | *Every quote, ranked by price, and it tells you which ones are estimates.* | Flat, factual, slightly faster. This is the honest sentence; do not sell it. |
| Ride | *The button is always Book on UG. Nobody sends you away.* | **This line is now false and must not be recorded.** See below. |
| Pool | *You pay for your seat first, and the price drops as the car fills.* | Lean on *drops*. It is the whole product in one verb. |
| Pool | *When the money is in, UG makes the trip.* | Slower. Something is being built here. |
| Rent | *Rent a Prado for the weekend and split it four ways.* | The sound of a plan being made. Slight lift on *four ways*. |
| Deliver | *A quarter of a seat. That is it.* | Two beats, then stop. The pause after is the line. |
| Atlas | *Air, bus, water, rail, Signature, stays. One table.* | Six items, even pace, no crescendo. Then *One table* lands. |
| Explore | *East African citizens pay East African prices.* | The proudest line in the film. Do not smile through it; let it be a statement of fact and let the listener feel it. |
| Rail | *Hakuna anayetumwa mbali. Twende.* | Swahili, and it should sound like Swahili — not English with Swahili words in it. |
| Link | *Install it. Same crest, same account, same shillings.* | Practical. A person telling you how, not a brand telling you why. |
| Link | *UG. Weebale. Tugende.* | *Weebale* — thank you — carries the whole film out. Warm, quiet, done. |

### One line must change before it is recorded

*"The button is always Book on UG. Nobody sends you away."*

That stopped being true in this build. UG now takes payment only for its own seats and cars;
every other row shows the fare and opens the operator's app, because there is no contract to place
those bookings. Recording the old line would put a false promise in a human voice, which is worse
than putting it in a synthetic one.

Replace with: ***"Every fare on one screen, and we tell you which ones we can book."***

## The cascade, and what each recording is worth

`manifest.json` lists what exists. The player checks in this order and says on screen which it is
using:

1. `bank/<lang>/<scene>-<n>.wav` — a named human. **This is the product.**
2. `rendered/` — Sunbird Spark-TTS SALT, for Ugandan languages nobody has recorded yet.
3. `cloned/` — Chatterbox Multilingual from a Ugandan reference clip, for Swahili and the gaps.
4. `visitors/` — CosyVoice 2, for Chinese, Japanese, Korean and the European languages.
5. Browser speech synthesis, labelled on screen as a placeholder, because it is one.

Record English and Luganda first: they cover most of the audience and they are the two the lead
can do in one session. Everything else can wait behind a model that says so.

## What this costs, plainly

Three artists, half a day each, one edit day: roughly **UGX 2.5–3.5m** all in at 2026 Kampala
rates, plus the room. Against the alternative — a free model that produces something every
Ugandan listener will identify as a machine inside two sentences, on a product whose argument is
that it is not pretending — that is not an expensive answer. It is the only one.
