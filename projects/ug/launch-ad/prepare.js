#!/usr/bin/env node
/* Stage a render root for the shoot.

   The film is captured from the real ../site/index.html in a real browser — nothing here
   redraws the product. But the page fetches three.js from cdnjs at runtime, and a render
   machine may have no route to it, in which case the map beat would be a black rectangle
   and the ad would be quietly wrong rather than loudly broken. So the render root is a
   copy of the site with one line changed, and only when a local copy of three.js is
   actually present:

     vendor/three.min.js exists   ->  THREE_SRC points at it, and the render is offline
     vendor/three.min.js missing  ->  the CDN URL is left alone, and the page needs network

   See README.md for how to get three.js r128 onto a machine with no route to a CDN.

     node prepare.js [--out .render]
*/
const fs = require('fs'), path = require('path');

const args = Object.fromEntries(process.argv.slice(2)
  .map((a, i, arr) => a.startsWith('--') ? [a.slice(2), arr[i + 1]] : []).filter(x => x.length));
const HERE = __dirname;
const SITE = path.join(HERE, '..', 'site');
const OUT = path.resolve(args.out || path.join(HERE, '.render'));
const VENDOR = path.join(HERE, 'vendor', 'three.min.js');
const CDN = "const THREE_SRC = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';";

fs.rmSync(OUT, { recursive: true, force: true });
fs.cpSync(SITE, OUT, { recursive: true });
// The plates and the score harness are served from the same origin, so the whole
// production needs one server rather than three. ug-score.js is taken from the showreel
// rather than copied into this directory: there is one score engine in this repo.
for (const f of ['captions.html', 'endcard.html', 'score.html']) fs.copyFileSync(path.join(HERE, f), path.join(OUT, f));
fs.copyFileSync(path.join(HERE, '..', 'showreel', 'ug-score.js'), path.join(OUT, 'ug-score.js'));

const idx = path.join(OUT, 'index.html');
let html = fs.readFileSync(idx, 'utf8');
if (fs.existsSync(VENDOR)) {
  if (!html.includes(CDN)) { console.error('prepare: THREE_SRC line not found in site/index.html'); process.exit(1); }
  fs.copyFileSync(VENDOR, path.join(OUT, 'three.min.js'));
  html = html.replace(CDN, "const THREE_SRC = 'three.min.js';  /* vendored: see launch-ad/README.md */");
  fs.writeFileSync(idx, html);
  console.log(`prepared ${OUT} (three.js vendored, renders offline)`);
} else {
  console.log(`prepared ${OUT} (no vendor/three.min.js: the map beat needs a route to cdnjs)`);
}
