# Languages: language justice in UG

Language justice is UG's marketing strategy as much as its ethic: a person should feel seen and
expected the moment they arrive. So the **first thing anyone touches is their language** — the
welcome screen is a turnable 3D ring of languages (a flat grouped list under reduced motion),
and choosing one answers back: *Welcome to Uganda* in that language, echoed in Luganda and
Swahili, before the map assembles. The choice is remembered on the device and, when signed in,
on the account; it can be changed any time from the nav, from Me, or by reopening the welcome
screen.

## The languages

**41 languages, 245 keys each, complete.** Every string in the app — the verbs, the doors, headings,
sections, buttons, modals, and the strings the JavaScript renders — exists in every language in
`data/i18n/<code>.json` and is assembled into the site by `server/scripts/i18n-build.cjs`. Nothing
falls back to English any more. Run the build to check: it prints coverage per language and fails
loudly on a bad tag.

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

## The honest rule

A language card shows its confidence: **complete**, **reviewed**, **draft**, or **early
draft**. Every dictionary was drafted and then re-read in a second grammar-and-agreement pass by
the build's translation teams — that pass is the fact-check we can do in software — but a
machine's second pass is not a native speaker's sign-off, so every Ugandan language ships as
**draft** until a named speaker has reviewed it, and each file carries a `translator_note` and
an `uncertain` list naming the keys the translator flagged. Where a string is missing or its
markup did not survive translation, the app shows English rather than a guess. Me carries
"Review this language"; the dictionary is one JSON file and a review is a pull request.

## The pipeline

1. `server/scripts/i18n-extract.py` marks every translatable element in `site/index.html`
   (idempotent) and writes the source strings to `data/i18n/en.json`.
2. Translators edit one `data/i18n/<code>.json` each; the schema carries name, native name,
   region, family, script, direction, confidence, a translator note and the uncertain list.
3. `node server/scripts/i18n-build.cjs` validates every file (all keys present, HTML tags
   intact), rewrites the generated LANGS and STR block in the site, and exports
   `data/languages.json`. Bad strings are dropped to the English fallback, never shipped broken.

## Voice

Sunbird AI's open Spark-TTS SALT model speaks seven of these languages (Ugandan English,
Luganda, Runyankore, Acholi, Ateso, Lugbara, Swahili); the showreel's voice pipeline
(`showreel/voice/`) uses it, and the same route can read the app aloud in v2.

## What a review needs

A native speaker reads their file top to bottom, fixes what is wrong, deletes fixed keys from
`uncertain`, raises `confidence` to `reviewed`, and adds their name to `review_note` if they
wish to be credited. Ten minutes with the welcome line, the four verbs, the doors and the
money strings is already a meaningful review; the welcome greeting is the single most
important string in the file.
