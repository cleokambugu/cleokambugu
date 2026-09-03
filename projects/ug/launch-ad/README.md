# UG launch ad

Fifteen seconds of the real UG app, captured in a real browser, in four deliverables.
Video is not committed to this repository (`.gitignore` excludes `*.mp4`, which is why
`../showreel/dist/` is untracked too), so `dist/` is built by the commands below:

| File | Shape | Where it is for |
|---|---|---|
| `dist/ug-launch-ad-15s-16x9.mp4` | 1920 × 1080 | the master: site, press, YouTube, a screen in a room |
| `dist/ug-launch-ad-15s-9x16.mp4` | 1080 × 1920 | phone feeds — re-shot at phone size, not cropped |
| `dist/ug-launch-ad-15s-1x1.mp4` | 1080 × 1080 | square feeds — cropped from the phone shoot |
| `dist/ug-launch-ad-6s-bumper.mp4` | 1920 × 1080 | the six-second cut-down |

All four are 30 fps CFR, H.264 High, bt709, AAC 192 kb/s, faststart. Captions are burnt in,
because a launch ad is watched muted.

Nothing here redraws the product. Every frame is `../site/index.html` in headless Chromium,
stepped one frame at a time so the choreography is exact and the same command produces the
same film twice.

## The cut

Ten beats in fifteen seconds. Nothing is held longer than 1.87 s.

| At | Beat | What is on screen |
|---:|---|---|
| 0.00 | the gate | the crest, and the greeting in three languages |
| 1.03 | the languages | the gate walks through Uganda's own: Olusoga, Lumasaaba, Lugwere, Olusamia, Ateso, Kupsabiny, Leb Acoli, Leb Lango, Kumam, Karimojong, Lugbara |
| 3.10 | the answer | Oluganda chosen, and the app greets back — *Tukwanirizza mu Uganda.* |
| 4.17 | the turn | the whole product in Luganda |
| 5.10 | the promise | *Genda. Gabana. Pangisa. Tuma.* |
| 6.03 | the Atlas | the particle map of Uganda, turned by hand |
| 7.90 | the compare desk | *Okulonda obubi kukusasuza ki* — cheapest right now UGX 2,050, 14 of 17 ways |
| 9.70 | the Virtual Stage | *Emmotoka ejja ng'ejjudde* — UGX 34,613, falls to UGX 25,960 when full |
| 11.37 | the fleet | *Pangisa emmotoka, oba tuukamu* |
| 12.80 | the crest | the end card |

Four captions, each over the shot it describes: *The app speaks your language* · *Every way
to move in Uganda* · *Every fare, ranked. One screen.* · *The price falls as the car fills.*
Every one is copy the product already uses.

The 16:9 and 9:16 cuts share the same beat map frame for frame, the same camera plan and
the same score, so they are one edit at two shapes rather than two films.

## The score

`score.js` renders `../showreel/ug-score.js` — the product's own sound-panel engine, 114 BPM,
A minor pentatonic, kidandali idiom: log drum, shekere, 3-2 son clave, congas, an
adungu-style pluck and an endingidi-style lead. All synthesised, no samples, no network.
It is rendered through an `OfflineAudioContext` against a cue sheet written to this picture,
so every impact, drop and key change lands on a cut. See `../showreel/SCORE.md`.

**There is no voice on it.** The narration pipeline (`../showreel/voice/`) has a casting
sheet, a direction sheet and a script, and no line has ever been recorded — the engines it
targets need network this environment does not have. A recorded Ugandan voice is the single
biggest thing this ad is still missing; see `../showreel/voice/CASTING.md`.

## Running it

Needs Node, Playwright with Chromium, and ffmpeg. Overridable: `PLAYWRIGHT_MODULE`,
`CHROMIUM`, `FFMPEG`, `SITE_URL`.

```sh
node prepare.js                       # stage .render/ from ../site
(cd .render && python3 -m http.server 8811) &

node plates.js 1920 1080 16x9         # caption plates + end card, composed per shape
node plates.js 1080 1920 9x16
node plates.js 1080 1080 1x1
node score.js                         # audio/ug-ad-score.wav
node score-bumper.js                  # audio/ug-bumper-score.wav

node shoot.js --shape 16x9            # frames/16x9/  ~3 min
node shoot.js --shape 9x16            # frames/9x16/  ~3 min

./build.sh 16x9 && ./build.sh 9x16 && ./build.sh 1x1
./build-bumper.sh
```

`frames/`, `plates/`, `audio/`, `.render/`, `vendor/` and `dist/` are all derived. The
first five are listed in this directory's `.gitignore`; `dist/` is covered by the
repository's own `*.mp4` rule, the same one that keeps `../showreel/dist/` untracked.

### three.js

The map beat needs three.js r128, which `../site/index.html` fetches from cdnjs at runtime.
On a machine with no route to a CDN the beat would render as a black rectangle and the ad
would be quietly wrong rather than loudly broken, so `prepare.js` will use a local copy if
one is sitting at `vendor/three.min.js` and otherwise leaves the CDN URL alone and says so.
To get one without a CDN:

```sh
git clone --depth 1 --filter=blob:none --sparse https://github.com/mrdoob/three.js /tmp/three
(cd /tmp/three && git checkout r128 && git sparse-checkout set build)
mkdir -p vendor && cp /tmp/three/build/three.min.js vendor/
```

## Three things the shoot has to settle first

Each was a real defect in an earlier cut, and each is now handled in `shoot.js`:

1. **`scroll-behavior: smooth`** (`../site/index.html`) is right for a person and wrong for
   a camera. A 4,500 px beat change animates across ~40 frames, so the shot that lands is
   whatever the page was passing through — which is how the caption *Every fare, ranked* once
   ended up over the Quality board, a wall of English body copy, instead of the fare table.
2. **UG Drive**, the app's auto-tour, is armed by a one-shot document `pointerdown`
   (`initAutoDrive()`). Turning the country by hand is a pointerdown, so the tour started
   under the map beat and drove the rest of the film, re-planning the trip to Ziwa Rhino
   Sanctuary and emptying the Virtual Stage. The shoot sets `ug:dockOff`, the product's own
   opt-out.
3. **Offsets depend on state.** Every scroll position here was measured with Oluganda
   chosen and the opening film finished. Measured in the English default they are all
   wrong by tens to hundreds of pixels, because the page is a different height.

`shoot.js` asserts the trip is still Ntinda → Downtown Kampala at the compare-desk beat and
exits non-zero if it is not, because every offset below the map depends on it.

## Provenance

Everything in this directory was made in this repository from this repository: the frames
from `../site/index.html`, the music from `../showreel/ug-score.js`, the crest on the end
card from the same 64-unit geometry the app draws, the type from Archivo and Martian Mono
via Google Fonts, the copy from the product's own strings. No stock, no library footage, no
generated imagery. The prices on screen are the prototype's own estimates, which is what the
end card says.
