// Exports the site's data block to ../data/*.json so the server and the site share one model.
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import vm from 'node:vm';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..', '..');
const html = readFileSync(join(root, 'site', 'index.html'), 'utf8');
const start = html.indexOf('const UGX_PER_USD'); const end = html.indexOf('/* =====================================================================\n   Helpers');
/* Anchor on the generated markers, not on `const LANGS = {`. That literal was the anchor until the
   dictionaries were split into packs and the block became `const LANGS = JSON.parse(…)`, at which
   point indexOf returned -1 and this script exported an empty slice and a ReferenceError. A marker
   is a contract; the shape of the value on the other side of it is not. */
const A = '/* i18n:begin', B = '/* i18n:end */';
const i18nStart = html.indexOf(A), i18nEnd = html.indexOf(B);
if (start < 0 || end < 0 || i18nStart < 0 || i18nEnd < 0) throw new Error('site/index.html does not carry the blocks this export reads');
const block = html.slice(start, end) + '\n' + html.slice(i18nStart, i18nEnd);
const ctx = {}; vm.runInNewContext(block + '\nObject.assign(ctx,{UGX_PER_USD,FUEL_UGX_PER_L,DRIVER_WAGE_PER_KM,ROUTES,PROVIDERS,FLEET,DESTS,PLANS,PLACES,LOCAL,ATLAS,AIRSTRIPS,UG_LAND,UG_LAKES,SEASONS,VENUES,EVENTS,VEHICLE_CLASSES,LANGS,STR});', { ctx });
const meta = { generated: new Date().toISOString().slice(0, 10), source: 'projects/ug/site/index.html data block', note: 'Every figure is an estimate. prov fields: snippet = read from a search snippet or third-party page, modelled = UG assumption, official = read on the operator page, UG model = UG own formula. See docs/arbitrage-model.md and docs/atlas.md.' };
const w = (f, o) => writeFileSync(join(root, 'data', f), JSON.stringify(o, null, 2));
w('providers.json', { ...meta, constants: { UGX_PER_USD: ctx.UGX_PER_USD, FUEL_UGX_PER_L: ctx.FUEL_UGX_PER_L, DRIVER_WAGE_PER_KM: ctx.DRIVER_WAGE_PER_KM }, providers: ctx.PROVIDERS });
w('routes.json', { ...meta, routes: ctx.ROUTES, places: ctx.PLACES, local_apps: ctx.LOCAL, airstrips: ctx.AIRSTRIPS });
w('fleet.json', { ...meta, fleet: ctx.FLEET, plans: ctx.PLANS });
w('destinations.json', { ...meta, destinations: ctx.DESTS });
w('atlas.json', { ...meta, atlas: ctx.ATLAS });
w('foresight.json', { ...meta, vehicle_classes: ctx.VEHICLE_CLASSES, seasons: ctx.SEASONS, venues: ctx.VENUES, events: ctx.EVENTS });
/* data/languages.json belongs to server/scripts/i18n-build.cjs, which builds it from the forty-one
   dictionaries. This script used to write it too, from whatever the site happened to hold, so the
   file said something different depending on which script ran last. One owner. */
console.log('exported', ctx.ROUTES.length, 'routes', ctx.PROVIDERS.length, 'providers', Object.keys(ctx.ATLAS).length, 'atlas modes',
  '·', Object.keys(ctx.LANGS).length, 'languages and', Object.keys(ctx.STR).length, 'source strings read back from the site');
