#!/usr/bin/env node
/* Render the showreel to MP4 files: long and short, silent and with sound.
   Frames are drawn deterministically through window.__UG_REEL.render(sec) in headless Chromium and
   piped to ffmpeg; the score is rendered offline with the same generative engine (ug-score.js) and
   muxed in. Narration: if voice/manifest.json exists (see voice/README.md) the rendered Ugandan
   voice files are mixed at each scene's start; otherwise the sound cuts carry music and captions
   only, because the browser's placeholder voice cannot be captured to a file.

   node build-video.js [--cut long|short|all] [--sound on|off|all] [--fps 24] [--out dist] [--quality 90]
   Needs: Playwright with Chromium, and ffmpeg (FFMPEG env, or imageio-ffmpeg's binary on PATH). */
const fs = require('fs'), path = require('path'), { spawn, execSync } = require('child_process');
const args = Object.fromEntries(process.argv.slice(2).map((a, i, arr) => a.startsWith('--') ? [a.slice(2), arr[i + 1]] : []).filter(x => x.length));
const FPS = +(args.fps || 30), W = +(args.w || 1920), H = +(args.h || 1080), Q = +(args.quality || 95), CRF = args.crf || '17';
const OUT = path.resolve(args.out || path.join(__dirname, 'dist'));
const PW = process.env.PLAYWRIGHT_MODULE || '/opt/node22/lib/node_modules/playwright';
const CHROME = process.env.CHROMIUM || '/opt/pw-browsers/chromium';
const FFMPEG = process.env.FFMPEG || (() => { try { return execSync('python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"').toString().trim(); } catch (e) { return 'ffmpeg'; } })();
const cuts = args.cut === 'all' || !args.cut ? ['long', 'short'] : [args.cut];
const sounds = args.sound === 'all' || !args.sound ? [false, true] : [args.sound === 'on'];
fs.mkdirSync(OUT, { recursive: true });

async function main() {
  const { chromium } = require(PW);
  const browser = await chromium.launch({ executablePath: CHROME, args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required', '--disable-gpu-vsync', '--font-render-hinting=none'] });
  for (const cut of cuts) {
    const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1, colorScheme: 'dark' });
    page.on('pageerror', e => console.error('PAGEERROR', e.message));
    const file = cut === 'short-cam' ? 'short-cam-sound.html' : cut === 'short' ? 'short-sound.html' : 'sound.html';
    await page.goto('file://' + path.join(__dirname, file), { waitUntil: 'load' });
    await page.waitForTimeout(1500); // fonts
    const total = await page.evaluate(() => window.__UG_REEL.total);
    const frames = Math.ceil(total * FPS);
    console.log(`[${cut}] ${total.toFixed(1)} s, ${frames} frames at ${FPS} fps`);
    // 1. video-only pass
    const silent = path.join(OUT, `ug-showreel-${cut}-silent.mp4`);
    const ff = spawn(FFMPEG, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', CRF, '-profile:v', 'high', '-level', '4.1', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-movflags', '+faststart', silent], { stdio: ['pipe', 'inherit', 'inherit'] });
    const stage = await page.$('#stage');
    const t0 = Date.now();
    for (let f = 0; f < frames; f++) {
      await page.evaluate(sec => window.__UG_REEL.render(sec), f / FPS);
      const buf = await stage.screenshot({ type: 'jpeg', quality: Q });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (f % (FPS * 10) === 0) console.log(`  ${(f / FPS).toFixed(0)} s / ${total.toFixed(0)} s  (${((Date.now() - t0) / 1000).toFixed(0)} s elapsed)`);
    }
    ff.stdin.end();
    await new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error('ffmpeg exit ' + c))));
    console.log('  wrote', silent);
    if (!sounds.includes(true)) { await page.close(); continue; }
    // 2. the music: a produced track in music/<cut>.mp3 when it exists (music/BRIEF.md), else the score rendered offline with the same engine
    const produced = path.join(__dirname, 'music', `${cut}.mp3`);
    const offsets = await page.evaluate(() => window.__UG_REEL.offsets);
    let wav = path.join(OUT, `ug-score-${cut}.wav`);
    if (fs.existsSync(produced)) { wav = produced; console.log('  music: produced track', produced); } else {
    const b64 = await page.evaluate(async ({ total, offsets, cut }) => {
      const sr = 48000, oc = new OfflineAudioContext(2, Math.ceil(sr * (total + 1)), sr);
      const g = oc.createGain(); g.gain.value = 1; g.connect(oc.destination);
      const sc = window.UGScore.create(oc, g);
      sc.play(cut.startsWith('short') ? 'short' : 'long');
      const step = 0.05; let next = 0;
      const plan = [];
      for (let t = step; t < total; t += step) plan.push(t);
      plan.forEach(t => oc.suspend(t).then(() => { if (!cut.startsWith('short')) { while (next < offsets.length && offsets[next] <= t + 1e-6) { sc.cue(next); next++; } } sc.tick(); oc.resume(); }));
      if (!cut.startsWith('short')) sc.cue(0);
      sc.tick();
      const buf = await oc.startRendering();
      // fade the tail, encode 16-bit PCM WAV
      const n = buf.length, ch = buf.numberOfChannels, out = new DataView(new ArrayBuffer(44 + n * ch * 2));
      const str = (o, s) => { for (let i = 0; i < s.length; i++) out.setUint8(o + i, s.charCodeAt(i)); };
      str(0, 'RIFF'); out.setUint32(4, 36 + n * ch * 2, true); str(8, 'WAVE'); str(12, 'fmt '); out.setUint32(16, 16, true); out.setUint16(20, 1, true); out.setUint16(22, ch, true); out.setUint32(24, sr, true); out.setUint32(28, sr * ch * 2, true); out.setUint16(32, ch * 2, true); out.setUint16(34, 16, true); str(36, 'data'); out.setUint32(40, n * ch * 2, true);
      const data = [buf.getChannelData(0), buf.getChannelData(1)];
      const fadeFrom = Math.floor((total - 1.2) * sr);
      let o = 44;
      for (let i = 0; i < n; i++) { const fade = i > fadeFrom ? Math.max(0, 1 - (i - fadeFrom) / (1.2 * sr)) : 1; for (let c = 0; c < ch; c++) { const v = Math.max(-1, Math.min(1, data[c][i] * fade)); out.setInt16(o, v < 0 ? v * 32768 : v * 32767, true); o += 2; } }
      const bytes = new Uint8Array(out.buffer); let s = ''; const CH = 0x8000;
      for (let i = 0; i < bytes.length; i += CH) s += String.fromCharCode.apply(null, bytes.subarray(i, i + CH));
      return btoa(s);
    }, { total, offsets, cut });
    fs.writeFileSync(wav, Buffer.from(b64, 'base64'));
    console.log('  score', wav, (fs.statSync(wav).size / 1e6).toFixed(1), 'MB'); }
    // 3. narration, if rendered Ugandan voice files exist
    const manifestPath = path.join(__dirname, 'voice', 'manifest.json');
    const ids = await page.evaluate(() => window.__UG_REEL.voiceLines.map(v => v.id));
    const inputs = ['-i', silent, '-i', wav]; let filter = '[1:a]volume=1.0[m]'; let mixIn = '[m]'; let k = 2; let voiced = false;
    if (fs.existsSync(manifestPath)) {
      const man = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
      let idx = 0; const labels = [];
      ids.forEach((id, i) => { const sc = man.scenes.find(s => s.id === id); if (!sc) return; let at = offsets[i] + 0.9; sc.files.forEach(fl => { const p = path.join(__dirname, 'voice', fl.file); if (!fs.existsSync(p)) return; inputs.push('-i', p); filter += `;[${k}:a]adelay=${Math.round(at * 1000)}|${Math.round(at * 1000)},volume=1.6[v${idx}]`; labels.push(`[v${idx}]`); at += (fl.seconds || 3) + 0.35; k++; idx++; }); });
      if (labels.length) { filter += `;${labels.join('')}amix=inputs=${labels.length}:normalize=0[vo];[m]sidechaincompress=threshold=0.05:ratio=6:attack=40:release=400[md];[md][vo]amix=inputs=2:normalize=0[mix]`; mixIn = '[mix]'; voiced = true; }
    }
    const sound = path.join(OUT, `ug-showreel-${cut}-sound.mp4`);
    execSync([FFMPEG, '-y', '-loglevel', 'error', ...inputs, '-filter_complex', `"${filter}"`, '-map', '0:v', '-map', `"${mixIn}"`, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-shortest', '-movflags', '+faststart', sound].join(' '), { stdio: 'inherit' });
    console.log('  wrote', sound, voiced ? '(music + rendered Ugandan narration)' : '(music + captions; narration joins once voice/ is rendered)');
    await page.close();
  }
  await browser.close();
  for (const f of fs.readdirSync(OUT)) console.log(f.padEnd(36), (fs.statSync(path.join(OUT, f)).size / 1e6).toFixed(1), 'MB');
}
main().catch(e => { console.error(e); process.exit(1); });
