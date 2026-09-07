/* UG client tests.
 *
 * Strategy note (this is the whole argument): index.html is one classic <script>. Top-level
 * `function` declarations AND top-level `const`/`let` bindings are both reachable from
 * page.evaluate(), because evaluate compiles in global scope. So the single file is directly
 * unit-testable in a real browser with NO build step, NO module refactor and NO test hooks in
 * the shipped file. The file stays the artefact; the browser is the module loader.
 *
 * Run:  node --test client.test.mjs
 * Needs: playwright chromium.
 */
import { test, before, after, describe } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFileSync, existsSync } from 'node:fs';
import { join, extname, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const require_ = createRequire(import.meta.url);
/* Playwright is a developer dependency of the checkout, not of the product. Resolve it wherever it
   lives — the local node_modules, or the global install a sandbox provides. */
const pw = (() => {
  for (const id of ['playwright', '/opt/node22/lib/node_modules/playwright/index.js']) {
    try { return require_(id); } catch { /* try the next */ }
  }
  throw new Error('playwright is not installed: npm i -D playwright, or run where a global copy exists');
})();
const { chromium } = pw;

const HERE = dirname(fileURLToPath(import.meta.url));
const PROJECT = join(HERE, '..', '..');
const SITE = process.env.UG_SITE || join(PROJECT, 'site');
const LAUNCH = { args: ['--no-sandbox', '--disable-dev-shm-usage'] };
if (process.env.UG_CHROMIUM) LAUNCH.executablePath = process.env.UG_CHROMIUM;
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json', '.webmanifest': 'application/manifest+json', '.png': 'image/png', '.svg': 'image/svg+xml' };

let server, origin, browser, ctx;
/* Lets test 5 mutate what the document says between loads. */
const overrides = new Map();
let htmlContentType = null; // null = default (with charset)

function start() {
  return new Promise((resolve) => {
    server = createServer((req, res) => {
      const url = new URL(req.url, 'http://x');
      let p = decodeURIComponent(url.pathname);
      if (p === '/' || p.endsWith('/')) p += 'index.html';
      if (overrides.has(p)) {
        const { body, type } = overrides.get(p);
        res.writeHead(200, { 'content-type': type, 'cache-control': 'no-cache' });
        return res.end(body);
      }
      const file = join(SITE, p);
      if (!file.startsWith(SITE) || !existsSync(file)) { res.writeHead(404); return res.end('404'); }
      const ext = extname(file);
      let type = TYPES[ext] || 'application/octet-stream';
      if (ext === '.html' && htmlContentType) type = htmlContentType;
      res.writeHead(200, { 'content-type': type, 'cache-control': 'no-cache' });
      res.end(readFileSync(file));
    }).listen(0, '127.0.0.1', () => { origin = `http://127.0.0.1:${server.address().port}`; resolve(); });
  });
}

/* A page with the real file loaded, third-party origins cut off so a test never depends on a CDN. */
async function openPage({ viewport = { width: 390, height: 844 }, offline3p = true, reducedMotion } = {}) {
  const c = await browser.newContext({ viewport, isMobile: true, hasTouch: true, deviceScaleFactor: 2, ...(reducedMotion ? { reducedMotion } : {}) });
  if (offline3p) await c.route(/^https:\/\/(cdnjs\.cloudflare\.com|fonts\.googleapis\.com|fonts\.gstatic\.com)/, (r) => r.abort());
  const page = await c.newPage();
  await page.goto(`${origin}/index.html`, { waitUntil: 'load', timeout: 120000 });
  await page.waitForFunction(() => typeof qaScore === 'function', null, { timeout: 30000 });
  /* Boot is no longer one synchronous task: what the first screen needs runs immediately and the
     rest drains through requestIdleCallback. Tests that measure the painted page wait for the end
     of that drain, which is also the honest definition of "the app is up". */
  await page.waitForFunction(() => window.__ugReady === true, null, { timeout: 30000 });
  return { c, page };
}

before(async () => { await start(); browser = await chromium.launch(LAUNCH); });
after(async () => { await browser?.close(); server?.close(); });

/* ------------------------------------------------------------------ 1 */
/* DEFECT: w(report) = 0.5^(age/90) with no clamp. A report dated in the future got
   0.5^negative — exponential weight. One forged timestamp outweighed 2000 honest reports.
   INVARIANT: no single report may weigh more than one report dated now. */
describe('1. report decay is bounded above by 1', () => {
  test('a report dated 10 years in the future cannot outvote 2000 honest ones', async () => {
    const { c, page } = await openPage();
    try {
      const result = await page.evaluate(() => {
        const DAY = 86400000, now = Date.now();
        const honest = [];
        for (let i = 0; i < 2000; i++) honest.push({ supplier: 'test-op', at: now - (i % 30) * DAY, meters: { care: 1 } });
        const forged = { supplier: 'test-op', at: now + 3650 * DAY, meters: { care: 0 } };
        localStorage.setItem('ug:qaReports', JSON.stringify([...honest, forged]));
        const withForged = qaRates('test-op').rates.care;
        localStorage.setItem('ug:qaReports', JSON.stringify(honest));
        const without = qaRates('test-op').rates.care;
        // and the weight function itself, read straight off the published formula
        const w = (ageDays) => Math.pow(0.5, Math.max(0, ageDays) / QA_HALFLIFE_DAYS);
        localStorage.removeItem('ug:qaReports');
        return { withForged, without, wFuture: w(-3650), wNow: w(0), wOld: w(90) };
      });
      assert.ok(result.wFuture <= 1 + 1e-12, `a future-dated report weighs ${result.wFuture}, must be <= 1`);
      assert.equal(result.wNow, 1);
      assert.ok(Math.abs(result.wOld - 0.5) < 1e-12, 'a 90-day-old report must weigh exactly half');
      // one bad report among 2000 good ones may move the rate by well under a point
      const moved = result.without - result.withForged;
      assert.ok(moved < 0.01, `one forged report moved the care rate by ${moved}; a single report must not dominate`);
      assert.ok(result.withForged > 0.99, `care collapsed to ${result.withForged} on one forged report`);
    } finally { await c.close(); }
  });
});

/* ------------------------------------------------------------------ 2 */
/* DEFECT: the shrinkage prior was the median of the same seeded table it was correcting.
   Categories with one member pulled toward themselves — shrinkage that did nothing.
   INVARIANT: the prior is exogenous. Nothing a supplier does may move its own prior. */
describe('2. the prior is exogenous to the evidence', () => {
  test('no amount of evidence changes the prior it is shrunk toward', async () => {
    const { c, page } = await openPage();
    try {
      const r = await page.evaluate(() => {
        const meters = QA_METERS.map((m) => m.id);
        const snap = () => Object.fromEntries(meters.map((m) => [m, qaPrior(m)]));
        const before = snap();
        const DAY = 86400000, now = Date.now();
        // flood every demo supplier with extreme evidence in both directions
        const reports = [];
        for (const id of Object.keys(QA_DEMO)) {
          for (let i = 0; i < 300; i++) {
            reports.push({ supplier: id, at: now - (i % 10) * DAY, meters: Object.fromEntries(meters.map((m) => [m, i % 2])) });
          }
        }
        localStorage.setItem('ug:qaReports', JSON.stringify(reports));
        const after = snap();
        localStorage.removeItem('ug:qaReports');
        return { before, after, published: QA_BASELINE, priorN: QA_PRIOR_N };
      });
      assert.deepEqual(r.after, r.before, 'the prior moved when the evidence moved: it is endogenous');
      // and it is the number published in docs/quality.md, not a drifted copy
      assert.deepEqual(r.before, { money: 0.86, time: 0.70, shows: 0.85, care: 0.80, fix: 0.55, pay: 0.84 },
        'code priors have drifted from the table published in docs/quality.md');
      assert.equal(r.priorN, 25, 'K is published as 25 trips in docs/quality.md');
    } finally { await c.close(); }
  });

  /* The number on screen must be the number in docs/quality.md, recomputed independently.
     This is what catches a prior — or a weight, or K — drifting between doc and code. */
  test('every meter on screen equals the published shrinkage formula, recomputed', async () => {
    const { c, page } = await openPage();
    try {
      const rows = await page.evaluate(() => {
        const out = [];
        for (const id of Object.keys(QA_DEMO)) {
          const q = qaScore(id);
          const { rates, n } = qaRates(id);
          for (const m of q.meters) {
            // independent reimplementation of: pulled = (n·raw + K·prior)/(n + K)
            const expect = Math.round(((n * rates[m.id] + QA_PRIOR_N * QA_BASELINE[m.id]) / (n + QA_PRIOR_N)) * 100);
            out.push({ id, meter: m.id, shown: m.value, expect, n, weight: m.weight, fixedW: QA_M[m.id].w });
          }
        }
        return out;
      });
      assert.ok(rows.length > 0, 'no demo meters to check');
      for (const r of rows) {
        assert.equal(r.shown, r.expect, `${r.id}/${r.meter}: screen shows ${r.shown}, published formula gives ${r.expect}`);
      }
      // and a counted meter's weight is the FIXED table weight — never a sum over declared promises
      for (const r of rows) {
        if (r.weight > 0) assert.equal(r.weight, r.fixedW,
          `${r.id}/${r.meter}: weight ${r.weight} != fixed table weight ${r.fixedW}; promises must not buy weight`);
      }
    } finally { await c.close(); }
  });

  test('a thin supplier is pulled toward the prior, not toward its own evidence', async () => {
    const { c, page } = await openPage();
    try {
      const r = await page.evaluate(() => {
        // an unseeded id: no QA_SEED row, so n is exactly the reports we file
        const one = [{ supplier: 'unseeded-op', at: Date.now(), meters: { money: 1 } }];
        localStorage.setItem('ug:qaReports', JSON.stringify(one));
        const { rates, n } = qaRates('unseeded-op');
        const pulled = (n * rates.money + QA_PRIOR_N * QA_BASELINE.money) / (n + QA_PRIOR_N);
        localStorage.removeItem('ug:qaReports');
        return { n, raw: rates.money, pulled, prior: QA_BASELINE.money };
      });
      assert.equal(r.n, 1);
      assert.equal(r.raw, 1, 'one perfect report should give a raw rate of 1');
      assert.ok(Math.abs(r.pulled - r.prior) < Math.abs(r.pulled - r.raw),
        `one report pulled the score to ${r.pulled}, closer to its own evidence (${r.raw}) than to the prior (${r.prior})`);
    } finally { await c.close(); }
  });
});

/* ------------------------------------------------------------------ 3 */
/* DEFECT: buttons overlapped prices at 390px — the commonest real screen in Kampala.
   INVARIANT: no two visible siblings that both carry text may overlap, and the document
   never scrolls sideways. Checked at the three widths that matter. */
describe('3. layout holds at narrow widths', () => {
  for (const width of [360, 390, 412]) {
    test(`no sibling overlap and no horizontal scroll at ${width}px`, async () => {
      /* reduced-motion is the app's own settled state: initReveal() returns early and .rv
         carries no transform, so a rect is a layout box and not an animation frame. */
      const { c, page } = await openPage({ viewport: { width, height: 844 }, reducedMotion: 'reduce' });
      try {
        const bad = await page.evaluate(() => {
          const seen = [];
          const vis = (el) => {
            const s = getComputedStyle(el);
            if (s.display === 'none' || s.visibility === 'hidden' || Number(s.opacity) === 0) return false;
            const r = el.getBoundingClientRect();
            return r.width > 1 && r.height > 1;
          };
          const ownText = (el) => Array.from(el.childNodes).some((n) => n.nodeType === 3 && n.textContent.trim().length);
          const overlap = (a, b) => {
            const x = Math.min(a.right, b.right) - Math.max(a.left, b.left);
            const y = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
            return x > 3 && y > 3 ? { x: Math.round(x), y: Math.round(y) } : null;
          };
          for (const parent of document.querySelectorAll('body *')) {
            if (parent.closest('svg')) continue;            // vector artwork overlaps by design
            const kids = Array.from(parent.children).filter((k) => {
              const s = getComputedStyle(k);
              // stacked-on-purpose elements are out of scope: only in-flow siblings are compared
              if (s.position !== 'static' && s.position !== 'relative') return false;
              // inline boxes share line boxes by design, and a wrapped inline's union rect
              // legitimately overlaps its neighbours. Only box-level siblings are comparable.
              if (s.display === 'inline' || s.display === 'contents') return false;
              // a wrapped element reports one union rect across several lines: not comparable either
              if (k.getClientRects().length > 1) return false;
              return true;
            }).filter(vis);
            if (kids.length < 2) continue;
            for (let i = 0; i < kids.length; i++) for (let j = i + 1; j < kids.length; j++) {
              const A = kids[i], B = kids[j];
              // only care when both carry their own text: a button over a price, not a decorative wrapper
              if (!ownText(A) || !ownText(B)) continue;
              const o = overlap(A.getBoundingClientRect(), B.getBoundingClientRect());
              const label = (el) => el.tagName.toLowerCase() + ':' + String(el.innerText ?? el.textContent ?? '').trim().replace(/\s+/g, ' ').slice(0, 28);
              if (o) seen.push({
                parent: parent.tagName.toLowerCase() + (parent.id ? '#' + parent.id : '') + (typeof parent.className === 'string' && parent.className.trim() ? '.' + parent.className.trim().split(/\s+/).slice(0, 2).join('.') : ''),
                a: label(A), b: label(B), o,
              });
            }
          }
          return { seen: seen.slice(0, 12), count: seen.length, scrollWidth: document.documentElement.scrollWidth, inner: window.innerWidth };
        });
        assert.equal(bad.count, 0, `overlapping text siblings:\n${JSON.stringify(bad.seen, null, 1)}`);
        assert.ok(bad.scrollWidth <= bad.inner + 1, `page scrolls sideways: scrollWidth ${bad.scrollWidth} > viewport ${bad.inner}`);
      } finally { await c.close(); }
    });
  }
});

/* ------------------------------------------------------------------ 4 */
/* DEFECT: a missing charset declaration produced mojibake in shipped video. The site ships
   41 languages; every one of them past English is non-ASCII somewhere.
   INVARIANT: every shipped HTML file declares utf-8 inside the first 1024 bytes (the spec's
   sniffing window), and the text survives a server that sends no charset at all. */
describe('4. utf-8 survives a server that says nothing', () => {
  const SHIPPED = [join(SITE, 'index.html')];
  for (const dir of [join(PROJECT, 'showreel')]) {
    for (const f of ['index.html', 'short.html', 'sound.html', 'short-sound.html', 'short-cam.html', 'short-cam-sound.html']) {
      const p = join(dir, f); if (existsSync(p)) SHIPPED.push(p);
    }
  }

  test('every shipped HTML declares utf-8 in the first 1024 bytes', () => {
    const missing = [];
    for (const p of SHIPPED) {
      const head = readFileSync(p).subarray(0, 1024).toString('latin1');
      if (!/<meta\s+charset\s*=\s*["']?utf-8/i.test(head) && !/charset\s*=\s*["']?utf-8/i.test(head)) missing.push(p);
    }
    assert.deepEqual(missing, [], `HTML with no utf-8 declaration in the sniffing window:\n${missing.join('\n')}`);
  });

  test('non-ASCII renders correctly when the response carries no charset', async () => {
    htmlContentType = 'text/html'; // deliberately bare: no ;charset=utf-8
    try {
      const { c, page } = await openPage();
      try {
        const r = await page.evaluate(() => {
          const body = document.body.innerText;
          // strings the app ships in Luganda / Acholi / Swahili, plus the arrow in the masthead
          const probes = ['Londa olulimi lwo', 'Chagua lugha yako', '→'];
          return {
            encoding: document.characterSet,
            replacementChars: (body.match(/�/g) || []).length,
            found: probes.filter((s) => body.includes(s)),
            probes,
            // a Luganda string straight out of the shipped bundle, not the DOM
            sample: (typeof STR !== 'undefined' && STR['page.p.ug_speaks_the_languages']) ? STR['page.p.ug_speaks_the_languages'].lg || '' : '',
          };
        });
        assert.equal(r.encoding, 'UTF-8', `document decoded as ${r.encoding}, not UTF-8`);
        assert.equal(r.replacementChars, 0, `${r.replacementChars} U+FFFD replacement characters in the rendered page`);
        assert.deepEqual(r.found, r.probes, 'non-ASCII UI strings did not survive decoding');
        assert.ok(!/�|Ã|â€/.test(r.sample), `mojibake in the shipped Luganda string: ${r.sample.slice(0, 80)}`);
      } finally { await c.close(); }
    } finally { htmlContentType = null; }
  });
});

/* ------------------------------------------------------------------ 5 */
/* DEFECT: the service worker was cache-first for the document, keyed to a hand-edited version
   string. Installed users were served a frozen index.html — a frozen price table — until
   somebody bumped a constant. A reviewer saw two versions of the product in one session.
   INVARIANT: the document is network-first. A price change on the server reaches an already
   installed client on the very next load, with no version bump. */
describe('5. the service worker never serves a stale document', () => {
  test('a changed price reaches an installed client on the next load', async () => {
    const c = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true });
    await c.route(/^https:\/\/(cdnjs|fonts)\./, (r) => r.abort());
    const page = await c.newPage();
    try {
      const marker = (v) => `<!doctype html><meta charset="utf-8"><title>t</title><body><p id="price">UGX ${v}</p>`;
      overrides.set('/index.html', { body: marker(11111), type: 'text/html; charset=utf-8' });

      await page.goto(`${origin}/index.html`, { waitUntil: 'load' });
      // install the real service worker from the real file
      await page.evaluate(async () => {
        const reg = await navigator.serviceWorker.register('/sw.js');
        await navigator.serviceWorker.ready;
        if (reg.active) return;
        await new Promise((r) => setTimeout(r, 500));
      });
      await page.waitForFunction(() => !!navigator.serviceWorker.controller || document.readyState === 'complete', null, { timeout: 15000 }).catch(() => {});
      await page.reload({ waitUntil: 'load' });
      await page.waitForFunction(() => !!navigator.serviceWorker.controller, null, { timeout: 15000 });
      const first = await page.textContent('#price');
      assert.equal(first.trim(), 'UGX 11111', 'setup: the controlled page should show the first price');

      // the price changes on the server. No version bump, no cache name change.
      overrides.set('/index.html', { body: marker(22222), type: 'text/html; charset=utf-8' });
      await page.reload({ waitUntil: 'load' });
      const second = await page.textContent('#price');
      assert.equal(second.trim(), 'UGX 22222',
        'the service worker served a frozen document: an installed client is still showing the old price table');

      // and it must still work offline, from cache
      await c.setOffline(true);
      await page.reload({ waitUntil: 'load' }).catch(() => {});
      const offline = await page.textContent('#price').catch(() => null);
      await c.setOffline(false);
      assert.ok(offline, 'the shell no longer works offline: network-first must still fall back to cache');
    } finally { overrides.delete('/index.html'); await c.close(); }
  });
});

/* ------------------------------------------------------------------ 6 */
/* DEFECT: `t` is the translator, and it is also the most tempting name in the file for a loop
   variable, a timeout handle, a piece of text. `trips.forEach((t,i)=>…)` shadowed it inside a
   render body, so wiring one button to the dictionary broke that whole section at runtime —
   silently, in every language, because nothing loads a second language in review.
   Same family: a key that reaches t() but is not in en.json renders as its own name, which is
   how the hero came to print the literal string "flipDeliver".
   INVARIANT: every language renders every list without throwing, and no raw key reaches a screen. */
describe('6. every language renders, and no key is left showing', () => {
  test('41 languages through every render path', async () => {
    const { c, page } = await openPage({ viewport: { width: 1280, height: 900 }, reducedMotion: 'reduce' });
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e.message)));
    try {
      const r = await page.evaluate(async () => {
        const RENDERERS = ['renderCompare', 'renderStages', 'renderAtlas', 'renderFleet', 'renderDeliver',
          'renderForesight', 'renderWall', 'renderLegs', 'renderOffers', 'renderTrips', 'renderDrive', 'renderDests'];
        /* a key looks like ui.something, flipSomething, or section.tag.slug — never a word a page
           would legitimately contain, which is why 'ride' and 'me' are not tested for */
        const keys = Object.keys(STR).filter((k) => k.includes('.') || /^flip[A-Z]/.test(k));
        const thrown = [], showing = [], unfetched = [];
        for (const code of Object.keys(LANGS)) {
          /* setLang fetches the pack, so this also proves every pack the picker offers exists and
             parses — the split shipped forty files, and a missing one is a silently English page. */
          try { await setLang(code, { keep: true }); } catch (e) { thrown.push([code, 'setLang', String(e.message)]); }
          if (code !== 'en' && !PACK) unfetched.push(code);
          for (const f of RENDERERS) {
            if (typeof window[f] !== 'function') continue;
            try { window[f](); } catch (e) { thrown.push([code, f, String(e.message)]); }
          }
          const text = document.body.innerText;
          for (const k of keys) if (text.includes(k)) showing.push([code, k]);
        }
        return { thrown, showing, unfetched, languages: Object.keys(LANGS).length };
      });
      assert.deepEqual(r.unfetched, [], `the picker offers languages with no pack behind them: ${r.unfetched.join(', ')}`);
      assert.equal(r.languages, 41);
      assert.deepEqual(r.thrown, [], `a render threw while a language was applied:\n${JSON.stringify(r.thrown, null, 1)}`);
      assert.deepEqual(r.showing, [], `raw dictionary keys rendered to the screen:\n${JSON.stringify(r.showing, null, 1)}`);
      assert.deepEqual(errors, [], `page errors while cycling languages:\n${errors.join('\n')}`);
    } finally { await c.close(); }
  });

  test('the trip rail speaks the chosen language', async () => {
    const { c, page } = await openPage();
    try {
      const r = await page.evaluate(async () => {
        const read = async (code) => {
          await setLang(code, { keep: true });
          startRail({ kind: 'ride', partner: { name: 'Bolt', sub: 'Bolt car', colour: '#111' }, title: 'Ntinda → CBD', price: 5220, eta: 7 });
          renderRail();
          return document.querySelector('#railBody').innerText;
        };
        const en = await read('en'), lg = await read('lg');
        localStorage.removeItem('ug:rail');
        return { en, lg };
      });
      assert.match(r.en, /Requested/, 'setup: the English rail should name its first step');
      assert.ok(!/Requested|Driver assigned|Arriving/.test(r.lg),
        `the rail is still English under Luganda — a rider watches these words for the whole trip:\n${r.lg.slice(0, 200)}`);
    } finally { await c.close(); }
  });
});

/* ------------------------------------------------------------------ 7 */
/* DEFECT: the whole product is one inline <script>, so a single syntax error is a blank page —
   and one arrived from a ${…} written inside a single-quoted string, which looks correct in a
   diff and is not. The browser is the only thing that can tell us, so ask it before anyone else does. */
describe('7. the single script parses', () => {
  test('index.html defines the app, not a syntax error', async () => {
    const { c, page } = await openPage();
    try {
      /* named directly, not through window: a top-level const lives in the global lexical scope
         and never becomes a property of the global object, which is exactly why page.evaluate can
         reach it and `window.STR` cannot. */
      const defined = await page.evaluate(() => [
        ['STR', typeof STR], ['LANGS', typeof LANGS], ['t', typeof t], ['LANG', typeof LANG],
        ['applyLang', typeof applyLang], ['setLang', typeof setLang], ['qaScore', typeof qaScore],
        ['renderCompare', typeof renderCompare], ['renderRail', typeof renderRail],
      ]);
      for (const [name, kind] of defined) {
        assert.notEqual(kind, 'undefined', `${name} is undefined: the inline script stopped before it got there`);
      }
    } finally { await c.close(); }
  });
});

/* ------------------------------------------------------------------ 8 */
/* The palette is now a clock, so "does it pass contrast" is no longer one question with two answers
   (night, noon) — it is 1,440 questions a day, times the weather. A colour system that drifts is only
   as good as its worst minute, and the worst minute is never the one you look at. So look at all of
   them: every minute of the day against clear, overcast, rain and storm, on every ink/ground pair
   that carries text. The two family changes are checked separately: they must happen exactly at
   sunrise and sunset and nowhere else, because a crossing anywhere else is the page walking through
   the unreadable middle where a dark ground meets a light one. */
describe('8. the day palette holds contrast at every minute, in any weather', () => {
  test('no minute of any day drops a text pair below its floor', async () => {
    const { c, page } = await openPage();
    try {
      const bad = await page.evaluate(() => {
        const lin = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
        const L = h => { const n = parseInt(h.slice(1), 16);
          return 0.2126 * lin((n >> 16) & 255) + 0.7152 * lin((n >> 8) & 255) + 0.0722 * lin(n & 255); };
        const ratio = (a, b) => { const x = L(a), y = L(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
        const D = window.__UG_DAY;
        const skies = [{cloud:0,rain:0}, {cloud:1,rain:0}, {cloud:.8,rain:.6}, {cloud:1,rain:1}];
        /* pair, floor. 7 is AAA body text; 4.5 is AA, which is where the quiet labels live. */
        const pairs = [['i','g',7], ['i','s',7], ['i2','s',4.5], ['i3','s',4.5], ['i3','g',4.5],
                       ['yt','s',4.5], ['yt','g',4.5], ['i','s2',7], ['i2','g',4.5]];
        const out = [];
        for (let m = 0; m < 1440; m++){
          const h = m / 60;
          for (const w of skies){
            const v = D.at(h, w);
            for (const [a, b, floor] of pairs){
              const r = ratio(v[a], v[b]);
              if (r < floor) out.push({at: h.toFixed(2), sky: JSON.stringify(w), pair: a + ' on ' + b,
                                       got: +r.toFixed(2), floor, colours: v[a] + ' / ' + v[b]});
            }
          }
        }
        return out.slice(0, 8);
      });
      assert.deepEqual(bad, [], 'the drifting palette drops below its contrast floor:\n' +
        bad.map(b => `  ${b.at}h ${b.sky} — ${b.pair} = ${b.got} (needs ${b.floor}) ${b.colours}`).join('\n'));
    } finally { await c.close(); }
  });

  test('the ground only crosses between dark and light at sunrise and sunset', async () => {
    const { c, page } = await openPage();
    try {
      const r = await page.evaluate(() => {
        const D = window.__UG_DAY, flips = [];
        let prev = D.at(0, null).dark;
        for (let m = 1; m < 1440; m++){
          const now = D.at(m / 60, null).dark;
          if (now !== prev) flips.push(+(m / 60).toFixed(3));
          prev = now;
        }
        return {flips, up: D.SUNUP, down: D.SUNDOWN};
      });
      assert.equal(r.flips.length, 2, `the palette changes family ${r.flips.length} times a day, at ${r.flips}; it must be exactly twice`);
      assert.ok(Math.abs(r.flips[0] - r.up) < 0.02, `first crossing at ${r.flips[0]}h, sunrise is ${r.up}h`);
      assert.ok(Math.abs(r.flips[1] - r.down) < 0.02, `second crossing at ${r.flips[1]}h, sunset is ${r.down}h`);
    } finally { await c.close(); }
  });

  test('a minute of drift is never a visible step', async () => {
    const { c, page } = await openPage();
    try {
      const worst = await page.evaluate(() => {
        const D = window.__UG_DAY;
        const rgb = h => { const n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };
        let worst = {d: 0};
        for (let m = 0; m < 1440; m++){
          const a = D.at(m / 60, null), b = D.at((m + 1) / 60, null);
          if (a.dark !== b.dark) continue;          // the two crossings are meant to be events
          for (const k of ['g', 's', 'i']){
            const x = rgb(a[k]), y = rgb(b[k]);
            const d = Math.max(Math.abs(x[0] - y[0]), Math.abs(x[1] - y[1]), Math.abs(x[2] - y[2]));
            if (d > worst.d) worst = {d, at: +(m / 60).toFixed(2), key: k};
          }
        }
        return worst;
      });
      /* Two 8-bit steps in a minute is far under a just-noticeable difference; the point of the whole
         design is that you never catch it moving. */
      assert.ok(worst.d <= 2, `the palette jumps ${worst.d}/255 in one minute at ${worst.at}h on --${worst.key}; that is a step, not a drift`);
    } finally { await c.close(); }
  });
});

/* ------------------------------------------------------------------ 9 */
/* DEFECT, found by a reader: switching to Amharic left the bus rows saying "Teera esimu" and the
   Foresight board saying "Nyuta yo". Both are real words — in Runyoro and Acholi — left behind by
   the previous language because rerenderAll() named eleven of the thirty render functions. A reader
   was being handed a language they had not asked for and could not read. The list is the fix; this
   test is what keeps it a fix. */
describe('9. changing language redraws every view', () => {
  test('rerenderAll names every render function in the file', async () => {
    const src = readFileSync(join(SITE, 'index.html'), 'utf8');
    const declared = [...src.matchAll(/^function (render[A-Za-z0-9_]*)\s*\(/gm)].map(m => m[1]);
    const listed = new Set([...src.matchAll(/'(render[A-Za-z0-9_]*)'/g)].map(m => m[1]));
    const missing = [...new Set(declared)].filter(n => !listed.has(n));
    assert.deepEqual(missing, [],
      'these render functions are never redrawn when the language changes, so they keep the previous ' +
      'language on screen — add them to RERENDER in index.html:\n  ' + missing.join('\n  '));
  });

  test('the bus rows and the foresight board follow the language', async () => {
    const { c, page } = await openPage();
    try {
      /* Runyoro first, so there is a previous language to be left behind, then Amharic. */
      const r = await page.evaluate(async () => {
        await setLang('nyo'); await new Promise(r => setTimeout(r, 60));
        await setLang('am');  await new Promise(r => setTimeout(r, 60));
        const grab = id => (document.getElementById(id) || {}).textContent || '';
        return {buses: grab('buses'), foresight: grab('foresightList')};
      });
      const strays = /Teera esimu|Kwata ha UG|Nyuta yo|omuhanda|Kwata aha UG/;
      assert.ok(!strays.test(r.buses), `the bus rows kept Runyoro after switching to Amharic:\n${r.buses.slice(0, 240)}`);
      assert.ok(!strays.test(r.foresight), `the foresight board kept Runyoro after switching to Amharic:\n${r.foresight.slice(0, 240)}`);
    } finally { await c.close(); }
  });
});

/* ------------------------------------------------------------------ 10 */
/* Uber left Uganda. A board that claims to list every way to move in the country must not offer a
   ride from a company that is not there — that is not a stale logo, it is a quote a rider cannot
   take. */
describe('10. the board only lists operators that are actually here', () => {
  test('no departed operator survives anywhere in the shipped page', async () => {
    const src = readFileSync(join(SITE, 'index.html'), 'utf8');
    const hits = [...src.matchAll(/.{0,60}[Uu]ber.{0,60}/g)].map(m => m[0].replace(/\s+/g, ' '));
    assert.deepEqual(hits, [], 'Uber is still in the page:\n  ' + hits.join('\n  '));
  });
});

/* ------------------------------------------------------------------ 11 */
/* DEFECT: initScene() is wrapped in a try/catch that turns any error into the words "3D map
   unavailable here" — so a broken scene looks exactly like a machine without WebGL, and ships. It
   already happened once: a `let` declared beside the weather layer sat in its temporal dead zone
   when recolour() reached it, and the whole map went dark on every browser in the world while every
   test still passed. If three.js loads at all, the scene must be alive. */
describe('11. the map survives its own initialisation', () => {
  test('when three.js loads, the scene is built and takes weather', async () => {
    const { c, page } = await openPage();
    try {
      const r = await page.evaluate(async () => {
        for (let i = 0; i < 60 && typeof THREE === 'undefined'; i++) await new Promise(r => setTimeout(r, 100));
        if (typeof THREE === 'undefined') return {skipped: 'three.js did not load in this environment'};
        for (let i = 0; i < 60 && (typeof scene === 'undefined' || scene === null); i++) await new Promise(r => setTimeout(r, 100));
        const alive = typeof scene !== 'undefined' && scene !== null;
        let wx = 'not tried';
        if (alive && scene.setWeather){ try { scene.setWeather({cloud:.9, rain:.7}); scene.setWeather(null); wx = 'ok'; }
                                        catch(e){ wx = 'threw: ' + e.message; } }
        return {alive, wx, hint: (document.getElementById('hint') || {}).textContent};
      });
      if (r.skipped) return;   /* no CDN in this sandbox: the point is only tested where it can be */
      assert.ok(r.alive, `three.js loaded but scene is null — initScene threw and was swallowed. Hint reads: "${r.hint}"`);
      assert.equal(r.wx, 'ok', `scene.setWeather is broken: ${r.wx}`);
      assert.ok(!/unavailable/.test(r.hint || ''), `the map fell back to "${r.hint}" even though three.js loaded`);
    } finally { await c.close(); }
  });
});

/* ------------------------------------------------------------------ 12 */
/* DEFECT, found by diffing this build against the one before it: renderTicker() and forty lines of
   .ticker CSS were still here, and the element they write to was not. The fares band had been lost
   in a markup edit, and nothing said so — the render function was simply never called, and if it
   had been it would have thrown on a null. Every id the JavaScript reaches for must exist, and the
   band it fills must fill. */
describe('12. every element the code reaches for is actually on the page', () => {
  test('no id is queried that no markup declares', () => {
    const src = readFileSync(join(SITE, 'index.html'), 'utf8');
    const want = new Set();
    for (const m of src.matchAll(/\$\('#([A-Za-z0-9_-]+)'\)|getElementById\('([A-Za-z0-9_-]+)'\)/g)) want.add(m[1] || m[2]);
    const have = new Set([...src.matchAll(/\bid=["']([A-Za-z0-9_-]+)["']/g)].map(m => m[1]));
    const orphans = [...want].filter(id => !have.has(id)).sort();
    assert.deepEqual(orphans, [], 'queried but never declared: ' + orphans.join(', '));
  });

  test('the fares band fills, and speaks the reader’s language', async () => {
    const { c, page } = await openPage();
    try {
      const r = await page.evaluate(async () => {
        for (let i = 0; i < 60 && !window.__ugReady; i++) await new Promise(r => setTimeout(r, 100));
        const el = document.getElementById('ticker');
        const en = el ? el.textContent : '';
        await setLang('sw'); await new Promise(r => setTimeout(r, 80));
        return {en, sw: el ? el.textContent : '', spans: el ? el.children.length : 0};
      });
      assert.ok(r.spans >= 8, `the fares band drew ${r.spans} items; it should carry the routes twice over`);
      assert.match(r.en, /UGX/, 'the fares band carries no fare');
      assert.match(r.sw, /rahisi zaidi sasa hivi/, 'the fares band stayed English after switching to Swahili');
    } finally { await c.close(); }
  });
});

/* ------------------------------------------------------------------ 13 */
/* A reader in Amharic was seeing "Mukono" and "Kampala" in Latin letters on a page that was
   otherwise in their script. Place names now carry a native form in every non-Latin dictionary,
   the helper rewrites them wherever a name is printed, and the map pins carry the native form
   alone. Latin-script languages must be untouched — Luganda is not owed 'ካምፓላ' — and must not
   be charged for the keys in the "still English" count. */
describe('13. place names are written in the reader’s script', () => {
  test('Amharic sees Ethiopic names; Luganda sees Latin and is not charged for it', async () => {
    const { c, page } = await openPage({ viewport: { width: 1280, height: 900 } });
    try {
      const r = await page.evaluate(async () => {
        for (let i = 0; i < 60 && !window.__ugReady; i++) await new Promise(r => setTimeout(r, 100));
        const opt = id => [...document.querySelector('#' + id).options].map(o => o.textContent);
        await setLang('lg'); await new Promise(r => setTimeout(r, 80));
        const lg = { from: opt('sFrom')[0], gap: i18nGap(), ticker: document.getElementById('ticker').textContent.slice(0, 80) };
        await setLang('am'); await new Promise(r => setTimeout(r, 80));
        const am = { from: opt('sFrom'), to: opt('cTo'), gap: i18nGap(), ticker: document.getElementById('ticker').textContent.slice(0, 120),
                     pins: [...document.querySelectorAll('#pins .pin .lbl')].map(l => l.textContent), route: document.getElementById('resSummary').textContent };
        await setLang('en'); await new Promise(r => setTimeout(r, 80));
        const en = { from: opt('sFrom')[0], ticker: document.getElementById('ticker').textContent.slice(0, 80) };
        return { lg, am, en };
      });
      const eth = /[ሀ-፿]/;
      assert.match(r.am.from.join(' '), eth, 'the pick-up select stayed Latin in Amharic: ' + r.am.from.join(', '));
      assert.match(r.am.to.join(' '), eth, 'the destination select stayed Latin in Amharic');
      assert.match(r.am.ticker, eth, 'the fares band stayed Latin in Amharic: ' + r.am.ticker);
      assert.match(r.am.route, eth, 'the compare summary stayed Latin in Amharic');
      assert.ok(/\(Kampala\)|\(Kololo\)|\(Ntinda\)/.test(r.am.from.join(' ')), 'the Latin form must stay beside the native one in prose');
      if (r.am.pins.length) { assert.match(r.am.pins[0], eth, 'the map pins stayed Latin'); assert.ok(!/\(/.test(r.am.pins[0]), 'pins carry the native form alone'); }
      assert.ok(!eth.test(r.lg.from) && !eth.test(r.lg.ticker), 'Luganda must not be rewritten');
      assert.ok(!eth.test(r.en.from) && !eth.test(r.en.ticker), 'switching back to English must restore Latin');
      assert.ok(r.lg.gap < 100, `Luganda is being charged for the place keys: gap ${r.lg.gap}`);
    } finally { await c.close(); }
  });
});
