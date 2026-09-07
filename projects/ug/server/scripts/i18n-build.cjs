#!/usr/bin/env node
/* Assemble data/i18n/*.json into the site: rewrites the LANGS and STR blocks in site/index.html between the
   i18n markers, and writes data/languages.json. Run after translators or reviewers change a dictionary.
   node server/scripts/i18n-build.cjs             (from projects/ug)
   node server/scripts/i18n-build.cjs --accept     (same, and accept the reported drift as reviewed)

   Three checks run before anything is written, because all three have already shipped bugs:

   ORPHANS   A key that lives in forty dictionaries but not in en.json is dropped silently — `keys` comes
             from en.json alone. That is how flipRide/flipPool/flipRent/flipDeliver were translated into
             every language and then rendered to the hero as the literal string "flipDeliver".
   DRIFT     English is the source. When an English string is edited, the forty translations of it do not
             change and nothing notices. The snapshot in data/i18n/.sources.json records the hash of each
             English string as of the last accepted build; any key whose hash has moved is named here.
   UNUSED    A key nothing in the site asks for is dead weight carried in forty languages. Dynamic lookups
             are listed in DYNAMIC below so they are not reported as dead. */
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const ROOT = path.resolve(__dirname, '..', '..');
const DIR = path.join(ROOT, 'data', 'i18n');
const SITE = path.join(ROOT, 'site', 'index.html');
const PACKS = path.join(ROOT, 'site', 'i18n');
/* The two strings the welcome gate says in every language at once, before any pack has loaded:
   turning the ring greets you in the language under your thumb. They stay inline for all 41. */
const INLINE_ALL = ['ui.welcome', 'ui.continue'];
const SNAP = path.join(DIR, '.sources.json');
const ACCEPT = process.argv.includes('--accept');
/* A published artifact is one file with nowhere to fetch a pack from. --inline-all writes
   site/i18n/all.json — every language in one object — so the artifact build can put the
   dictionaries back into the document it ships, and the demo speaks 41 languages again. */
const INLINE_ALL_FILE = process.argv.includes('--inline-all');
const ORDER = { // picker groups, in the order they appear
  'Uganda · Central': ['lg'], 'Uganda · East': ['xog', 'myx', 'gwr', 'lsm', 'teo', 'kpz'], 'Uganda · North': ['ach', 'laj', 'kdi', 'kdj'],
  'Uganda · West Nile': ['alz', 'lgg', 'mhi', 'keo'], 'Uganda · West': ['nyn', 'cgg', 'ttj', 'nyo', 'koo'],
  'East Africa · Africa': ['sw', 'rw', 'so', 'am', 'ar', 'ln', 'ha', 'zu'],
  'World': ['en', 'fr', 'de', 'it', 'es', 'es-MX', 'pt', 'pt-BR', 'ru', 'zh-Hans', 'ja', 'ko', 'hi'],
};
/* keys the JavaScript looks up through a variable, so the source scan cannot see them */
const DYNAMIC = ['ride', 'pool', 'rent', 'deliver', 'flipRide', 'flipPool', 'flipRent', 'flipDeliver',
  'ui.requested', 'ui.placed', 'ui.driverAssigned', 'ui.arriving', 'ui.onTrip', 'ui.done',   // the trip rail's steps
  'day.night', 'day.dawn', 'day.morning', 'day.midday', 'day.afternoon', 'day.dusk'];        // looked up through PHASE_KEY
const en = JSON.parse(fs.readFileSync(path.join(DIR, 'en.json'), 'utf8'));
const keys = Object.keys(en.strings);
const files = fs.readdirSync(DIR).filter(f => f.endsWith('.json') && !f.startsWith('.')).map(f => f.replace(/\.json$/, ''));
const langs = {}, str = {};
for (const k of keys) str[k] = { en: en.strings[k].text };
const report = [], orphans = new Map();
for (const code of files) {
  if (code === 'en') { langs.en = { name: 'English', native: 'English', region: 'World', dir: 'ltr', script: 'Latin', confidence: 'complete', uncertain: 0, missing: 0 }; continue; }
  const d = JSON.parse(fs.readFileSync(path.join(DIR, code + '.json'), 'utf8'));
  let missing = 0, bad = 0, applicable = keys.length;
  for (const k of Object.keys(d.strings || {})) if (!(k in en.strings)) { if (!orphans.has(k)) orphans.set(k, []); orphans.get(k).push(code); }
  for (const k of keys) {
    const v = d.strings && d.strings[k];
    /* place.* keys are script work: a Latin-script language neither ships nor lacks them */
    if (k.startsWith('place.') && (d.script || 'Latin') === 'Latin' && !(typeof v === 'string' && v.trim())) { applicable--; continue; }
    if (typeof v !== 'string' || !v.trim()) { missing++; continue; }
    if (en.strings[k].html) { // tags must survive translation
      const tags = s => (s.match(/<\/?[a-z]+/g) || []).sort().join(',');
      if (tags(v) !== tags(en.strings[k].text)) { bad++; continue; }
    }
    str[k][code] = v;
  }
  langs[code] = { name: d.name, native: d.native, region: d.region || '', family: d.family || '', dir: d.dir || 'ltr', script: d.script || 'Latin', confidence: d.confidence || 'unreviewed', note: d.translator_note || '', uncertain: (d.uncertain || []).length, missing, review: d.review_note || '' };
  report.push(`${code.padEnd(8)} ${String(applicable - missing).padStart(3)}/${applicable}  ${String(bad).padStart(2)} bad-tags  ${String((d.uncertain || []).length).padStart(3)} uncertain  ${(d.confidence || 'unreviewed').padEnd(11)} ${d.name}`);
}
/* ---- ORPHANS: translated everywhere, absent from en.json, therefore never shipped ---- */
const orphanList = [...orphans.keys()].sort();
/* ---- DRIFT: the English string moved and its translations did not ---- */
const hash = s => crypto.createHash('sha256').update(s, 'utf8').digest('hex').slice(0, 12);
const now = {}; for (const k of keys) now[k] = hash(en.strings[k].text);
const was = fs.existsSync(SNAP) ? JSON.parse(fs.readFileSync(SNAP, 'utf8')).sources || {} : null;
const drift = was ? keys.filter(k => was[k] && was[k] !== now[k]) : [];
const fresh = was ? keys.filter(k => !was[k]) : keys;
/* ---- UNUSED: in en.json, asked for by nothing ---- */
const site0 = fs.readFileSync(SITE, 'utf8');
const cut = (s, a, b) => { const i = s.indexOf(a), j = s.indexOf(b); return i < 0 || j < 0 ? s : s.slice(0, i) + s.slice(j); };
const scan = cut(site0, 'const STR = ', '\n/* i18n:end */');
const asked = new Set(DYNAMIC);
for (const k of keys) if (k.startsWith('place.')) asked.add(k);   // looked up through place()
for (const m of scan.matchAll(/\bt\(\s*['"]([^'"]+)['"]\s*\)/g)) asked.add(m[1]);
for (const m of scan.matchAll(/data-i18n(?:-html)?=["']([^"']+)["']/g)) asked.add(m[1]);
for (const m of scan.matchAll(/(?:STR|WL|PACK)\[\s*['"]([^'"]+)['"]\s*\]/g)) asked.add(m[1]);
const unused = keys.filter(k => !asked.has(k));
// order LANGS by the picker groups; unknown codes go last
const ordered = {};
for (const [group, codes] of Object.entries(ORDER)) for (const c of codes) if (langs[c]) ordered[c] = { ...langs[c], group };
for (const c of Object.keys(langs)) if (!ordered[c]) ordered[c] = { ...langs[c], group: 'Other' };
/* ---- one language per request, not forty-one ----
   Shipping every dictionary in the document cost 206 KB gzip and 4.1 seconds of domInteractive on
   a 400 kbps phone — measured, on the exact device this product exists for. English is inlined
   because it is the fallback for every missing string; the rest are packs the app fetches when a
   language is chosen, and the service worker keeps them. The trade is honest and worth naming: the
   FIRST switch to a new language needs the network. It is paid once, by the person who switches,
   instead of four seconds paid by everybody on every cold load. */
fs.mkdirSync(PACKS, { recursive: true });
for (const f of fs.readdirSync(PACKS)) if (f.endsWith('.json')) fs.unlinkSync(path.join(PACKS, f));
let packBytes = 0;
for (const code of files) {
  if (code === 'en') continue;
  const pack = {};
  for (const k of keys) if (str[k][code] != null) pack[k] = str[k][code];
  const body = JSON.stringify({ lang: code, generated: new Date().toISOString().slice(0, 10), strings: pack });
  fs.writeFileSync(path.join(PACKS, code + '.json'), body + '\n');
  packBytes += body.length;
}
const strEn = {}; for (const k of keys) strEn[k] = str[k].en;
if (INLINE_ALL_FILE) {
  const all = {};
  for (const code of files) { if (code === 'en') continue; all[code] = {}; for (const k of keys) if (str[k][code] != null) all[code][k] = str[k][code]; }
  fs.writeFileSync(path.join(PACKS, 'all.json'), JSON.stringify({ generated: new Date().toISOString().slice(0, 10), note: 'Every pack in one object, for a single-file build that cannot fetch. Written only by --inline-all.', packs: all }) + '\n');
  console.log(`all.json written for a single-file build: ${Math.round(fs.statSync(path.join(PACKS, 'all.json')).size / 1024)} KB`);
}
const wl = {}; for (const k of INLINE_ALL) if (str[k]) wl[k] = str[k];
/* The picker's metadata only. The translator notes are prose about a language, not part of using
   it, and they were 12 KB of the 12.6 KB that LANGS cost; they live in the packs now. */
const meta = {};
for (const [c, v] of Object.entries(ordered)) meta[c] = { name: v.name, native: v.native, region: v.region, family: v.family, dir: v.dir, script: v.script, confidence: v.confidence, group: v.group, uncertain: v.uncertain, missing: v.missing };
for (const code of files) {
  if (code === 'en') continue;
  const f = path.join(PACKS, code + '.json');
  const j = JSON.parse(fs.readFileSync(f, 'utf8'));
  j.note = ordered[code].note; j.review = ordered[code].review;
  fs.writeFileSync(f, JSON.stringify(j) + '\n');
}
let site = site0;
const A = '/* i18n:begin (generated by server/scripts/i18n-build.cjs from data/i18n/*.json; do not edit by hand) */';
const B = '/* i18n:end */';
/* JSON.parse of a string literal beats an object literal for a payload this size: the JSON parser
   is a fast path, the JS parser is not. */
const lit = (o) => `JSON.parse(${JSON.stringify(JSON.stringify(o))})`;
const block = `${A}
const LANGS = ${lit(meta)};
const STR = ${lit(strEn)};          /* English: the source, and the fallback for every missing string */
const WL = ${lit(wl)};              /* the welcome gate greets in all of them before any pack loads */
const I18N_DIR = 'i18n/';
let PACK = null;                    /* the chosen language, fetched on demand */
${B}`;
if (site.includes(A)) {
  site = site.slice(0, site.indexOf(A)) + block + site.slice(site.indexOf(B) + B.length);
} else {
  const legacy = site.indexOf('/* i18n:begin');
  const a = legacy >= 0 ? legacy : site.indexOf('const LANGS = {');
  const b = legacy >= 0 ? site.indexOf(B) + B.length : site.indexOf('\n};', site.indexOf('const STR = {')) + 3;
  if (a < 0 || b < 3) throw new Error('LANGS/STR block not found');
  site = site.slice(0, a) + block + site.slice(b);
}
fs.writeFileSync(SITE, site);
fs.writeFileSync(path.join(ROOT, 'data', 'languages.json'), JSON.stringify({ generated: new Date().toISOString().slice(0, 10), source: 'data/i18n/*.json via server/scripts/i18n-build.cjs', keys: keys.length, languages: ordered }, null, 1));
console.log(report.join('\n'));
console.log(`${Object.keys(ordered).length} languages, ${keys.length} keys`);
console.log(`inline: LANGS ${Math.round(JSON.stringify(meta).length / 1024)} KB + English ${Math.round(JSON.stringify(strEn).length / 1024)} KB + welcome ${Math.round(JSON.stringify(wl).length / 1024)} KB`);
console.log(`packs:  ${files.length - 1} files, ${Math.round(packBytes / 1024)} KB total, ${Math.round(packBytes / (files.length - 1) / 1024 * 10) / 10} KB each -> site/i18n/`);
if (orphanList.length) {
  console.log(`\nORPHANS — translated but never shipped, because en.json has no such key (${orphanList.length}):`);
  for (const k of orphanList) console.log(`  ${k.padEnd(28)} in ${orphans.get(k).length} language${orphans.get(k).length === 1 ? '' : 's'}`);
  console.log('  Add the key to en.json, or delete it from the dictionaries. Silence here is how the hero shipped the word "flipDeliver".');
}
if (drift.length) {
  console.log(`\nDRIFT — the English moved and ${files.length - 1} translations did not (${drift.length}):`);
  for (const k of drift) console.log(`  ${k}\n    now: ${en.strings[k].text.slice(0, 96)}`);
  console.log('  Retranslate these, then re-run with --accept to record the new source.');
}
if (unused.length) console.log(`\nUNUSED — in en.json, asked for by nothing in the site (${unused.length}): ${unused.join(', ')}`);
if (!was || ACCEPT || !drift.length) {
  fs.writeFileSync(SNAP, JSON.stringify({ note: 'Hash of each English source string as of the last accepted build. Drift against this is reported by i18n-build.cjs; refresh it with --accept once the translations have caught up.', generated: new Date().toISOString().slice(0, 10), sources: now }, null, 1) + '\n');
  if (fresh.length && was) console.log(`\n${fresh.length} new key${fresh.length === 1 ? '' : 's'} recorded in .sources.json.`);
}
if (orphanList.length || (drift.length && !ACCEPT)) process.exitCode = 1;
