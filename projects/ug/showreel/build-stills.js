#!/usr/bin/env node
/* Marketing stills: 4K frames from the showreel (deterministic render at chosen seconds) and 2x stills of the
   site's key screens, dark and light, desktop and phone. PNG, no player chrome.
   node build-stills.js [--out ../marketing] */
const fs = require('fs'), path = require('path');
const args = Object.fromEntries(process.argv.slice(2).map((a, i, arr) => a.startsWith('--') ? [a.slice(2), arr[i + 1]] : []).filter(x => x.length));
const OUT = path.resolve(args.out || path.join(__dirname, '..', 'marketing'));
const PW = process.env.PLAYWRIGHT_MODULE || '/opt/node22/lib/node_modules/playwright';
const CHROME = process.env.CHROMIUM || '/opt/pw-browsers/chromium';
const THREE = process.env.THREE_LOCAL; // optional local three.min.js when the CDN is unreachable
fs.mkdirSync(OUT, { recursive: true });

/* seconds into the long cut worth a poster */
const REEL_STILLS = [
  ['01-map-assembles', 6.2], ['02-ug-lock', 11.6], ['03-four-verbs', 15.2], ['04-one-crest', 34.0], ['05-the-desk-ranked', 52.0],
  ['06-virtual-stage', 84.0], ['07-the-drop-funded', 102.0], ['08-comfort-map', 120.0], ['09-signature', 142.0], ['10-parcel-in-the-boot', 165.0],
  ['11-the-atlas', 188.0], ['12-the-pearl', 212.0], ['13-tazama-dock', 232.0], ['14-one-link', 268.0],
];

async function main() {
  const { chromium } = require(PW);
  const browser = await chromium.launch({ executablePath: CHROME, args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--font-render-hinting=none'] });
  // 1. reel frames at 3840x2160
  let page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2, colorScheme: 'dark' });
  await page.goto('file://' + path.join(__dirname, 'index.html'), { waitUntil: 'load' });
  await page.waitForTimeout(1500);
  const stage = await page.$('#stage');
  for (const [name, sec] of REEL_STILLS) {
    await page.evaluate(s => window.__UG_REEL.render(s), sec);
    await page.waitForTimeout(80);
    await stage.screenshot({ path: path.join(OUT, `reel-${name}.png`), type: 'png' });
    console.log('reel', name);
  }
  await page.close();
  // 2. site screens
  const site = 'file://' + path.join(__dirname, '..', 'site', 'index.html');
  const shots = [
    ['site-hero-desktop', { width: 1600, height: 1000 }, 'dark', '#top', null],
    ['site-hero-desktop-light', { width: 1600, height: 1000 }, 'light', '#top', null],
    ['site-desk-desktop', { width: 1600, height: 1000 }, 'dark', '#compare', null],
    ['site-atlas-desktop', { width: 1600, height: 1000 }, 'dark', '#atlas', () => { document.querySelector('#atlas').open = true; }],
    ['site-stage-desktop', { width: 1600, height: 1000 }, 'dark', '#stage', null],
    ['site-drive-desktop', { width: 1600, height: 1000 }, 'dark', '#drive', () => { document.querySelector('#foresight').open = true; }],
    ['site-hero-phone', { width: 390, height: 844 }, 'dark', '#top', null],
    ['site-desk-phone', { width: 390, height: 844 }, 'dark', '#compare', null],
    ['site-stage-phone', { width: 390, height: 844 }, 'dark', '#stage', null],
    ['site-install-phone', { width: 390, height: 844 }, 'dark', '#install', null],
  ];
  for (const [name, vp, scheme, sel, pre] of shots) {
    page = await browser.newPage({ viewport: vp, deviceScaleFactor: 2, colorScheme: scheme });
    if (THREE) await page.route('**/three.js/r128/three.min.js', r => r.fulfill({ path: THREE, contentType: 'application/javascript' }));
    await page.goto(site, { waitUntil: 'load' });
    /* Dismiss BOTH gates. The welcome screen shipped after this script was written, so every
       site-* still since then has been a photograph of the language picker filed under the name
       of the screen it was supposed to show. */
    await page.evaluate(() => {
      try { sessionStorage.setItem('ug:intro', '1'); localStorage.setItem('ug:welcomed', '1'); } catch (e) {}
      const i = document.querySelector('#intro'); if (i) i.remove();
      const w = document.querySelector('#welcome'); if (w) { w.hidden = true; w.remove(); }
    });
    if (scheme === 'light') await page.evaluate(() => { document.documentElement.dataset.theme = 'light'; });
    await page.waitForTimeout(2600);
    if (pre) await page.evaluate(pre);
    await page.evaluate(s => document.querySelector(s).scrollIntoView({ block: 'start' }), sel);
    await page.waitForTimeout(1200);
    await page.evaluate(() => document.querySelectorAll('.rv').forEach(e => { e.style.opacity = 1; e.style.transform = 'none'; e.style.filter = 'none'; }));
    await page.screenshot({ path: path.join(OUT, `${name}.png`), type: 'png' });
    console.log('site', name);
    await page.close();
  }
  await browser.close();
  for (const f of fs.readdirSync(OUT).sort()) console.log(f.padEnd(40), (fs.statSync(path.join(OUT, f)).size / 1e6).toFixed(2), 'MB');
}
main().catch(e => { console.error(e); process.exit(1); });
