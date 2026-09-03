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
const SNAP = path.join(DIR, '.sources.json');
const ACCEPT = process.argv.includes('--accept');
const ORDER = { // picker groups, in the order they appear
  'Uganda · Central': ['lg'], 'Uganda · East': ['xog', 'myx', 'gwr', 'lsm', 'teo', 'kpz'], 'Uganda · North': ['ach', 'laj', 'kdi', 'kdj'],
  'Uganda · West Nile': ['alz', 'lgg', 'mhi', 'keo'], 'Uganda · West': ['nyn', 'cgg', 'ttj', 'nyo', 'koo'],
  'East Africa · Africa': ['sw', 'rw', 'so', 'am', 'ar', 'ln', 'ha', 'zu'],
  'World': ['en', 'fr', 'de', 'it', 'es', 'es-MX', 'pt', 'pt-BR', 'ru', 'zh-Hans', 'ja', 'ko', 'hi'],
};
/* keys the JavaScript looks up through a variable, so the source scan cannot see them */
const DYNAMIC = ['ride', 'pool', 'rent', 'deliver', 'flipRide', 'flipPool', 'flipRent', 'flipDeliver',
  'ui.requested', 'ui.placed', 'ui.driverAssigned', 'ui.arriving', 'ui.onTrip', 'ui.done'];   // the trip rail's steps
const en = JSON.parse(fs.readFileSync(path.join(DIR, 'en.json'), 'utf8'));
const keys = Object.keys(en.strings);
const files = fs.readdirSync(DIR).filter(f => f.endsWith('.json') && !f.startsWith('.')).map(f => f.replace(/\.json$/, ''));
const langs = {}, str = {};
for (const k of keys) str[k] = { en: en.strings[k].text };
const report = [], orphans = new Map();
for (const code of files) {
  if (code === 'en') { langs.en = { name: 'English', native: 'English', region: 'World', dir: 'ltr', script: 'Latin', confidence: 'complete', uncertain: 0, missing: 0 }; continue; }
  const d = JSON.parse(fs.readFileSync(path.join(DIR, code + '.json'), 'utf8'));
  let missing = 0, bad = 0;
  for (const k of Object.keys(d.strings || {})) if (!(k in en.strings)) { if (!orphans.has(k)) orphans.set(k, []); orphans.get(k).push(code); }
  for (const k of keys) {
    const v = d.strings && d.strings[k];
    if (typeof v !== 'string' || !v.trim()) { missing++; continue; }
    if (en.strings[k].html) { // tags must survive translation
      const tags = s => (s.match(/<\/?[a-z]+/g) || []).sort().join(',');
      if (tags(v) !== tags(en.strings[k].text)) { bad++; continue; }
    }
    str[k][code] = v;
  }
  langs[code] = { name: d.name, native: d.native, region: d.region || '', family: d.family || '', dir: d.dir || 'ltr', script: d.script || 'Latin', confidence: d.confidence || 'unreviewed', note: d.translator_note || '', uncertain: (d.uncertain || []).length, missing, review: d.review_note || '' };
  report.push(`${code.padEnd(8)} ${String(keys.length - missing).padStart(3)}/${keys.length}  ${String(bad).padStart(2)} bad-tags  ${String((d.uncertain || []).length).padStart(3)} uncertain  ${(d.confidence || 'unreviewed').padEnd(11)} ${d.name}`);
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
for (const m of scan.matchAll(/\bt\(\s*['"]([^'"]+)['"]\s*\)/g)) asked.add(m[1]);
for (const m of scan.matchAll(/data-i18n(?:-html)?=["']([^"']+)["']/g)) asked.add(m[1]);
for (const m of scan.matchAll(/STR\[\s*['"]([^'"]+)['"]\s*\]/g)) asked.add(m[1]);
const unused = keys.filter(k => !asked.has(k));
// order LANGS by the picker groups; unknown codes go last
const ordered = {};
for (const [group, codes] of Object.entries(ORDER)) for (const c of codes) if (langs[c]) ordered[c] = { ...langs[c], group };
for (const c of Object.keys(langs)) if (!ordered[c]) ordered[c] = { ...langs[c], group: 'Other' };
let site = site0;
const A = '/* i18n:begin (generated by server/scripts/i18n-build.cjs from data/i18n/*.json; do not edit by hand) */';
const B = '/* i18n:end */';
const block = `${A}\nconst LANGS = ${JSON.stringify(ordered)};\nconst STR = ${JSON.stringify(str)};\n${B}`;
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
console.log(`${Object.keys(ordered).length} languages, ${keys.length} keys, STR ${Math.round(JSON.stringify(str).length / 1024)} KB`);
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
