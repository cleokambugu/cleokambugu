# Languages: language justice in UG

Language justice is UG's marketing strategy as much as its ethic: a person should feel seen and
expected the moment they arrive. So the **first thing anyone touches is their language** — the
welcome screen is a turnable 3D ring of languages (a flat grouped list under reduced motion),
and choosing one answers back: *Welcome to Uganda* in that language, echoed in Luganda and
Swahili, before the map assembles. The choice is remembered on the device and, when signed in,
on the account; it can be changed any time from the nav, from Me, or by reopening the welcome
screen.

## The languages

**41 languages. 247 of 262 strings in every one of them.** Every string a person taps or reads in
the ordinary run of the app — the verbs, the doors, headings, sections, buttons, modals, and the
strings the JavaScript renders — exists in all 41 languages in `data/i18n/<code>.json`, assembled
into the site by `server/scripts/i18n-build.cjs`. Run the build: it prints coverage per language
and flags any translation whose inline markup does not match the English.

The fifteen that are still English are the Quality section's long method paragraphs. They are the
deepest prose in the app and the least likely to be read on a phone; the full method is in
[quality.md](quality.md) either way. They are the next batch, and the build will keep saying 247
until they are done rather than rounding up.

An earlier version of this page said "243 keys each" while five dictionaries held 35 of them, so a
reader who chose Zulu, Lingala, Somali, Hausa or Kinyarwanda got a page that was mostly English
under a heading about language justice. Those five were finished, along with Rukonzo, before this
sentence was allowed to change.

| Group | Languages |
| --- | --- |
| Uganda · Central | Luganda |
| Uganda · East | Lusoga, Lumasaba (Lugisu), Lugwere, Lusamia, Ateso, Kupsabiny (Sebei) |
| Uganda · North | Acholi, Lango, Kumam, Ngakarimojong |
| Uganda · West Nile | Alur, Lugbara, Ma'di, Kakwa |
| Uganda · West | Runyankore, Rukiga, Rutooro, Runyoro, Rukonzo |
| East Africa · Africa | Swahili, Kinyarwanda, Somali, Amharic, Arabic (RTL), Lingala, Hausa, isiZulu |
| World | English, French, German, Italian, Spanish (Spain and Mexico), Portuguese (Portugal and Brazil), Russian, Chinese (Simplified), Japanese, Korean, Hindi |

## Status, and why it is not a grade

Every language is **in service**, with a version and a date. There is no ladder of draft, reviewed
and complete any more, and the word *draft* does not appear in the product.

That is not a relabelling exercise. Twenty-six languages were carrying a "draft" label while
already holding every string — the label had simply never been updated. Six really were
incomplete; they were finished. What was left was a framing problem: describing a language by what
it lacks is the wrong model for a translation, which is a living thing in every product that has
ever shipped one and does not need apologising for.

What replaces it is provenance and a correction path, which is what a reader actually needs:

- **Who wrote it.** UG, not first-language speakers. Every dictionary says so in its
  `translator_note`, along with the register aimed at and any construction we are unsure of.
- **How to fix it.** *Suggest a better word* is in Me, in every language, and takes three fields:
  the word we used, the word you would use, where you saw it. A correction from somebody who
  speaks the language outranks anything UG wrote.

The African group exists so a traveller from Kigali, Addis, Khartoum, Kinshasa, Kano or Durban
lands in a language of theirs; the world group is for visitors who do not read English. Arabic
sets `dir="rtl"` on the whole document.

## What the build will not let us get away with

Every dictionary was written and then re-read in a second grammar-and-agreement pass — the
fact-check that can be done in software — and a second pass is not a native speaker's sign-off.
So each file carries a `translator_note` saying who wrote it and in what register, and an
`uncertain` list naming the source terms the writer could not settle: mostly product words with
no word in the language yet (plug-in, endpoint, sandbox, escrow), and in some files a
construction — a perfective passive, an imperative shape — that a first-language speaker should
rule on. Fourteen files carry one. Where a string is missing or its markup did not survive
translation, the app shows English rather than a guess. Me carries "Review this language"; the
dictionary is one JSON file and a review is a pull request.

Three failures had already shipped before `i18n-build.cjs` was taught to look for them, so it now
refuses to be quiet about any of the three:

- **Orphans.** A key can live in forty dictionaries and not in `en.json`, and the build takes its
  key list from `en.json` alone — so the key is silently dropped and `t()` returns the key name.
  That is exactly what happened: the hero's four flip lines were translated into forty languages
  and the English hero rendered the literal string `flipDeliver`. Eight more orphans were found
  the moment the check existed. The build now names them and exits non-zero.
- **Drift.** English is the source. When an English string is edited, its forty translations do
  not move and nothing notices — 10,414 cells with no owner. `data/i18n/.sources.json` holds the
  hash of every English string as of the last accepted build; any key whose English has changed
  since is named, and the build exits non-zero until `--accept` records that the translations
  have caught up.
- **Dead keys.** A key nothing in the site asks for is forty translations of nothing. The build
  scans the site for every `data-i18n` attribute and `t('…')` lookup and lists what is unclaimed.

## The pipeline

1. `server/scripts/i18n-extract.py` marks every translatable element in `site/index.html`
   (idempotent) and writes the source strings to `data/i18n/en.json`.
2. Translators edit one `data/i18n/<code>.json` each; the schema carries name, native name,
   region, family, script, direction, confidence, a translator note, and `uncertain` — the list
   of source terms and constructions the writer wants a first-language speaker to rule on.
3. `node server/scripts/i18n-build.cjs` validates every file (all keys present, HTML tags
   intact), rewrites the generated LANGS and STR block in the site, and exports
   `data/languages.json`. Bad strings are dropped to the English fallback, never shipped broken.

## Voice

Sunbird AI's open Spark-TTS SALT model speaks seven of these languages (Ugandan English,
Luganda, Runyankore, Acholi, Ateso, Lugbara, Swahili); the showreel's voice pipeline
(`showreel/voice/`) uses it, and the same route can read the app aloud in v2.

## What a review needs

A native speaker reads their file top to bottom, fixes what is wrong, deletes from `uncertain`
whatever they have now settled, and adds their name to `review_note` if they wish to be credited.
There is no grade to raise: the language was already in service, and the review makes it better.
Ten minutes with the welcome line, the four verbs, the doors and the money strings is already a
meaningful review; the welcome greeting is the single most important string in the file.
