/* UG showreel score — generative WebAudio, no samples.
   window.UGScore.create(ctx, destGain) -> { play(cut), cue(i), stop(), duck(on), tick() }
   Amapiano / afrobeats / kidandali flavoured: log drum, swung shakers, 3-2 clave, congas,
   offbeat guitar skank, pentatonic "UG theme" pluck, endingidi-style lead, warm pad, risers. */
(function () {
  'use strict';
  var BPM = 114, LOOK = 0.1, TICK = 25, SWING = 0.17;
  var S16 = 60 / BPM / 4, BAR = S16 * 16;

  /* ---- levels: which layers are alive and how loud (0..1.3) ---- */
  var LEVELS = {
    off:    {},
    pad:    { pad: 1, pluck: 1, solo: 1 },
    sparse: { pad: 1, pluck: 1, shaker: .55, clave: .8, log: .6, shek: .8 },
    groove: { pad: 1, pluck: 1, shaker: 1, clave: 1, log: 1, shek: 1, kick: 1, hat: .6, conga: 1 },
    full:   { pad: .9, pluck: 1, shaker: 1, clave: 1, log: 1, shek: 1, kick: 1, hat: 1, conga: 1, clap: 1, skank: 1 },
    drop:   { pad: .8, pluck: 1, shaker: 1, clave: 1, log: 1.15, shek: 1, kick: 2, hat: 1, ohat: 1, conga: 1, clap: 1, skank: 1, lead: 1 },
    outro:  { pad: 1, pluck: 1, solo: 1, shek: .5, lead: 1 }
  };

  /* ---- programs: per scene (long cut) or whole piece (short cut). at = seconds since cue ---- */
  var LONG = [
    [{ at: 0, lvl: 'pad' }, { at: 8, riser: 2.6 }, { at: 10.6, impact: 1, lvl: 'groove' }, { at: 15.5, lvl: 'full' }],   // 0 opening: map assembles, U+G lock at 10.55
    [{ at: 0, lvl: 'sparse', key: -2 }, { at: 11.4, lvl: 'groove', key: 0 }],                                          // 1 problem: three apps -> one crest
    [{ at: 0, lvl: 'groove', skank: 1 }, { at: 12, lvl: 'full' }],                                                      // 2 ride: compare desk, Book on UG
    [{ at: 0, lvl: 'groove' }, { at: 19, lvl: 'full' }, { at: 27.8, riser: 2.2 }, { at: 30, impact: 1, lvl: 'drop' }],  // 3 pool: virtual stage fills -> drop
    [{ at: 0, lvl: 'full' }],                                                                                           // 4 drive / offers
    [{ at: 0, lvl: 'groove', lead: 1, skank: 0 }],                                                                      // 5 rent / signature: fiddle over the fleet
    [{ at: 0, lvl: 'full', conga: 1.3 }],                                                                               // 6 deliver: heavier hand percussion
    [{ at: 0, lvl: 'groove', key: 2, lead: 1 }, { at: 6, lvl: 'full', key: 2, lead: 1 }, { at: 14, riser: 2.2 }, { at: 16.3, impact: 1, lvl: 'drop', key: 2, lead: 1 }], // 7 atlas: air/water/rail, up to B
    [{ at: 0, lvl: 'sparse', key: 2, lead: 1 }, { at: 10, lvl: 'groove', key: 2, lead: 1 }],                            // 8 explore / foresight
    [{ at: 0, lvl: 'groove', key: 0 }],                                                                                 // 9 plug-ins / languages: back home to A
    [{ at: 0, lvl: 'full' }],                                                                                           // 10 stay on UG / teleport
    [{ at: 0, lvl: 'groove' }, { at: 8, lvl: 'outro', lead: 1 }, { at: 12.4, fin: 1 }]                                  // 11 one link / close
  ];
  var SHORT = [[{ at: 0, lvl: 'pad' }, { at: 5.8, riser: 2.6 }, { at: 8.4, impact: 1, lvl: 'groove' }, { at: 16, lvl: 'full', skank: 1 },
    { at: 34.75, lvl: 'groove' }, { at: 47.5, riser: 2.2 }, { at: 49.75, impact: 1, lvl: 'drop' },
    { at: 54.75, lvl: 'full', key: 2, lead: 1 }, { at: 62.7, riser: 2.2 }, { at: 64.9, impact: 1, lvl: 'drop', key: 2, lead: 1 },
    { at: 73.5, lvl: 'groove', key: 0 }, { at: 78, lvl: 'outro', lead: 1 }, { at: 83.8, fin: 1 }, { at: 86.5, lvl: 'off' }]];  // short cut, 86 s: opening 16 (UG lock 8.4), ride, pool (drop 49.75), atlas (lift 64.9), close

  /* ---- patterns, in 16th steps of a bar ---- */
  var CHORD_ROOT = [0, 8, 3, -2];                                        // Am  F  C  G (semitones from key root)
  var CHORDS = [[0, 3, 7, 10], [-4, 0, 3, 7], [3, 7, 10, 14], [-2, 2, 5, 10]];
  var LOG = [[[3, 0, .9], [6, 0, 1], [10, 7, .8], [12, 0, .9], [14, 5, .7]],
             [[3, 0, .9], [6, 0, 1], [8, 7, .7], [10, 5, .8], [13, 0, .8], [15, 3, .6]]];
  var CLAVE = [0, 3, 6, 10, 12];                                          // 3-2 son clave
  var SHK = [1, .35, .6, .45];                                            // shaker accent cycle
  var CONGA = [[0, 'l', .5], [2, 'l', .4], [4, 's', .9], [8, 'l', .5], [10, 'l', .4], [12, 's', .8], [14, 'o', 1], [15, 'o', .9]];
  var MOTIF = [[0, 0], [3, 3], [6, 5], [10, 7], [12, 10], [16, 7], [19, 5], [22, 3], [26, 0], [28, -2]]; // A minor pentatonic, clave-shaped

  /* entries with only a one-shot (riser / impact / fin) inherit the level and overrides of the entry before them */
  LONG.concat(SHORT).forEach(function (p) { for (var i = 1; i < p.length; i++) if (!p[i].lvl) for (var k in p[i - 1]) if (!(k in p[i]) && k !== 'at' && k !== 'riser' && k !== 'impact' && k !== 'fin') p[i][k] = p[i - 1][k]; });

  function hz(base, semi) { return base * Math.pow(2, semi / 12); }

  function create(ctx, dest) {
    var noise = mkNoise(ctx, 2), imp = mkImpulse(ctx, 2.2);
    var G = null, timer = null, mode = null, prog = null, cueT = 0, nextStep = 0, stepN = 0, fired = null, ducked = false, curKey = 0;

    function gain(v, to) { var g = ctx.createGain(); g.gain.value = v; if (to) g.connect(to); return g; }
    function mkNoise(c, s) { var b = c.createBuffer(1, c.sampleRate * s, c.sampleRate), d = b.getChannelData(0); for (var i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1; return b; }
    function mkImpulse(c, s) { var n = c.sampleRate * s, b = c.createBuffer(2, n, c.sampleRate); for (var ch = 0; ch < 2; ch++) { var d = b.getChannelData(ch); for (var i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / n, 2.6); } return b; }

    /* ---- graph: sustained voices + buses ---- */
    function build() {
      var out = gain(ducked ? .4 : 1, dest), trim = gain(.38, out);
      var lim = ctx.createDynamicsCompressor(); lim.threshold.value = -8; lim.knee.value = 3; lim.ratio.value = 20; lim.attack.value = .001; lim.release.value = .12; lim.connect(trim);
      var comp = ctx.createDynamicsCompressor(); comp.threshold.value = -16; comp.ratio.value = 3; comp.attack.value = .006; comp.release.value = .18; comp.connect(lim);
      var rev = ctx.createConvolver(); rev.buffer = imp; var revG = gain(.22, comp); rev.connect(revG);
      var sc = gain(1, comp);                                              // sidechain bus: pad, log, skank, pluck pump under the kick
      var pad = gain(0, sc), padF = ctx.createBiquadFilter(); padF.type = 'lowpass'; padF.frequency.value = 560; padF.Q.value = .7; padF.connect(pad);
      var padSend = gain(.5, rev); padF.connect(padSend);
      var oscs = [], i;
      for (i = 0; i < 4; i++) { var o = ctx.createOscillator(); o.type = 'sawtooth'; o.detune.value = (i % 2 ? 7 : -7); var g = gain(i < 2 ? .07 : .045, padF); o.connect(g); o.start(); oscs.push(o); }
      var sub = ctx.createOscillator(); sub.type = 'sine'; sub.connect(gain(.11, padF)); sub.start();
      var lfo = ctx.createOscillator(); lfo.frequency.value = .09; var lg = gain(160, padF.frequency); lfo.connect(lg); lfo.start();
      /* endingidi-style lead: saw -> nasal bandpass, vibrato, slow attack */
      var lead = ctx.createOscillator(); lead.type = 'sawtooth'; var lf = ctx.createBiquadFilter(); lf.type = 'bandpass'; lf.frequency.value = 1100; lf.Q.value = 3.2;
      var leadG = gain(0, comp); lead.connect(lf); lf.connect(leadG); lf.connect(gain(.6, rev)); lead.start();
      var vib = ctx.createOscillator(); vib.frequency.value = 5.6; var vg = gain(14, lead.detune); vib.connect(vg); vib.start();
      G = { out: out, comp: comp, rev: rev, sc: sc, pad: pad, oscs: oscs, sub: sub, lfo: lfo, lead: lead, leadG: leadG, vib: vib, drums: gain(1, comp), pluck: gain(1, sc), pluckSend: gain(.35, rev), log: gain(1, sc), skank: gain(1, sc) };
      G.pluck.connect(G.pluckSend);
    }
    function teardown() {
      if (!G) return; var g = G, t = ctx.currentTime; G = null;
      g.out.gain.setTargetAtTime(0, t, .12);
      setTimeout(function () { try { g.oscs.concat([g.sub, g.lfo, g.lead, g.vib]).forEach(function (o) { o.stop(); }); g.out.disconnect(); } catch (e) { } }, 600);
    }

    /* ---- one-shot voices ---- */
    function burst(t, dur, vel, type, f, q, to, atk) {
      var s = ctx.createBufferSource(); s.buffer = noise; var fl = ctx.createBiquadFilter(); fl.type = type; fl.frequency.value = f; fl.Q.value = q || 1;
      var g = gain(0, to || G.drums); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vel, t + (atk || .003)); g.gain.exponentialRampToValueAtTime(.001, t + dur);
      s.connect(fl); fl.connect(g); s.start(t); s.stop(t + dur + .02); return fl;
    }
    function tone(t, dur, vel, type, f0, f1, fT, to) {
      var o = ctx.createOscillator(); o.type = type; o.frequency.setValueAtTime(f0, t); if (f1) o.frequency.exponentialRampToValueAtTime(f1, t + fT);
      var g = gain(0, to || G.drums); g.gain.setValueAtTime(vel, t); g.gain.exponentialRampToValueAtTime(.001, t + dur); o.connect(g); o.start(t); o.stop(t + dur + .02); return o;
    }
    function kick(t, v) { tone(t, .38, .9 * v, 'sine', 165, 46, .09); burst(t, .02, .25 * v, 'lowpass', 2500, .7);
      var s = G.sc.gain; s.setValueAtTime(1, t); s.linearRampToValueAtTime(.32, t + .012); s.linearRampToValueAtTime(1, t + .3); }
    function logDrum(t, f, v) {                                            // the amapiano bass: sine with a fast pitch drop + a little grit
      var o = ctx.createOscillator(); o.type = 'sine'; o.frequency.setValueAtTime(f * 2.6, t); o.frequency.exponentialRampToValueAtTime(f, t + .045);
      var o2 = ctx.createOscillator(); o2.type = 'triangle'; o2.frequency.setValueAtTime(f * 2, t + .001); o2.frequency.exponentialRampToValueAtTime(f, t + .04);
      var g = gain(0, G.log); g.gain.setValueAtTime(.75 * v, t); g.gain.setTargetAtTime(0, t + .06, .11);
      var g2 = gain(.18 * v, g); o.connect(g); o2.connect(g2); o.start(t); o2.start(t); o.stop(t + .6); o2.stop(t + .6);
    }
    function clap(t, v) { for (var i = 0; i < 3; i++) burst(t + i * .009, .03, .5 * v, 'bandpass', 1600, 1.2); burst(t + .026, .19, .55 * v, 'bandpass', 1900, .9, G.drums).connect(gain(.4, G.rev)); }
    function hat(t, v, open) { burst(t, open ? .28 : .045, (open ? .28 : .3) * v, 'highpass', 8200, .8); }
    function shaker(t, v) { burst(t, .04 + .04 * v, .32 * v, 'bandpass', 6600, .9, G.drums, .006); }
    function shekere(t, v) { burst(t, .11, .28 * v, 'bandpass', 3300, .55, G.drums, .004); burst(t + .017, .07, .14 * v, 'bandpass', 4200, .7); }
    function clave(t, v) { tone(t, .07, .35 * v, 'sine', 1880, 0, 0); tone(t, .04, .12 * v, 'sine', 2510, 0, 0); }
    function conga(t, kind, v) {
      if (kind === 'l') tone(t, .08, .22 * v, 'sine', 150, 120, .05);
      else if (kind === 's') { tone(t, .07, .4 * v, 'sine', 262, 230, .03); burst(t, .035, .18 * v, 'bandpass', 2800, 1.5); }
      else tone(t, .24, .5 * v, 'sine', 196, 178, .06);
    }
    function pluck(t, f, v) {                                              // adungu-ish: triangle + octave sine, lowpass that closes fast
      var fl = ctx.createBiquadFilter(); fl.type = 'lowpass'; fl.Q.value = 1.2; fl.frequency.setValueAtTime(5200, t); fl.frequency.exponentialRampToValueAtTime(900, t + .18);
      var g = gain(0, G.pluck); g.gain.setValueAtTime(.42 * v, t); g.gain.exponentialRampToValueAtTime(.001, t + .7); fl.connect(g);
      tone(t, .7, 1, 'triangle', f, 0, 0, fl); tone(t, .35, .35, 'sine', f * 2, 0, 0, fl); tone(t, .5, .6, 'triangle', f * 1.004, 0, 0, fl); burst(t, .012, .12, 'highpass', 3000, .7, fl);
    }
    function skank(t, semis, v) {                                          // kidandali / dancehall offbeat chop: three saws through a tight bandpass
      var fl = ctx.createBiquadFilter(); fl.type = 'bandpass'; fl.frequency.value = 2100; fl.Q.value = .8; var g = gain(0, G.skank);
      g.gain.setValueAtTime(.16 * v, t); g.gain.exponentialRampToValueAtTime(.001, t + .13); fl.connect(g);
      for (var i = 0; i < 3; i++) tone(t + i * .004, .13, .5, 'sawtooth', hz(220, semis[i] + 12), 0, 0, fl);
    }
    function riser(t, len) {
      var f = burst(t, len + .3, .5, 'bandpass', 400, 1.4, G.drums, len); f.frequency.exponentialRampToValueAtTime(5200, t + len);
      var o = tone(t, len + .1, .12, 'sawtooth', 110, 440, len, G.comp); o.detune.value = 5;
      for (var i = 0; i < 18; i++) { var u = i / 18, tt = t + len * (1 - Math.pow(1 - u, 1.8)); clap(tt, .35 + .5 * u); }
    }
    function impact(t) { tone(t, 1.3, 1, 'sine', 62, 34, .5); burst(t, .5, .8, 'lowpass', 700, .5); burst(t, 1.4, .35, 'highpass', 2500, .5, G.drums).connect(gain(.8, G.rev)); }
    function finale(t, key) { logDrum(t, hz(55, key), 1.1); shekere(t, 1); impact(t + .01); [0, 3, 7, 12, 15].forEach(function (s, i) { pluck(t + i * .045, hz(220, key + s), .9 - i * .1); }); }

    /* ---- program lookup ---- */
    function levelAt(time) {
      var e, best = null; for (var i = 0; i < prog.length; i++) { e = prog[i]; if (cueT + e.at <= time) best = e; }
      if (!best) return { L: LEVELS.off, key: curKey };
      var L = {}, base = LEVELS[best.lvl] || LEVELS.off, k; for (k in base) L[k] = base[k];
      for (k in best) if (k !== 'at' && k !== 'lvl' && k !== 'riser' && k !== 'impact' && k !== 'fin' && k !== 'key') L[k] = best[k];
      if (best.key !== undefined) curKey = best.key;
      return { L: L, key: curKey };
    }
    function fireOnce(now) {
      for (var i = 0; i < prog.length; i++) { var e = prog[i], t = cueT + e.at; if (fired[i] || t >= now + LOOK) continue; if (t < now - .05) { fired[i] = 1; continue; }
        if (e.riser) riser(t, e.riser); if (e.impact) impact(t); if (e.fin) finale(t, curKey); fired[i] = 1; }
    }

    /* ---- the step scheduler ---- */
    function step(n, t0) {
      var s = n % 16, bar = Math.floor(n / 16), lv = levelAt(t0), L = lv.L, key = lv.key, t = t0 + (s % 2 ? SWING * S16 : 0);
      var ci = (L.solo ? Math.floor(bar / 2) : bar) % 4, root = CHORD_ROOT[ci], chord = CHORDS[ci];
      if (s === 0) {                                                       // chord change on the bar
        var pf = hz(110, key + root), pg = L.pad ? .95 * L.pad : 0;
        G.oscs.forEach(function (o, i) { o.frequency.setTargetAtTime(hz(110, key + chord[i]) * (i < 2 ? 1 : 2), t0, .08); });
        G.sub.frequency.setTargetAtTime(pf / 2, t0, .08); G.pad.gain.setTargetAtTime(pg, t0, L.pad ? 1.2 : .5);
      }
      if (L.kick && (s === 0 || s === 8 || (L.kick > 1 && (s === 4 || s === 12)))) kick(t, 1); else if (L.kick && s === 11) kick(t, .45);
      if (L.log) LOG[bar % 2].forEach(function (h) { if (h[0] === s) logDrum(t, hz(55, key + root + h[1]), h[2] * L.log); });
      if (L.clap && (s === 4 || s === 12)) clap(t, L.clap);
      if (L.hat) { if (s % 4 === 2) hat(t, .8 * L.hat, L.ohat && s === 14); else if (L.hat >= 1 && s % 4 === 3) hat(t, .3, false); }
      if (L.shaker) shaker(t0 + (s % 2 ? .21 * S16 : 0), SHK[s % 4] * L.shaker);
      if (L.shek && (s % 4 === 0 || s === 14 || s === 7)) shekere(t, (s % 4 ? .45 : 1) * L.shek);
      if (L.clave && CLAVE.indexOf(s) >= 0) clave(t, L.clave);
      if (L.conga) CONGA.forEach(function (c) { if (c[0] === s) conga(t, c[1], c[2] * L.conga); });
      if (L.skank && s % 4 === 2) skank(t, [chord[0] + key, chord[1] + key, chord[2] + key], L.skank);
      if (L.pluck) {                                                       // the UG theme: 2-bar motif, answered an octave up in bars 3-4; halved in solo mode
        var pos = (bar % 4) * 16 + s, m = L.solo ? 2 : 1, up = (!L.solo && bar % 4 >= 2) ? 12 : 0;
        MOTIF.forEach(function (q) { if (q[0] * m === (L.solo ? pos : pos % 32)) pluck(t, hz(220, key + q[1] + (L.solo ? 12 : up)), (up ? .6 : .85) * L.pluck); });
      }
      var lg = G.leadG.gain;                                               // endingidi lead: the motif at half speed, legato
      if (L.lead) { var lp = (bar % 4) * 16 + s; MOTIF.forEach(function (q) { if (q[0] * 2 === lp) { G.lead.frequency.setTargetAtTime(hz(440, key + q[1]), t, .04); if (q[0] === 0) { lg.setTargetAtTime(0, t - .05, .05); } lg.setTargetAtTime(.2 * L.lead, t, .09); } }); }
      else if (s === 0) lg.setTargetAtTime(0, t0, .25);
    }
    function tick() {
      if (!G || !prog) return; var now = ctx.currentTime;
      fireOnce(now);
      while (nextStep < now + LOOK) { step(stepN, nextStep); stepN++; nextStep += S16; }
    }

    /* ---- public ---- */
    function play(cut) {
      stop(); mode = cut === 'short' ? 'short' : 'long'; build(); curKey = 0;
      var t = ctx.currentTime + .08; cueT = t; nextStep = t; stepN = 0; prog = mode === 'short' ? SHORT[0] : LONG[0]; fired = [];
      if (ctx.state === "suspended" && ctx.resume && !ctx.startRendering) { var pr = ctx.resume(); if (pr && pr.catch) pr.catch(function () { }); }
      timer = setInterval(tick, TICK); tick();
    }
    function cue(i) {
      if (!G || mode !== 'long') return; var p = LONG[Math.max(0, Math.min(LONG.length - 1, i | 0))];
      prog = p; fired = []; cueT = ctx.currentTime;
    }
    function stop() { if (timer) clearInterval(timer); timer = null; prog = null; teardown(); }
    function duck(on) { ducked = !!on; if (G) G.out.gain.setTargetAtTime(ducked ? .4 : 1, ctx.currentTime, .06); }   // ~ -8 dB under narration
    return { play: play, cue: cue, stop: stop, duck: duck, tick: tick, bpm: BPM, levels: LEVELS, programs: { long: LONG, short: SHORT } };
  }

  window.UGScore = { create: create };
})();
