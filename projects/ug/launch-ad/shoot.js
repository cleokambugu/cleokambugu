#!/usr/bin/env node
/* Shoot the UG launch ad: 450 deterministic frames of the real app in a real browser.

     node shoot.js --shape 16x9   ->  frames/16x9/0000.png ...  1920 x 1080
     node shoot.js --shape 9x16   ->  frames/9x16/0000.png ...  1080 x 1920

   Frame-stepped rather than screen-recorded, so the choreography is exact and the same
   command produces the same film twice. Ten beats in fifteen seconds; nothing is held
   longer than 1.87 s:

     0.00  the crest, the greeting in three languages
     1.03  the gate walks through Uganda's own languages
     3.10  Oluganda chosen — the app greets back: Tukwanirizza mu Uganda.
     4.17  the turn: the whole product in Luganda
     5.10  Genda. Gabana. Pangisa. Tuma.
     6.03  the particle map, turned by hand
     7.90  Okulonda obubi kukusasuza ki — 14 of 17 ways, cheapest first
     9.70  Emmotoka ejja ng'ejjudde — the price falls as the car fills
    11.37  Pangisa emmotoka, oba tuukamu — the fleet
    12.80  back to the map, under the end card

   Three things about the app have to be settled before a frame is worth keeping, and each
   of them was a defect in an earlier cut:

     · scroll-behavior is smooth (site/index.html), which is right for a person and wrong
       for a camera — a 4,500 px beat change then animates across ~40 frames and the shot
       that lands is whatever the page was passing through. Cuts must be cuts.
     · UG Drive is the app's auto-tour and initAutoDrive() arms a one-shot document
       pointerdown to start it. Turning the country by hand is a pointerdown, so the tour
       began under the map beat and drove the rest of the film, re-planning the trip and
       emptying the Virtual Stage. 'ug:dockOff' is the product's own opt-out.
     · every scroll offset is measured with Oluganda chosen and the opening film finished,
       because the page is a different height in that state than in the English default.

   Needs Playwright with Chromium and a server for the render root (see README.md).
*/
const fs = require('fs'), path = require('path');

const args = Object.fromEntries(process.argv.slice(2)
  .map((a, i, arr) => a.startsWith('--') ? [a.slice(2), arr[i + 1]] : []).filter(x => x.length));
const PW = process.env.PLAYWRIGHT_MODULE || '/opt/node22/lib/node_modules/playwright';
const CHROME = process.env.CHROMIUM || '/opt/pw-browsers/chromium';
const URL = process.env.SITE_URL || 'http://127.0.0.1:8811';
const SHAPE = args.shape || '16x9';
const OUT = path.resolve(args.out || path.join(__dirname, 'frames', SHAPE));
const N = 450;

/* Beat -> [firstFrame, lastFrame, scrollY]. The frame numbers are identical in both
   shapes, so the two masters are the same edit rather than two different films; only the
   offsets differ, because the phone layout is a different page. */
const SHAPES = {
  '16x9': {
    vw: 1280, vh: 720, dsf: 1.5, mobile: false, gate: 'carousel', drift: 26,
    drag: { x: 890, y: 330, dx: 150, dy: 20 },
    beats: {
      gate: [0, 30, 0], ring: [31, 92, 0], greet: [93, 124, 0], turn: [125, 152, 0],
      hero: [153, 180, 0], map: [181, 236, 186], fares: [237, 290, 2120],
      stage: [291, 340, 6660], fleet: [341, 383, 8660], bookend: [384, 449, 186],
    },
  },
  /* 405 x 720 at deviceScaleFactor 8/3 is exactly 1080 x 1920 — the phone cut is shot at
     its delivered size against the app's own mobile blocking, never cropped down from the
     desktop master. On a phone the welcome gate is not the 3D carousel at all: #wlStage
     collapses to zero height and the languages render as #wlList, a column grouped by
     region, which puts a dozen Ugandan languages on screen at once instead of three. */
  '9x16': {
    vw: 405, vh: 720, dsf: 8 / 3, mobile: true, gate: 'list', drift: 40,
    drag: { x: 200, y: 200, dx: 96, dy: 14 },
    beats: {
      gate: [0, 30, 0], ring: [31, 92, 0], greet: [93, 124, 0], turn: [125, 152, 0],
      hero: [153, 180, 0], map: [181, 236, 900], fares: [237, 290, 3740],
      stage: [291, 340, 12500], fleet: [341, 383, 16120], bookend: [384, 449, 900],
    },
  },
};

const easeOut = t => 1 - Math.pow(1 - t, 3);
const seg = (f, a, b) => Math.max(0, Math.min(1, (f - a) / (b - a)));

/* The front card of the carousel is the one nearest the camera, so it is simply the
   largest on screen. Reading its size is far more robust than sniffing a border colour. */
const frontLang = page => page.evaluate(() => {
  const el = document.getElementById('welcome'); if (!el) return null;
  let best = null, area = -1;
  el.querySelectorAll('[data-wl]').forEach(c => {
    const r = c.getBoundingClientRect(); const a = r.width * r.height;
    if (a > area) { area = a; best = c.dataset.wl; }
  });
  return best;
});

async function main() {
  const S = SHAPES[SHAPE];
  if (!S) { console.error(`shoot: unknown shape ${SHAPE} (16x9 | 9x16)`); process.exit(2); }
  const B = S.beats;
  const beatAt = f => Object.entries(B).find(([, v]) => f >= v[0] && f <= v[1]);

  fs.rmSync(OUT, { recursive: true, force: true });
  fs.mkdirSync(OUT, { recursive: true });

  const { chromium } = require(PW);
  const browser = await chromium.launch({
    executablePath: CHROME,
    args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader',
           '--autoplay-policy=no-user-gesture-required', '--font-render-hinting=none', '--disable-lcd-text'],
  });
  const page = await browser.newPage({
    viewport: { width: S.vw, height: S.vh }, deviceScaleFactor: S.dsf,
    isMobile: S.mobile, hasTouch: S.mobile, colorScheme: 'dark', reducedMotion: 'no-preference',
  });
  page.on('pageerror', e => console.error('PAGEERROR', e.message));
  await page.addInitScript(() => { try { localStorage.setItem('ug:dockOff', 'true'); } catch (e) {} });

  await page.goto(URL + '/index.html', { waitUntil: 'load' });
  await page.waitForFunction(() => window.__ugReady === true, null, { timeout: 60000 });
  await page.waitForTimeout(1500);
  await page.addStyleTag({ content:
    '#toast{display:none!important}\n' +               // product behaviour, uninvited in a 15 s spot
    'html,body,*{scroll-behavior:auto!important}\n' +  // cuts must be cuts
    '#pins,.pin{pointer-events:none!important}' });    // the drag wants the canvas, not a pin

  // warm the WebGL scene behind the gate so the map beat is never a black rectangle
  await page.evaluate(() => { const g = document.getElementById('welcome'); if (g) { g.style.visibility = 'hidden'; g.__hover = true; } });
  await page.evaluate(() => document.getElementById('map')?.scrollIntoView({ block: 'center' }));
  await page.waitForTimeout(8000);
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
  await page.evaluate(() => { const g = document.getElementById('welcome'); if (g) g.style.visibility = ''; });
  await page.waitForTimeout(700);

  let FWD = null, PAN = 0;
  if (S.gate === 'carousel') {
    // The keydown listener lives on #wlStage. Without focusing it the arrow keys go to
    // BODY and do nothing at all — which is how an earlier cut's montage ended up being
    // the idle auto-spin drifting through the tail of the list, showing Chinese,
    // Japanese, Korean and Russian rather than a single Ugandan language.
    await page.evaluate(() => {
      const g = document.getElementById('welcome'); if (g) g.__hover = true;   // stop the idle spin
      document.getElementById('wlStage')?.focus();
    });
    let home = 0;
    while (await frontLang(page) !== 'lg' && home < 44) { await page.keyboard.press('ArrowRight'); await page.waitForTimeout(70); home++; }
    await page.keyboard.press('ArrowRight'); await page.waitForTimeout(140);
    FWD = (await frontLang(page)) === 'xog' ? 'ArrowRight' : 'ArrowLeft';   // measured, not assumed
    await page.keyboard.press(FWD === 'ArrowRight' ? 'ArrowLeft' : 'ArrowRight'); await page.waitForTimeout(140);
    console.log(`gate: carousel, forward is ${FWD}, opening on ${await frontLang(page)}`);
  } else {
    // the pan stops where Uganda stops: on Lugbara, the last of the Ugandan groups
    PAN = await page.evaluate(() => {
      const list = document.getElementById('wlList');
      const last = list?.querySelector('[data-wl="lgg"]');
      return (!list || !last) ? 0 : Math.max(0, last.offsetTop - list.clientHeight + last.offsetHeight + 24);
    });
    const shown = await page.evaluate(() => [...document.querySelectorAll('#wlList [data-wl]')]
      .slice(0, 12).map(e => e.dataset.wl).join(' '));
    console.log(`gate: list, pan 0 -> ${PAN}px, opening on ${shown}`);
  }

  const t0 = Date.now(); const seen = []; let route = '?';
  for (let f = 0; f < N; f++) {
    const [name, [a, b, y]] = beatAt(f);

    if (name === 'ring') {
      if (S.gate === 'carousel') {
        if ((f - B.ring[0]) % 5 === 0 && f > B.ring[0]) {
          await page.keyboard.press(FWD);
          const fl = await frontLang(page); if (fl && seen[seen.length - 1] !== fl) seen.push(fl);
        }
      } else {
        await page.evaluate(v => { const l = document.getElementById('wlList'); if (l) l.scrollTop = v; },
                            Math.round(PAN * easeOut(seg(f, B.ring[0], B.ring[1]))));
      }
    }
    if (f === B.greet[0]) {
      await page.evaluate(() => { const w = document.getElementById('welcome');
        const c = [...w.querySelectorAll('[data-wl]')].find(e => e.dataset.wl === 'lg'); if (c) c.click(); });
    }
    if (f === B.turn[0]) await page.evaluate(() => document.getElementById('wlGo')?.click());

    // a slow drift inside each beat, so a held shot still breathes
    const drift = S.drift * easeOut(seg(f, a, b));
    await page.evaluate(v => window.scrollTo({ top: v, behavior: 'instant' }), Math.round(y + (y > 0 ? drift : 0)));

    // turn the country by hand across the map beat
    if (name === 'map') {
      const u = seg(f, B.map[0], B.map[1]);
      if (f === B.map[0]) { await page.mouse.move(S.drag.x, S.drag.y); await page.mouse.down(); }
      await page.mouse.move(S.drag.x + S.drag.dx * u, S.drag.y - S.drag.dy * Math.sin(u * Math.PI));
      if (f === B.map[1]) await page.mouse.up();
    }

    // One assertion, on the beat the film's money claim rests on: if anything has moved
    // the trip off the route these offsets were measured against, the compare desk and
    // the Virtual Stage are answering a different question and the cut is wrong.
    if (f === B.fares[0] + 3) {
      route = await page.evaluate(() => [...document.querySelectorAll('#compare select')]
        .slice(0, 2).map(e => e.options[e.selectedIndex]?.text).join(' -> '));
    }

    await page.screenshot({ path: path.join(OUT, String(f).padStart(4, '0') + '.png'), animations: 'allow' });
    if (f % 60 === 0) console.log(`  ${f}/${N} ${name} y=${Math.round(y)} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  if (seen.length) console.log('languages shown:', seen.join(' '));
  console.log('route on the compare desk:', route);
  if (route !== 'Ntinda -> Downtown Kampala') {
    console.error('shoot: the trip moved off Ntinda -> Downtown Kampala; the offsets below the map no longer hold');
    await browser.close(); process.exit(1);
  }
  console.log(`done ${SHAPE} in ${((Date.now() - t0) / 1000).toFixed(0)} s -> ${OUT}`);
  await browser.close();
}

main().catch(e => { console.error(e); process.exit(1); });
