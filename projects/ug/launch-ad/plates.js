/* Render the burnt-in caption plates and the end card at one size.

     node plates.js 1920 1080 16x9
     node plates.js 1080 1920 9x16
     node plates.js 1080 1080 1x1

   captions.html and endcard.html read their size off the query string and re-set
   themselves for it — the phone plates are composed at phone scale, not the 16:9 plates
   dropped into a tall box, which is the difference between a caption that reads in a feed
   and one that does not. Output lands in plates/<tag>/.

   Needs Playwright with Chromium and a server for the render root (see README.md). */
const fs = require('fs'), path = require('path');
const PW = process.env.PLAYWRIGHT_MODULE || '/opt/node22/lib/node_modules/playwright';
const CHROME = process.env.CHROMIUM || '/opt/pw-browsers/chromium';
const URL = process.env.SITE_URL || 'http://127.0.0.1:8811';
const { chromium } = require(PW);
const W = +process.argv[2], H = +process.argv[3], TAG = process.argv[4];
const OUT = path.join(__dirname, 'plates', TAG || `${W}x${H}`);

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await chromium.launch({
    executablePath: CHROME,
    args: ['--font-render-hinting=none', '--disable-lcd-text'],
  });
  const p = await b.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });

  for (const i of [0, 1, 2, 3]) {
    await p.goto(`${URL}/captions.html?w=${W}&h=${H}&i=${i}`, { waitUntil: 'load' });
    await p.waitForTimeout(2200);                        // let Archivo land before the shutter
    await p.screenshot({ path: path.join(OUT, `cap${i}.png`), omitBackground: true });
  }
  await p.goto(`${URL}/endcard.html?w=${W}&h=${H}`, { waitUntil: 'load' });
  await p.waitForTimeout(2200);
  await p.screenshot({ path: path.join(OUT, 'card.png') });

  console.log(`plates ${W}x${H} -> ${OUT}`);
  await b.close();
})();
