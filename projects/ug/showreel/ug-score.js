/* UG showreel score v2 — generative WebAudio, no samples.
   window.UGScore.create(ctx, destGain) -> { play(cut), cue(i), stop(), duck(on), tick() }
   Kampala amapiano / Afro-house / kidandali: humanised timing and velocity, round-robin timbres,
   layered kit, saturated log drum with sidechain, FM Rhodes comping over moving voicings, supersaw
   only on drops, pluck <-> "hey" call-and-response, plate reverb, dotted-8th delay, bus comp + soft clip. */
(function () {
  'use strict';
  var BPM = 114, LOOK = 0.1, TICK = 25;
  var S16 = 60 / BPM / 4, BAR = S16 * 16, DOT8 = S16 * 3;
  var SWING = [0, .17, .02, .14], SHKSW = [0, .23, .05, .19];         // shuffle curve per 16th of a beat: 'e' late, 'and' near straight, 'a' a bit less
  var seed = 7; function R() { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }   // seeded so offline renders repeat
  function H(t, ms) { return t + (R() * 2 - 1) * ms * .001; }          // humanise: +/- ms
  function V(v, a) { return v * (1 - (a || .08) + 2 * (a || .08) * R()); }   // velocity jitter
  var RR = {}; function rr(k, n) { RR[k] = (RR[k] || 0) + 1; return RR[k] % n; }   // round robin
  function hz(base, semi) { return base * Math.pow(2, semi / 12); }

  /* ---- levels: which layers are alive and how loud ---- */
  var LEVELS = {
    off:    {},
    pad:    { pad: 1, ep: 1, pluck: 1, solo: 1 },
    break:  { pad: .6, ep: 1, pluck: .8, shaker: .85, solo: 1 },                                   // breakdown: Rhodes and shaker only
    sparse: { pad: .8, ep: 1, pluck: 1, shaker: .6, clave: .8, log: .6, shek: .7, rim: .6 },
    groove: { pad: .8, ep: 1, pluck: 1, shaker: 1, clave: 1, log: 1, shek: 1, kick: 1, hat: .6, conga: 1, rim: .8 },
    full:   { pad: .7, ep: 1, pluck: 1, shaker: 1, clave: 1, log: 1, shek: 1, kick: 1, hat: 1, conga: 1, clap: 1, skank: 1, rim: 1 },
    drop:   { pad: .5, ep: .85, saw: 1, pluck: 1, adlib: 1, shaker: 1, clave: 1, log: 1.15, shek: 1, kick: 2, hat: 1, ohat: 1, conga: 1, clap: 1, skank: 1, lead: 1, rim: 1 },
    outro:  { pad: 1, ep: 1, pluck: 1, solo: 1, shek: .5, shaker: .5, lead: 1 }
  };

  /* ---- programs: per scene (long cut) or whole piece (short cut). at = seconds since cue. Hit times unchanged from v1 ---- */
  var LONG = [
    [{ at: 0, lvl: 'pad' }, { at: 8, riser: 2.6 }, { at: 10.6, impact: 1, lvl: 'groove' }, { at: 15.5, lvl: 'full' }],   // 0 opening: map assembles, U+G lock at 10.55
    [{ at: 0, lvl: 'sparse', key: -2 }, { at: 11.4, lvl: 'groove', key: 0 }],                                          // 1 problem: three apps -> one crest
    [{ at: 0, lvl: 'groove', skank: 1 }, { at: 12, lvl: 'full' }],                                                      // 2 ride: compare desk, Book on UG
    [{ at: 0, lvl: 'break' }, { at: 8.4, lvl: 'groove' }, { at: 19, lvl: 'full' }, { at: 27.8, riser: 2.2 }, { at: 30, impact: 1, lvl: 'drop' }],  // 3 pool: breakdown, seats fill -> drop at 30
    [{ at: 0, lvl: 'full' }],                                                                                           // 4 drive / offers
    [{ at: 0, lvl: 'groove', lead: 1, skank: 0 }],                                                                      // 5 rent / signature: fiddle over the fleet
    [{ at: 0, lvl: 'full', conga: 1.3 }],                                                                               // 6 deliver: heavier hand percussion
    [{ at: 0, lvl: 'groove', key: 2, lead: 1 }, { at: 6, lvl: 'full', key: 2, lead: 1 }, { at: 14, riser: 2.2 }, { at: 16.3, impact: 1, lvl: 'drop', key: 2, lead: 1 }], // 7 atlas: up to B
    [{ at: 0, lvl: 'sparse', key: 2, lead: 1 }, { at: 10, lvl: 'groove', key: 2, lead: 1 }],                            // 8 explore / foresight
    [{ at: 0, lvl: 'groove', key: 0 }],                                                                                 // 9 plug-ins / languages: back home to A
    [{ at: 0, lvl: 'full' }],                                                                                           // 10 stay on UG / teleport
    [{ at: 0, lvl: 'groove' }, { at: 8, lvl: 'outro', lead: 1 }, { at: 12.4, fin: 1 }]                                  // 11 one link / close
  ];
  var SHORT = [[{ at: 0, lvl: 'pad' }, { at: 5.8, riser: 2.6 }, { at: 8.4, impact: 1, lvl: 'groove' }, { at: 16, lvl: 'full', skank: 1 },
    { at: 34.75, lvl: 'break' }, { at: 41.05, lvl: 'groove' }, { at: 47.5, riser: 2.2 }, { at: 49.75, impact: 1, lvl: 'drop' },
    { at: 54.75, lvl: 'full', key: 2, lead: 1 }, { at: 62.7, riser: 2.2 }, { at: 64.9, impact: 1, lvl: 'drop', key: 2, lead: 1 },
    { at: 73.5, lvl: 'groove', key: 0 }, { at: 78, lvl: 'outro', lead: 1 }, { at: 83.8, fin: 1 }, { at: 86.5, lvl: 'off' }]];  // 86 s: lock 8.4, breakdown 34.75, Stage drop 49.75, Atlas lift 64.9

  /* ---- harmony: Am7 · Fmaj7 · Cmaj7 · G(add9); two voicings each so the top line moves by step across 8 bars ---- */
  var CHORD_ROOT = [0, 8, 3, -2];                                        // log-drum roots (semitones from A1)
  var VOIC = [[[0, 7, 10, 15, 19], [7, 12, 15, 19, 22]],                 // A E G C E  |  E A C E G     (semitones from A2)
              [[-4, 3, 8, 12, 19], [8, 12, 15, 19, 24]],                 // F C F A E  |  F A C E A
              [[3, 10, 14, 19, 22], [7, 10, 14, 17, 19]],                // C G B E G  |  E G B D E
              [[-2, 5, 12, 14, 17], [2, 5, 10, 14, 17]]];                // G D A B D  |  B D G B D
  var LOG = [[[3, 0, .9], [6, 0, 1], [10, 7, .8], [12, 0, .9], [14, 5, .7]],
             [[3, 0, .9], [6, 0, 1], [8, 7, .7], [10, 5, .8], [13, 0, .8], [15, 3, .6]]];
  var CLAVE = [0, 3, 6, 10, 12];                                          // 3-2 son clave
  var SHK = [[1, .4, .65, .5], [1, .45, .7, .38]];                        // shaker accent cycles, alternate bars
  var CONGA = [[0, 'l', .5], [2, 'l', .4], [4, 's', .9], [8, 'l', .5], [10, 'l', .4], [12, 's', .8], [14, 'o', 1], [15, 'o', .9]];
  var EPR = [[0, .95, .9], [6, .3, .65], [11, .22, .55], [14, .18, .45]];  // Rhodes comping: step, length in bars, velocity
  var MOTIF = [[0, 0], [3, 3], [6, 5], [10, 7], [12, 10], [16, 7], [19, 5], [22, 3], [26, 0], [28, -2]]; // A minor pentatonic, clave-shaped
  var ADL = [0, 6, 16, 22, 26];                                           // "hey" answers in bars 3-4 of a drop phrase

  LONG.concat(SHORT).forEach(function (p) { for (var i = 1; i < p.length; i++) if (!p[i].lvl) for (var k in p[i - 1]) if (!(k in p[i]) && k !== 'at' && k !== 'riser' && k !== 'impact' && k !== 'fin') p[i][k] = p[i - 1][k]; });

  function create(ctx, dest) {
    var noise = mkNoise(ctx, 2), plateIR = mkPlate(ctx, 2.1);
    var G = null, timer = null, mode = null, prog = null, cueT = 0, nextStep = 0, stepN = 0, fired = null, pre = null, ducked = false, curKey = 0;

    function gain(v, to) { var g = ctx.createGain(); g.gain.value = v; if (to) g.connect(to); return g; }
    function pan(v, to) { var p = ctx.createStereoPanner ? ctx.createStereoPanner() : ctx.createGain(); if (p.pan) p.pan.value = v; p.connect(to); return p; }
    function filt(type, f, q, to) { var b = ctx.createBiquadFilter(); b.type = type; b.frequency.value = f; b.Q.value = q || 1; if (to) b.connect(to); return b; }
    function shaper(k, to) { var n = 1024, c = new Float32Array(n), d = Math.tanh(k); for (var i = 0; i < n; i++) c[i] = Math.tanh(k * (i * 2 / (n - 1) - 1)) / d; var w = ctx.createWaveShaper(); w.curve = c; w.oversample = '2x'; if (to) w.connect(to); return w; }
    function mkNoise(c, s) { var b = c.createBuffer(1, c.sampleRate * s, c.sampleRate), d = b.getChannelData(0); for (var i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1; return b; }
    function mkPlate(c, s) {                                             // plate-ish: 18 ms pre-delay, dense bright early, tail darkens (one-pole opening -> closing)
      var n = c.sampleRate * s, p0 = Math.floor(c.sampleRate * .018), b = c.createBuffer(2, n, c.sampleRate);
      for (var ch = 0; ch < 2; ch++) { var d = b.getChannelData(ch), y = 0; for (var i = p0; i < n; i++) { var u = (i - p0) / (n - p0), a = .62 - .54 * u; y += a * ((Math.random() * 2 - 1) - y); d[i] = y * Math.pow(1 - u, 2.4) * (1 + .7 * Math.exp(-u * 30)); } }
      return b;
    }
    function dip(p, t, to, att, rel) { p.setValueAtTime(1, t); p.linearRampToValueAtTime(to, t + att); p.linearRampToValueAtTime(1, t + rel); }

    /* ---- graph: buses, sends, sustained voices ---- */
    function build() {
      var out = gain(ducked ? .4 : 1, dest), trim = gain(.8, out);
      var clip = shaper(1.4, trim);                                      // soft-clip limiter: tanh, keeps peaks under the trim
      var lim = ctx.createDynamicsCompressor(); lim.threshold.value = -3; lim.knee.value = 1; lim.ratio.value = 12; lim.attack.value = .002; lim.release.value = .08; lim.connect(clip);
      var mk = gain(1.25, lim);                                          // makeup
      var comp = ctx.createDynamicsCompressor(); comp.threshold.value = -16; comp.knee.value = 10; comp.ratio.value = 2.5; comp.attack.value = .015; comp.release.value = .25; comp.connect(mk);   // bus glue: a few dB on the drops, nothing on the intro
      var mix = gain(.45, comp);                                          // the sum, before dynamics (peaks ~ -2 dBFS on the drops)
      var rev = ctx.createConvolver(); rev.buffer = plateIR; var revOut = gain(.35, mix), revHP = filt('highpass', 260, .7, revOut); rev.connect(revHP);
      var dly = ctx.createDelay(1); dly.delayTime.value = DOT8; var dLP = filt('lowpass', 2600, .7), dlyOut = gain(.7, mix); dly.connect(dLP); dLP.connect(gain(.36, dly)); dLP.connect(pan(.35, dlyOut)); dLP.connect(gain(.3, rev));   // dotted-8th delay
      var sc = gain(1, mix), pump = gain(1, sc);                          // sc: kick sidechain (everything harmonic); pump: log-drum sidechain (pad + Rhodes)
      var drums = shaper(1.25, mix), drG = gain(1, drums);                // drum bus with light saturation
      /* pad: dark triangles + sub, breathing lowpass */
      var padG = gain(0, pump), padF = filt('lowpass', 420, .8, padG); padF.connect(gain(.35, rev));
      var pads = [], i;
      for (i = 0; i < 2; i++) { var o = ctx.createOscillator(); o.type = 'triangle'; o.detune.value = i ? 6 : -6; o.connect(gain(.14, padF)); o.start(); pads.push(o); }
      var sub = ctx.createOscillator(); sub.type = 'sine'; sub.connect(gain(.16, padF)); sub.start();
      var lfo = ctx.createOscillator(); lfo.frequency.value = .08; lfo.connect(gain(140, padF.frequency)); lfo.start();
      /* supersaw: six detuned saws, filtered; only opened on the drops */
      var sawG = gain(0, sc), sawF = filt('lowpass', 500, 1.1, sawG), saws = []; sawF.connect(gain(.3, rev));
      [-19, -11, -4, 5, 12, 20].forEach(function (c, j) { var o = ctx.createOscillator(); o.type = 'sawtooth'; o.detune.value = c; o.connect(pan((j % 2 ? .5 : -.5) * (1 - j / 8), gain(.05, sawF))); o.start(); saws.push(o); });
      /* endingidi-style lead: saw -> nasal bandpass, vibrato, slow attack, delay + plate */
      var lead = ctx.createOscillator(); lead.type = 'sawtooth'; var lf = filt('bandpass', 1100, 3.2); var leadOut = gain(1, mix), leadG = gain(0, pan(.15, leadOut)); lead.connect(lf); lf.connect(leadG); leadG.connect(gain(.5, rev)); leadG.connect(gain(.35, dly)); lead.start();
      var vib = ctx.createOscillator(); vib.frequency.value = 5.4; vib.connect(gain(14, lead.detune)); vib.start();
      /* Rhodes bus with a slow tremolo */
      var ep = gain(.8, pump), epT = ctx.createOscillator(); epT.frequency.value = 4.3; epT.connect(gain(.1, ep.gain)); epT.start(); ep.connect(gain(.28, rev)); ep.connect(gain(.08, dly));
      var logOut = gain(.36, mix), logIn = shaper(2.4, filt('lowpass', 400, .9, logOut));  // log drum: saturate, then keep it round; ~2 dB over the kit
      G = { out: out, comp: comp, mix: mix, rev: rev, dly: dly, sc: sc, pump: pump, drums: drG, pad: padG, pads: pads, sub: sub, lfo: lfo, sawG: sawG, sawF: sawF, saws: saws, lead: lead, leadG: leadG, vib: vib, ep: ep, epT: epT, logIn: logIn,
        bus: { drums: drG, log: logOut, harm: sc, lead: leadOut, rev: revOut, dly: dlyOut },
        pluck: gain(1, pan(.1, sc)), skank: gain(1, pan(-.2, sc)), vox: gain(2.4, pan(-.15, mix)),
        pShk: pan(.35, drG), pHat: pan(-.28, drG), pRim: pan(.22, drG), pClv: pan(.15, drG), pCgL: pan(-.3, drG), pCgR: pan(.3, drG) };
      G.pluck.connect(gain(.3, rev)); G.pluck.connect(gain(.22, dly)); G.skank.connect(gain(.15, dly)); G.vox.connect(gain(.45, rev)); G.vox.connect(gain(.3, dly));
    }
    function teardown() {
      if (!G) return; var g = G, t = ctx.currentTime; G = null;
      g.out.gain.setTargetAtTime(0, t, .12);
      setTimeout(function () { try { g.pads.concat(g.saws, [g.sub, g.lfo, g.lead, g.vib, g.epT]).forEach(function (o) { o.stop(); }); g.out.disconnect(); } catch (e) { } }, 600);
    }

    /* ---- one-shot primitives ---- */
    function burst(t, dur, vel, type, f, q, to, atk) {
      var s = ctx.createBufferSource(); s.buffer = noise; s.playbackRate.value = .9 + R() * .2; var fl = filt(type, f, q);
      var g = gain(0, to || G.drums); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vel, t + (atk || .003)); g.gain.exponentialRampToValueAtTime(.001, t + dur);
      s.connect(fl); fl.connect(g); s.start(t); s.stop(t + dur + .02); return fl;
    }
    function tone(t, dur, vel, type, f0, f1, fT, to) {
      var o = ctx.createOscillator(); o.type = type; o.frequency.setValueAtTime(f0, t); if (f1) o.frequency.exponentialRampToValueAtTime(f1, t + fT);
      var g = gain(0, to || G.drums); g.gain.setValueAtTime(vel, t); g.gain.exponentialRampToValueAtTime(.001, t + dur); o.connect(g); o.start(t); o.stop(t + dur + .02); return o;
    }

    /* ---- the kit ---- */
    function kick(t, v, four) {
      t = H(t, 2.5); var f0 = [168, 158, 178][rr('k', 3)];
      tone(t, .4, .95 * v, 'sine', f0, 44, .085);                        // body
      tone(t, .05, .32 * v, 'triangle', 1500, 220, .018);                 // beater click
      burst(t, .016, .28 * v, 'highpass', 3200, .6);                      // air
      dip(G.sc.gain, t, four ? .26 : .34, .012, .28);                     // the amapiano pump on everything harmonic
    }
    function logDrum(t, f, v) {                                            // the bass: sine with a fast pitch drop + 2nd harmonic, hot into the saturator; pushed ~5 ms late like a producer would
      t = H(t + .005, 3); var o = ctx.createOscillator(); o.type = 'sine'; o.frequency.setValueAtTime(f * 2.4, t); o.frequency.exponentialRampToValueAtTime(f, t + .05);
      var o2 = ctx.createOscillator(); o2.type = 'triangle'; o2.frequency.setValueAtTime(f * 2, t); o2.frequency.exponentialRampToValueAtTime(f, t + .04);
      var g = gain(0, G.logIn); g.gain.setValueAtTime(1.2 * v, t); g.gain.setTargetAtTime(0, t + .07, .12);
      o.connect(g); o2.connect(gain(.25, g)); o.start(t); o2.start(t); o.stop(t + .7); o2.stop(t + .7);
      dip(G.pump.gain, t, 1 - .28 * Math.min(1, v), .02, .17);            // the chords duck under each bass note
    }
    function clap(t, v) {                                                  // several hands, never the same spacing, plus the room
      t = H(t, 4); var n = 4 + rr('cn', 2), f = [1500, 1750, 1350][rr('cf', 3)];
      for (var i = 0; i < n; i++) burst(t + i * (.007 + R() * .006), .028, (.3 + .12 * R()) * v, 'bandpass', f + R() * 300, 1.4);
      burst(t + .03, .22, .5 * v, 'bandpass', f + 400, .8).connect(gain(.55, G.rev));
    }
    function hat(t, v, open) {                                             // decay follows velocity; three sizzles round-robin
      t = H(t, 4); var f = [8000, 8700, 7400][rr('h', 3)], dur = open ? .2 + .12 * v : .012 + .06 * v;
      burst(t, dur, (open ? .26 : .3) * v, 'highpass', f, .7, G.pHat); if (v > .5) burst(t, dur * .6, .09 * v, 'bandpass', 11000, 2, G.pHat);
    }
    function rim(t, v) { t = H(t, 3); tone(t, .05, .4 * v, 'sine', [820, 860, 790][rr('r', 3)], 600, .03, G.pRim); burst(t, .025, .25 * v, 'bandpass', 3600, 1.8, G.pRim); burst(t, .004, .2 * v, 'highpass', 5000, .5, G.pRim); }
    function shaker(t0, s, v) {                                            // 16ths on their own swing curve; accented hits get the second "shh"
      var t = H(t0 + SHKSW[s % 4] * S16, 3), f = [6200, 6800, 5800, 7200][rr('s', 4)];
      burst(t, .03 + .06 * v, .3 * v, 'bandpass', f, 1.1, G.pShk, .008); if (s % 4 === 0) burst(t + .02, .07, .12 * v, 'bandpass', f * 1.3, 1.5, G.pShk, .01);
    }
    function shekere(t, v) { t = H(t, 4); burst(t, .11, .28 * v, 'bandpass', 3300 + rr('sk', 3) * 250, .55, G.pShk, .004); burst(t + .017, .07, .14 * v, 'bandpass', 4200, .7, G.pShk); }
    function clave(t, v) { t = H(t, 2); var f = 1880 * (1 + (rr('cl', 3) - 1) * .012); tone(t, .07, .35 * v, 'sine', f, 0, 0, G.pClv); tone(t, .04, .12 * v, 'sine', f * 1.335, 0, 0, G.pClv); }
    function conga(t, kind, v) {
      t = H(t, 4); var d = 1 + (rr('cg', 3) - 1) * .03;
      if (kind === 'l') tone(t, .08, .22 * v, 'sine', 150 * d, 120, .05, G.pCgL);
      else if (kind === 's') { tone(t, .07, .4 * v, 'sine', 262 * d, 230, .03, G.pCgR); burst(t, .035, .18 * v, 'bandpass', 2800, 1.5, G.pCgR); }
      else tone(t, .24, .5 * v, 'sine', 196 * d, 178, .06, G.pCgR);
    }
    function tom(t, v, f) { tone(t, .28, .6 * v, 'sine', f * 1.5, f, .06); burst(t, .03, .2 * v, 'lowpass', 1800, .7); }
    function swell(t, len, v) {                                            // reverse-noise riser: highpass noise swelling to the hit, cut dead on it
      var s = ctx.createBufferSource(); s.buffer = noise; s.loop = true; var fl = filt('highpass', 1200, .6), g = gain(0, G.drums);
      g.gain.setValueAtTime(.001, t); g.gain.exponentialRampToValueAtTime(v, t + len); g.gain.setValueAtTime(0, t + len); fl.frequency.exponentialRampToValueAtTime(4000, t + len);
      s.connect(fl); fl.connect(g); fl.connect(gain(.5, G.rev)); s.start(t); s.stop(t + len + .01);
    }

    /* ---- melodic voices ---- */
    function pluck(t, f, v) {                                              // adungu-ish: triangle + octave sine + click; lowpass closing fast; delay + plate on the bus
      t = H(t, 5); f *= 1 + (R() - .5) * .004; var fl = filt('lowpass', 5200 * (1 + (rr('p', 3) - 1) * .12), 1.2, null); fl.frequency.setValueAtTime(fl.frequency.value, t); fl.frequency.exponentialRampToValueAtTime(900, t + .18);
      var g = gain(0, G.pluck); g.gain.setValueAtTime(.42 * v, t); g.gain.exponentialRampToValueAtTime(.001, t + .7); fl.connect(g);
      tone(t, .7, 1, 'triangle', f, 0, 0, fl); tone(t, .35, .35, 'sine', f * 2, 0, 0, fl); tone(t, .5, .6, 'triangle', f * 1.004, 0, 0, fl); burst(t, .012, .12, 'highpass', 3000, .7, fl);
    }
    function epNote(t, f, v, dur, pn) {                                    // FM electric piano: sine carrier, 1:1 modulator with a velocity-shaped index that decays, 7:1 tine
      var c = ctx.createOscillator(), m = ctx.createOscillator(), tn = ctx.createOscillator(); c.type = m.type = tn.type = 'sine';
      f *= 1 + (R() - .5) * .003; c.frequency.value = f; m.frequency.value = f; tn.frequency.value = f * 7;
      var mi = gain(0, c.frequency); m.connect(mi); mi.gain.setValueAtTime(f * (1 + .9 * v), t); mi.gain.setTargetAtTime(f * .2, t + .01, .14);
      var ti = gain(0, c.frequency); tn.connect(ti); ti.gain.setValueAtTime(f * .3 * v, t); ti.gain.setTargetAtTime(0, t, .03);
      var g = gain(0, pan(pn, G.ep)); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(.3 * v, t + .004); g.gain.setTargetAtTime(.3 * v * .4, t + .04, .32); g.gain.setTargetAtTime(0, t + dur, .09);
      c.connect(g); [c, m, tn].forEach(function (o) { o.start(t); o.stop(t + dur + .6); });
    }
    function epChord(t, chord, key, v, dur) { chord.forEach(function (n, i) { epNote(H(t + i * .007, 3), hz(110, key + n), V(v * (i === 0 ? .8 : 1), .1), dur, -.25 + i * .12); }); }
    function skank(t, semis, v) {                                          // kidandali / dancehall offbeat chop: three saws through a tight bandpass
      t = H(t, 4); var fl = filt('bandpass', 2100, .8); var g = gain(0, G.skank);
      g.gain.setValueAtTime(.16 * v, t); g.gain.exponentialRampToValueAtTime(.001, t + .13); fl.connect(g);
      for (var i = 0; i < 3; i++) tone(t + i * .004, .13, .5, 'sawtooth', hz(220, semis[i] + 12), 0, 0, fl);
    }
    function adlib(t, f, v) {                                              // "hey": breath, then a saw through three formant bandpasses gliding e -> ey, pitch falling off
      t = H(t, 8); f *= 1 + (R() - .5) * .04; burst(t - .02, .035, .12 * v, 'bandpass', 1800, 1, G.vox, .01);
      var o = ctx.createOscillator(); o.type = 'sawtooth'; o.frequency.setValueAtTime(f * 1.03, t); o.frequency.exponentialRampToValueAtTime(f * .93, t + .2);
      var g = gain(0, G.vox); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(.55 * v, t + .015); g.gain.setTargetAtTime(0, t + .11, .05);
      [[560, 400, 5, 1], [1800, 2200, 8, .45], [2600, 2800, 10, .22]].forEach(function (F) { var b = filt('bandpass', F[0], F[2], gain(F[3], g)); b.frequency.exponentialRampToValueAtTime(F[1], t + .13); o.connect(b); });
      o.start(t); o.stop(t + .4);
    }

    /* ---- one-shots: risers with fills, impacts, the finale ---- */
    function riser(t, len) {
      var e = t + len, f = burst(t, len + .3, .4, 'bandpass', 400, 1.4, G.drums, len); f.frequency.exponentialRampToValueAtTime(5200, e);
      tone(t, len + .1, .1, 'sawtooth', 110, 440, len, G.mix).detune.value = 5;
      swell(t, len, .4);
      for (var i = 0; i < 16; i++) { var u = i / 16; clap(t + len * (1 - Math.pow(1 - u, 1.8)), .3 + .5 * u); }
      for (i = 8; i >= 1; i--) rim(e - i * S16, .35 + (8 - i) * .08);       // rim roll over the last two beats
      [[4, 200], [3, 160], [2, 125]].forEach(function (x, j) { tom(H(e - x[0] * S16, 3), .8 + j * .1, x[1]); });   // toms falling into the hit
    }
    function impact(t) {
      tone(t, 1.3, 1, 'sine', 62, 34, .5); burst(t, .5, .8, 'lowpass', 700, .5); burst(t, 1.4, .35, 'highpass', 2500, .5, G.drums).connect(gain(.8, G.rev));
      dip(G.sc.gain, t, .12, .01, .5);
      if (levelAt(t + .01).L.adlib) adlib(t + .06, hz(440, curKey), 1);
    }
    function finale(t, key) {
      logDrum(t, hz(55, key), 1.1); shekere(t, 1); impact(t + .01); adlib(t + .1, hz(440, key), 1);
      epChord(t, VOIC[0][0], key, 1, 2.5); [0, 3, 7, 12, 15].forEach(function (s, i) { pluck(t + i * .045, hz(220, key + s), .9 - i * .1); });
    }

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
      for (var i = 0; i < prog.length; i++) {
        var e = prog[i], t = cueT + e.at;
        if (e.fin && !pre[i] && t - 1.9 < now + LOOK) { pre[i] = 1; if (t - 1.9 > now - .05) swell(t - 1.9, 1.9, .55); }   // reverse riser into the final hit
        if (fired[i] || t >= now + LOOK) continue; if (t < now - .05) { fired[i] = 1; continue; }
        if (e.riser) riser(t, e.riser); if (e.impact) impact(t); if (e.fin) finale(t, curKey); fired[i] = 1;
      }
    }

    /* ---- the step scheduler ---- */
    function step(n, t0) {
      var s = n % 16, bar = Math.floor(n / 16), lv = levelAt(t0), L = lv.L, key = lv.key, t = t0 + SWING[s % 4] * S16;
      var ci = (L.solo ? Math.floor(bar / 2) : bar) % 4, root = CHORD_ROOT[ci], chord = VOIC[ci][Math.floor(bar / 4) % 2];
      if (s === 0) {                                                       // chord change on the bar: pad + supersaw retune, levels ease
        G.pads.forEach(function (o, i) { o.frequency.setTargetAtTime(hz(110, key + chord[i + 1]), t0, .08); });
        G.sub.frequency.setTargetAtTime(hz(55, key + root) / (root > 5 ? 2 : 1), t0, .08); G.pad.gain.setTargetAtTime(L.pad ? .9 * L.pad : 0, t0, L.pad ? 1.2 : .5);
        G.saws.forEach(function (o, i) { o.frequency.setTargetAtTime(hz(110, key + chord[1 + (i % 3)]) * (i < 3 ? 1 : 2), t0, .05); });
        G.sawG.gain.setTargetAtTime(L.saw ? .5 * L.saw : 0, t0, L.saw ? .25 : .6); G.sawF.frequency.setTargetAtTime(L.saw ? 2400 : 500, t0, .4);
      }
      if (L.kick && (s === 0 || s === 8 || (L.kick > 1 && (s === 4 || s === 12)))) kick(t, V(1, .04), L.kick > 1); else if (L.kick && s === 11) kick(t, .42, false);
      if (L.log) LOG[bar % 2].forEach(function (h) { if (h[0] === s) logDrum(t, hz(55, key + root + h[1]), V(h[2] * L.log, .06)); });
      if (L.clap && (s === 4 || s === 12)) clap(t, V(L.clap, .1));
      if (L.hat) { if (s % 4 === 2) hat(t, V(.8 * L.hat, .12), L.ohat && s === 14); else if (L.hat >= 1 && s % 4 === 3) hat(t, V(.3, .3), false); else if (L.hat >= 1 && bar % 4 === 3 && s === 15) hat(t, .5, false); }
      if (L.rim && (s === 7 || s === 15 || (bar % 2 && s === 13))) rim(t, V((s === 15 ? .8 : .6) * L.rim, .15));
      if (L.shaker) shaker(t0, s, V(SHK[bar % 2][s % 4] * L.shaker * (bar % 4 === 3 && s === 15 ? 1.3 : 1), .12));
      if (L.shek && (s % 4 === 0 || s === 14 || s === 7)) shekere(t, V((s % 4 ? .45 : 1) * L.shek, .1));
      if (L.clave && CLAVE.indexOf(s) >= 0) clave(t, V(L.clave, .08));
      if (L.conga) CONGA.forEach(function (c) { if (c[0] === s) conga(t, c[1], V(c[2] * L.conga, .12)); });
      if (L.skank && s % 4 === 2) skank(t, [chord[1] + key, chord[2] + key, chord[3] + key], V(L.skank, .1));
      if (L.ep) {                                                          // Rhodes comping: whole-bar chord in the quiet levels, syncopated stabs in the groove
        var ev = L.ep * (L.solo ? 1 : .85);
        if (L.solo) { if (s === 0) epChord(t, chord, key, .8 * ev, BAR * .95); if (s === 12 && bar % 2) epChord(t, chord, key, .35 * ev, DOT8); }
        else { EPR.forEach(function (h) { if (h[0] === s && !(bar % 2 && s === 11)) epChord(t, chord, key, h[2] * ev, h[1] * BAR); }); if (bar % 2 && s === 13) epChord(t, chord, key, .4 * ev, S16 * 2); }
      }
      if (L.pluck) {                                                       // the UG theme: 2-bar call; bars 3-4 answer an octave up, or with the "hey" on the drops
        var pos = (bar % 4) * 16 + s, m = L.solo ? 2 : 1, ans = !L.solo && bar % 4 >= 2;
        if (ans && L.adlib) { if (ADL.indexOf(pos - 32) >= 0) adlib(t, hz(220, key + 12 + [0, 3, 7][rr('a', 3)]), V(.9 * L.adlib, .15)); }
        else MOTIF.forEach(function (q) { if (q[0] * m === (L.solo ? pos : pos % 32)) pluck(t, hz(220, key + q[1] + (L.solo || ans ? 12 : 0)), V((ans ? .6 : .85) * L.pluck, .1)); });
      }
      var lg = G.leadG.gain;                                               // endingidi lead: the motif at half speed, legato
      if (L.lead) { var lp = (bar % 4) * 16 + s; MOTIF.forEach(function (q) { if (q[0] * 2 === lp) { G.lead.frequency.setTargetAtTime(hz(440, key + q[1]), H(t, 10), .04); if (q[0] === 0) lg.setTargetAtTime(0, t - .05, .05); lg.setTargetAtTime(.32 * L.lead, t, .09); G.vib.frequency.setTargetAtTime(5 + R(), t, .2); } }); }
      else if (s === 0) lg.setTargetAtTime(0, t0, .25);
    }
    function tick() {
      if (!G || !prog) return; var now = ctx.currentTime;
      fireOnce(now);
      while (nextStep < now + LOOK) { step(stepN, nextStep); stepN++; nextStep += S16; }
    }

    /* ---- public ---- */
    function play(cut) {
      stop(); mode = cut === 'short' ? 'short' : 'long'; seed = 7; RR = {}; build(); curKey = 0;
      var t = ctx.currentTime + .08; cueT = t; nextStep = t; stepN = 0; prog = mode === 'short' ? SHORT[0] : LONG[0]; fired = []; pre = [];
      if (ctx.state === "suspended" && ctx.resume && !ctx.startRendering) { var pr = ctx.resume(); if (pr && pr.catch) pr.catch(function () { }); }
      timer = setInterval(tick, TICK); tick();
    }
    function cue(i) {
      if (!G || mode !== 'long') return; var p = LONG[Math.max(0, Math.min(LONG.length - 1, i | 0))];
      prog = p; fired = []; pre = []; cueT = ctx.currentTime;
    }
    function stop() { if (timer) clearInterval(timer); timer = null; prog = null; teardown(); }
    function duck(on) { ducked = !!on; if (G) G.out.gain.setTargetAtTime(ducked ? .4 : 1, ctx.currentTime, .06); }   // ~ -8 dB under narration
    return { play: play, cue: cue, stop: stop, duck: duck, tick: tick, bpm: BPM, levels: LEVELS, programs: { long: LONG, short: SHORT }, _graph: function () { return G; } };
  }

  window.UGScore = { create: create };
})();
