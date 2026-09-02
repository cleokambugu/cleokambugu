// Exports the site's data block to ../data/*.json so the server and the site share one model.
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import vm from 'node:vm';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..', '..');
const html = readFileSync(join(root, 'site', 'index.html'), 'utf8');
const start = html.indexOf('const UGX_PER_USD'); const end = html.indexOf('/* =====================================================================\n   Helpers');
const block = html.slice(start, end);
const ctx = {}; vm.runInNewContext(block + '\nObject.assign(ctx,{UGX_PER_USD,FUEL_UGX_PER_L,DRIVER_WAGE_PER_KM,ROUTES,PROVIDERS,FLEET,DESTS,PLANS,PLACES,LOCAL,ATLAS,AIRSTRIPS,UG_LAND,UG_LAKES});', { ctx });
const meta = { generated: new Date().toISOString().slice(0, 10), source: 'projects/ug/site/index.html data block', note: 'Every figure is an estimate. prov fields: snippet = read from a search snippet or third-party page, modelled = UG assumption, official = read on the operator page, UG model = UG own formula. See docs/arbitrage-model.md and docs/atlas.md.' };
const w = (f, o) => writeFileSync(join(root, 'data', f), JSON.stringify(o, null, 2));
w('providers.json', { ...meta, constants: { UGX_PER_USD: ctx.UGX_PER_USD, FUEL_UGX_PER_L: ctx.FUEL_UGX_PER_L, DRIVER_WAGE_PER_KM: ctx.DRIVER_WAGE_PER_KM }, providers: ctx.PROVIDERS });
w('routes.json', { ...meta, routes: ctx.ROUTES, places: ctx.PLACES, local_apps: ctx.LOCAL, airstrips: ctx.AIRSTRIPS });
w('fleet.json', { ...meta, fleet: ctx.FLEET, plans: ctx.PLANS });
w('destinations.json', { ...meta, destinations: ctx.DESTS });
w('atlas.json', { ...meta, atlas: ctx.ATLAS });
console.log('exported', ctx.ROUTES.length, 'routes', ctx.PROVIDERS.length, 'providers', Object.keys(ctx.ATLAS).length, 'atlas modes');
