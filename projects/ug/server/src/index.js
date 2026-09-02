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
import { seed } from './seed.js';

const here = fileURLToPath(new URL('.', import.meta.url));
const VERSION = '1.2.0';
const sandbox = process.env.UG_SANDBOX === '1' || !process.env.FLW_SECRET_KEY;
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
    console.log(`UG ${VERSION} · ${sandbox ? 'SANDBOX (no real money, OTP codes returned to the client)' : 'LIVE'} · http://localhost:${port}`);
  });
}
