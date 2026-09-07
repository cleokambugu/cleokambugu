/* Render 6 s of the UG score for the bumper cut, offline and deterministically.
   ug-score.js is the sound panel's engine (SCORE.md): 114 BPM, A minor pentatonic,
   kidandali / Afro-house — log drum, shekere, clave, congas, an adungu-ish pluck and
   an endingidi-style lead, all synthesised, no samples and no network.

   The six-second bumper needs its own cue sheet, so SHORT[0] is replaced in place before
   play('short') reads it. It opens already inside the groove — a bumper has no room for
   an intro — and lands the finale on the crest:
     0.00  impact, break — the app greets back in Luganda
     0.60  impact, groove — the turn
     1.53  drop — the compare desk
     3.07  up a tone — the Virtual Stage
     4.10  outro under the end card, finale hit at 5.10
*/
const fs = require('fs'), path = require('path');
const PW = process.env.PLAYWRIGHT_MODULE || '/opt/node22/lib/node_modules/playwright';
const CHROME = process.env.CHROMIUM || '/opt/pw-browsers/chromium';
const URL = process.env.SITE_URL || 'http://127.0.0.1:8811';
const { chromium } = require(PW);
const OUT = path.join(__dirname, 'audio');
const TOTAL = 6.4;

const PROGRAM = [
  { at: 0,    impact: 1, lvl: 'break' },        // 0.00  the app greets back in Luganda
  { at: 0.60, impact: 1, lvl: 'groove' },       // 0.60  the turn
  { at: 1.53, lvl: 'drop', lead: 1 },           // 1.53  the compare desk
  { at: 3.07, lvl: 'full', key: 2, lead: 1 },   // 3.07  the Virtual Stage
  { at: 4.10, lvl: 'outro', key: 0, lead: 1 },  // 4.10  the crest
  { at: 5.10, fin: 1 },
];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({
    executablePath: CHROME,
    args: ['--autoplay-policy=no-user-gesture-required'],
  });
  const page = await browser.newPage();
  page.on('pageerror', e => console.error('PAGEERROR', e.message));
  await page.goto(URL + '/score.html', { waitUntil: 'load' });
  await page.waitForFunction(() => !!window.UGScore, null, { timeout: 20000 });

  const b64 = await page.evaluate(async ({ total, program }) => {
    const sr = 48000;
    const oc = new OfflineAudioContext(2, Math.ceil(sr * total), sr);
    const g = oc.createGain(); g.gain.value = 1; g.connect(oc.destination);
    const sc = window.UGScore.create(oc, g);
    // swap the ad's cue sheet into the array play() will read
    sc.programs.short[0].splice(0, sc.programs.short[0].length, ...program);
    sc.play('short');
    const step = 0.05;
    for (let t = step; t < total; t += step) oc.suspend(t).then(() => { sc.tick(); oc.resume(); });
    sc.tick();
    const buf = await oc.startRendering();

    const n = buf.length, ch = buf.numberOfChannels;
    const out = new DataView(new ArrayBuffer(44 + n * ch * 2));
    const str = (o, s) => { for (let i = 0; i < s.length; i++) out.setUint8(o + i, s.charCodeAt(i)); };
    str(0, 'RIFF'); out.setUint32(4, 36 + n * ch * 2, true); str(8, 'WAVE'); str(12, 'fmt ');
    out.setUint32(16, 16, true); out.setUint16(20, 1, true); out.setUint16(22, ch, true);
    out.setUint32(24, sr, true); out.setUint32(28, sr * ch * 2, true);
    out.setUint16(32, ch * 2, true); out.setUint16(34, 16, true);
    str(36, 'data'); out.setUint32(40, n * ch * 2, true);
    const data = [buf.getChannelData(0), buf.getChannelData(1)];
    const fadeIn = Math.floor(0.25 * sr);              // no click on the first sample
    const fadeFrom = Math.floor((total - 1.0) * sr);
    let o = 44, peak = 0;
    for (let i = 0; i < n; i++) {
      let f = 1;
      if (i < fadeIn) f = i / fadeIn;
      if (i > fadeFrom) f = Math.min(f, Math.max(0, 1 - (i - fadeFrom) / (1.0 * sr)));
      for (let c = 0; c < ch; c++) {
        const v = Math.max(-1, Math.min(1, data[c][i] * f));
        peak = Math.max(peak, Math.abs(v));
        out.setInt16(o, v < 0 ? v * 32768 : v * 32767, true); o += 2;
      }
    }
    const bytes = new Uint8Array(out.buffer); let s = ''; const CH = 0x8000;
    for (let i = 0; i < bytes.length; i += CH) s += String.fromCharCode.apply(null, bytes.subarray(i, i + CH));
    return { b64: btoa(s), peak };
  }, { total: TOTAL, program: PROGRAM });

  const wav = path.join(OUT, 'ug-bumper-score.wav');
  fs.writeFileSync(wav, Buffer.from(b64.b64, 'base64'));
  console.log('score', wav, (fs.statSync(wav).size / 1e6).toFixed(2), 'MB, peak', b64.peak.toFixed(3));
  await browser.close();
})();
