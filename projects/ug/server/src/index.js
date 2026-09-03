// UG server: serves the site and the API from one process. `npm start` in production, `npm run dev` for the sandbox.
import http from 'node:http';
import { createReadStream, statSync } from 'node:fs';
import { join, extname, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { openDb } from './db.js';
import { Ledger } from './ledger.js';
import { Stages } from './stages.js';
import { Bookings } from './bookings.js';
import { Otp } from './otp.js';
import { Flutterwave } from './flutterwave.js';
import { createApi, handle } from './api.js';
import { assertInvariants } from './ledger.js';
import { seed } from './seed.js';

const here = fileURLToPath(new URL('.', import.meta.url));
const VERSION = '1.2.0';
/* Sandbox is a deliberate choice, never a consequence of a missing key. It used to be
   `UG_SANDBOX === '1' || !FLW_SECRET_KEY`, so a deploy that forgot the Flutterwave key came up in
   sandbox — with sandbox document verification and a sandbox payment path — and nothing said so.
   Missing configuration now stops the process instead of quietly relaxing it. */
const sandbox = process.env.UG_SANDBOX === '1';
if (sandbox && process.env.NODE_ENV === 'production') throw new Error('refusing to run the sandbox in production: unset UG_SANDBOX');
if (!sandbox && !process.env.FLW_SECRET_KEY) throw new Error('FLW_SECRET_KEY is required outside the sandbox: set it, or set UG_SANDBOX=1 to run without payments');
const siteDir = process.env.UG_SITE_DIR || join(here, '..', '..', 'site');
const brandDir = join(here, '..', '..', 'brand');

export function buildApp({ dbPath } = {}) {
  const db = openDb(dbPath);
  const ledger = new Ledger(db);
  const stages = new Stages(db, ledger, { sandbox });
  const bookings = new Bookings(db, ledger, { adapter: process.env.UG_CONCIERGE || 'sim' });
  const otp = new Otp(db, { sandbox });
  const flw = new Flutterwave();
  const api = createApi({ db, ledger, stages, bookings, otp, flw, sandbox, version: VERSION });
  if (process.env.UG_DEMO_SEED === '1') seed({ db, stages, ledger });
  return { db, ledger, stages, bookings, otp, flw, api };
}

const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.webmanifest': 'application/manifest+json', '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon', '.txt': 'text/plain; charset=utf-8', '.yaml': 'text/yaml' };
function serveStatic(pathname, res) {
  let p = decodeURIComponent(pathname); if (p === '/' || p === '') p = '/index.html';
  const base = p.startsWith('/brand/') ? brandDir : siteDir; const rel = p.startsWith('/brand/') ? p.slice(7) : p;
  const file = normalize(join(base, rel)); if (!file.startsWith(base)) { res.writeHead(403); return res.end(); }
  let st; try { st = statSync(file); } catch { res.writeHead(404, { 'content-type': 'text/plain' }); return res.end('not found'); }
  if (st.isDirectory()) return serveStatic(p + '/index.html', res);
  const ext = extname(file);
  res.writeHead(200, { 'content-type': TYPES[ext] || 'application/octet-stream', 'cache-control': ext === '.html' ? 'no-cache' : 'public, max-age=3600', 'x-ug-version': VERSION,
    'content-security-policy': "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://checkout.flutterwave.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.flutterwave.com https://checkout.flutterwave.com; frame-src https://checkout.flutterwave.com; media-src 'self' blob:" });
  createReadStream(file).pipe(res);
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const app = buildApp();
  const port = Number(process.env.PORT) || 8787;
  http.createServer((req, res) => handle(app.api, app.db, req, res, { serveStatic })).listen(port, () => {
    console.log(`UG ${VERSION} · ${sandbox ? 'SANDBOX (no real money; OTP codes go to this log)' : 'LIVE'} · http://localhost:${port}`);
  });
  /* Two things a ledger cannot do for itself: give money back when a car never filled, and notice that
     it has stopped agreeing with the world. Both on a timer, both loud. The sweep also runs lazily on
     stage reads, so a stopped timer delays a refund rather than losing it. */
  setInterval(() => {
    try { const n = app.stages.sweepCutoffs(); if (n) console.log(`[sweep] refunded ${n} seat(s) on stages that did not fill`); }
    catch (e) { console.error('[sweep]', e); }
  }, 5 * 60 * 1000).unref();
  setInterval(() => {
    try { assertInvariants(app.db); } catch (e) { console.error('[invariants]', e.message); }
  }, 60 * 60 * 1000).unref();
}
