#!/usr/bin/env node
/* index.html is the source of the showreel. This writes the other three cuts from it:
   sound.html (long, with sound), short.html (short, silent), short-sound.html (short, with sound).
   Run: node build.js */
const fs = require('fs'), path = require('path');
const src = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
const SOUND_LINE = "const SOUND = params.get('sound') === '1';";
if (!src.includes(SOUND_LINE)) throw new Error('index.html changed: SOUND line not found');
const CUT_LINE = "const CUT = (typeof FORCE_CUT!=='undefined' && FORCE_CUT) || params.get('cut') || 'long';";
if (!src.includes(CUT_LINE)) throw new Error('index.html changed: CUT line not found');
const variants = {
  'sound.html': { title: 'UG Showreel with Sound', sound: true, cut: 'long' },
  'short.html': { title: 'UG Short Cut', sound: false, cut: 'short' },
  'short-sound.html': { title: 'UG Short Cut with Sound', sound: true, cut: 'short' },
  'short-cam.html': { title: 'UG Short Cut · Camera', sound: false, cut: 'short', cam: true },
  'short-cam-sound.html': { title: 'UG Short Cut · Camera · Sound', sound: true, cut: 'short', cam: true },
};
for (const [file, v] of Object.entries(variants)) {
  let out = src.replace('<title>UG Showreel</title>', `<title>${v.title}</title>`)
    .replace(SOUND_LINE, `const SOUND = ${v.sound}; // ${v.sound ? 'the sound cut' : 'silent'}`)
    .replace(CUT_LINE, `const FORCE_CUT = '${v.cut}';${v.cam ? " const FORCE_CAM = true;" : ''}\n${CUT_LINE}`);
  fs.writeFileSync(path.join(__dirname, file), out);
  console.log(file, out.length);
}
