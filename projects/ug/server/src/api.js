// HTTP API. No framework: a tiny router over node:http, JSON in and out, Bearer sessions.
import { randomBytes } from 'node:crypto';
import { id, now } from './db.js';
import { httpError } from './stages.js';
import { pulse, pulseGeoJSON } from './pulse.js';
import { ROUTES, route, capFor } from './model.js';
import { forecast, foresightGeoJSON, commit as fxCommit, addEvent as fxAddEvent } from './foresight.js';

export function createApi({ db, ledger, stages, bookings, otp, flw, sandbox, version }) {
  const routes = [];
  const on = (method, pattern, handler, auth = false) => routes.push({ method, re: new RegExp('^' + pattern.replace(/:(\w+)/g, '(?<$1>[^/]+)') + '$'), handler, auth });

  const me = (u) => ({ id: u.id, name: u.name, phone: u.phone, roles: JSON.parse(u.roles), verification: u.verification, verified: u.verification === 'verified', vouches: u.vouches, agent: !!u.agent,
    rider: u.rider ? JSON.parse(u.rider) : null, owner: u.owner ? JSON.parse(u.owner) : null, comfort: u.comfort ? JSON.parse(u.comfort) : null, payout_limit_ugx: u.payout_limit_ugx, createdAt: u.created_at });
  const user = (uid) => db.prepare('select * from users where id = ?').get(uid);

  // sandbox: documents clear a minute after upload
  const sweep = () => { if (sandbox) db.prepare(`update users set verification = 'verified' where verification = 'documents_pending' and json_extract(documents, '$.at') < ?`).run(now() - 60 * 1000); };

  on('GET', '/api/health', () => ({ ok: true, version, sandbox, flwPublicKey: flw.publicKey || null, routes: ROUTES.length, time: now() }));

  // ---- identity ----
  /* Operator number verification (GSMA Mobile Connect / CAMARA Number Verification). Live, this
     proxies the carrier endpoint, which can only confirm a line over that carrier's mobile data —
     so it returns verified:false on wifi and the caller falls back to an SMS code. There is no
     carrier contract here, so it is a sandbox stub that says so in the response. */
  on('POST', '/api/auth/number-verify', async (req) => {
    const msisdn = String(req.body.msisdn || '').replace(/\D/g, '');
    if (msisdn.length < 9) throw httpError(400, 'msisdn required');
    return { verified: false, sandbox: true,
      reason: 'No carrier agreement in this build. Wire MTN or Airtel Number Verification here; it only works over mobile data.' };
  });
  on('POST', '/api/auth/otp', async (req) => otp.send(req.body.phone));
  on('POST', '/api/auth/verify', async (req) => {
    const r = otp.check(req.body.phone, req.body.code); if (!r.ok) throw httpError(401, r.why);
    let u = db.prepare('select * from users where phone = ?').get(r.to);
    if (!u) { const uid = id('u'); db.prepare('insert into users (id, phone, name, roles, created_at) values (?,?,?,?,?)').run(uid, r.to, String(req.body.name || '').slice(0, 40) || null, JSON.stringify(['rider']), now()); u = user(uid); }
    else if (req.body.name && !u.name) { db.prepare('update users set name = ? where id = ?').run(String(req.body.name).slice(0, 40), u.id); u = user(u.id); }
    const token = randomBytes(24).toString('hex');
    db.prepare('insert into sessions (token, user_id, device, created_at) values (?,?,?,?)').run(token, u.id, String(req.headers['user-agent'] || '').slice(0, 120), now());
    return { token, me: me(u) };
  });
  on('GET', '/api/me', (req) => { sweep(); return me(user(req.user.id)); }, true);
  on('PATCH', '/api/me', (req) => {
    const b = req.body; const sets = []; const args = [];
    if (b.name) { sets.push('name = ?'); args.push(String(b.name).slice(0, 40)); }
    if (Array.isArray(b.roles)) { sets.push('roles = ?'); args.push(JSON.stringify(b.roles.filter((r) => ['rider', 'driver', 'owner'].includes(r)))); }
    if (b.rider) { sets.push('rider = ?'); args.push(JSON.stringify(b.rider)); }
    if (b.owner) { sets.push('owner = ?'); args.push(JSON.stringify(b.owner)); }
    if (b.agent != null) { sets.push('agent = ?'); args.push(b.agent ? 1 : 0); }
    if (b.lang && /^[a-z]{2,3}$/.test(b.lang)) { sets.push('lang = ?'); args.push(b.lang); }
    if (sets.length) { args.push(req.user.id); db.prepare(`update users set ${sets.join(', ')} where id = ?`).run(...args); }
    return me(user(req.user.id));
  }, true);
  on('DELETE', '/api/session', (req) => { db.prepare('delete from sessions where token = ?').run(req.token); return { ok: true }; }, true);

  on('GET', '/api/comfort', (req) => me(user(req.user.id)).comfort, true);
  on('PUT', '/api/comfort', (req) => {
    const c = req.body || {}; const clean = { base: String(c.base || 'Kampala').slice(0, 40), radius: Math.min(40, Math.max(3, Number(c.radius) || 10)), corridors: (c.corridors || []).filter((x) => route(x)).slice(0, 30),
      days: (c.days || []).slice(0, 7), hours: (c.hours || []).slice(0, 4), vehicle: String(c.vehicle || 'RAV4').slice(0, 30), plate: String(c.plate || '').toUpperCase().slice(0, 12), nos: (c.nos || []).slice(0, 6), driver_type: c.driver_type === 'going_anyway' ? 'going_anyway' : 'for_hire', min_payout_ugx: Number(c.min_payout_ugx) || 0 };
    const roles = new Set(JSON.parse(user(req.user.id).roles)); roles.add('driver');
    db.prepare('update users set comfort = ?, roles = ? where id = ?').run(JSON.stringify(clean), JSON.stringify([...roles]), req.user.id);
    return clean;
  }, true);
  on('POST', '/api/me/documents', (req) => {
    const d = { plate: !!req.body.plate, permit: !!req.body.permit, insurance: !!req.body.insurance, at: now() };
    db.prepare(`update users set documents = ?, verification = case when verification = 'verified' then 'verified' else 'documents_pending' end where id = ?`).run(JSON.stringify(d), req.user.id);
    return me(user(req.user.id));
  }, true);
  on('POST', '/api/me/verify-sandbox', (req) => { if (!sandbox) throw httpError(403, 'sandbox only'); db.prepare(`update users set verification = 'verified' where id = ?`).run(req.user.id); return me(user(req.user.id)); }, true);
  on('POST', '/api/vouches', (req) => {
    const drv = user(req.body.driverId); if (!drv) throw httpError(404, 'no such driver'); if (drv.id === req.user.id) throw httpError(400, 'you cannot vouch for yourself');
    const v = user(req.user.id); if (v.verification === 'none' && !v.agent) throw httpError(403, 'vouchers must be verified or agents');
    db.prepare('insert or ignore into vouches (voucher_id, driver_id, circle, created_at) values (?,?,?,?)').run(req.user.id, drv.id, String(req.body.circle || '').slice(0, 40), now());
    const n = db.prepare('select count(*) c from vouches where driver_id = ?').get(drv.id).c;
    db.prepare(`update users set vouches = ?, verification = case when verification = 'none' and ? >= 2 then 'vouched' else verification end where id = ?`).run(n, n, drv.id);
    return { vouches: n };
  }, true);

  // ---- stages ----
  on('GET', '/api/stages', (req) => stages.list({ status: req.query.status, route: req.query.corridor }));
  on('POST', '/api/stages', (req) => stages.create(req.user.id, req.body), true);
  on('GET', '/api/stages/:id', (req) => { const s = stages.get(req.params.id); if (!s) throw httpError(404, 'no such stage'); return s; });
  on('POST', '/api/stages/:id/intents', (req) => stages.queue(req.user.id, req.params.id), true);
  on('POST', '/api/intents/:id/confirm', async (req) => {
    const it = stages.intent(req.params.id); if (!it || it.user_id !== req.user.id) throw httpError(404, 'no such intent');
    if (flw.live) {
      if (!req.body.transaction_id) throw httpError(400, 'transaction_id required');
      const v = await flw.verify(req.body.transaction_id);
      if (!v.ok || v.tx_ref !== it.tx_ref || v.currency !== 'UGX' || Number(v.amount) < it.amount_ugx) throw httpError(402, `payment ${v.status}; nothing held`);
      return stages.hold(it.id, { flwId: String(v.id) });
    }
    if (!sandbox) throw httpError(503, 'payments not configured');
    return stages.hold(it.id, { flwId: 'sandbox' });
  }, true);
  on('DELETE', '/api/intents/:id', (req) => stages.cancel(req.user.id, req.params.id), true);
  on('GET', '/api/intents', (req) => db.prepare('select i.*, s.route, s.day, s.win, s.status stage_status, s.driver_label from intents i join stages s on s.id = i.stage_id where i.user_id = ? order by i.created_at desc limit 50').all(req.user.id), true);
  on('POST', '/api/stages/:id/depart', (req) => stages.depart(req.user.id, req.params.id), true);
  on('GET', '/api/offers', (req) => { sweep(); return stages.offersFor(req.user.id); }, true);
  on('POST', '/api/offers/:id/accept', (req) => { sweep(); return stages.accept(req.user.id, req.params.id); }, true);
  on('POST', '/api/offers/:id/decline', (req) => { stages.decline(req.user.id, req.params.id); return { ok: true }; }, true);
  on('GET', '/api/earnings', (req) => ({ payable_ugx: ledger.balance(`payable:driver:${req.user.id}`), journal: ledger.journalFor(`payable:driver:${req.user.id}`).slice(-20) }), true);

  // ---- bookings (stay on UG) ----
  on('POST', '/api/bookings', (req) => bookings.create(req.user.id, req.body), true);
  on('POST', '/api/bookings/:id/confirm', async (req) => {
    const b = bookings.get(req.params.id); if (!b || b.user_id !== req.user.id) throw httpError(404, 'no such booking');
    if (flw.live) { const v = await flw.verify(req.body.transaction_id); if (!v.ok || v.tx_ref !== b.tx_ref) throw httpError(402, `payment ${v.status}`); return bookings.hold(b.id, String(v.id)); }
    if (!sandbox) throw httpError(503, 'payments not configured');
    return bookings.hold(b.id, 'sandbox');
  }, true);
  on('GET', '/api/bookings/current', (req) => bookings.current(req.user.id), true);
  on('POST', '/api/bookings/:id/cancel', (req) => bookings.cancel(req.user.id, req.params.id), true);

  // ---- pulse, fares, feedback, plugins ----
  on('GET', '/api/pulse', (req) => pulse(db, req.query.role || 'rider'));
  on('GET', '/api/pulse.geojson', () => pulseGeoJSON(db));
  on('POST', '/api/fares/samples', (req) => { if (!route(req.body.route)) throw httpError(400, 'unknown route'); db.prepare('insert into fare_samples (user_id, route, provider, paid_ugx, at) values (?,?,?,?,?)').run(req.user.id, req.body.route, String(req.body.provider || '').slice(0, 30), Math.round(Number(req.body.paid_ugx) || 0), now()); return { ok: true }; }, true);
  on('GET', '/api/fares/index', () => db.prepare(`select route, provider, count(*) n, round(avg(paid_ugx)) avg_ugx, min(paid_ugx) min_ugx, max(paid_ugx) max_ugx from fare_samples where at > ? group by route, provider`).all(now() - 7 * 24 * 3600 * 1000));
  on('POST', '/api/feedback', (req) => { db.prepare('insert into feedback (user_id, booking_id, text, tags, rating, at) values (?,?,?,?,?,?)').run(req.user.id, req.body.booking_id || null, String(req.body.text || '').slice(0, 2000), JSON.stringify(req.body.tags || []), Number(req.body.rating) || null, now()); return { ok: true }; }, true);
  on('POST', '/api/plugins/:id/connect', (req) => {
    const allowed = ['felt', 'infrared', 'tazama', 'cephable', 'clarifom']; if (!allowed.includes(req.params.id)) throw httpError(404, 'no such plug-in');
    const ep = String(req.body.endpoint || ''); if (!/^https?:\/\/[\w.\-:]+(\/[^\s"'<>]*)?$/.test(ep)) throw httpError(400, 'endpoint must be a plain http(s) URL');
    db.prepare('insert into plugins (user_id, plugin, endpoint, consent, connected_at) values (?,?,?,?,?) on conflict(user_id, plugin) do update set endpoint = excluded.endpoint, consent = excluded.consent, connected_at = excluded.connected_at').run(req.user.id, req.params.id, ep, req.body.consent ? 1 : 0, now());
    return { ok: true };
  }, true);
  on('GET', '/api/plugins', (req) => db.prepare('select plugin, endpoint, consent, connected_at from plugins where user_id = ?').all(req.user.id), true);

  // ---- foresight: demand before it happens ----
  on('GET', '/api/foresight', (req) => forecast(db, { days: Math.min(14, Number(req.query.days) || 7) }));
  on('GET', '/api/foresight.geojson', () => foresightGeoJSON(db));
  on('POST', '/api/foresight/commit', (req) => fxCommit(db, req.user.id, req.body), true);
  on('POST', '/api/foresight/events', (req) => { const u = user(req.user.id); if (!u.agent && !u.comfort) throw httpError(403, 'agents and drivers can add events'); return fxAddEvent(db, req.user.id, req.body); }, true);

  // ---- Flutterwave webhook: verified against the processor, idempotent through the ledger refs ----
  on('POST', '/api/webhooks/flutterwave', async (req) => {
    if (!flw.webhookValid(req.headers)) throw httpError(401, 'bad webhook hash');
    const ev = req.body; db.prepare('insert into events (kind, ref, payload, at) values (?,?,?,?)').run(ev.event || 'unknown', ev.data?.tx_ref || null, JSON.stringify(ev).slice(0, 20000), now());
    if (ev.event === 'charge.completed' && ev.data?.status === 'successful') {
      const v = flw.live ? await flw.verify(ev.data.id) : { ok: true, tx_ref: ev.data.tx_ref, id: ev.data.id, amount: ev.data.amount };
      if (!v.ok) return { ok: true, ignored: 'not successful on verify' };
      const it = db.prepare('select * from intents where tx_ref = ?').get(v.tx_ref); if (it) { stages.hold(it.id, { flwId: String(v.id), amount: v.amount }); return { ok: true, held: it.id }; }
      const b = db.prepare('select * from bookings where tx_ref = ?').get(v.tx_ref); if (b) { bookings.hold(b.id, String(v.id)); return { ok: true, held: b.id }; }
    }
    return { ok: true };
  });

  return { routes, me };
}

// ---- request plumbing ----
export async function handle(api, db, req, res, { serveStatic }) {
  const url = new URL(req.url, 'http://x');
  const query = Object.fromEntries(url.searchParams.entries());
  const send = (status, body, headers = {}) => { res.writeHead(status, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', ...headers }); res.end(JSON.stringify(body)); };
  if (req.method === 'OPTIONS') { res.writeHead(204, cors()); return res.end(); }
  for (const r of api.routes) {
    if (r.method !== req.method) continue;
    const m = url.pathname.match(r.re); if (!m) continue;
    try {
      let body = {};
      if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(req.method)) { const raw = await readBody(req, 64 * 1024); body = raw ? JSON.parse(raw) : {}; }
      const ctx = { params: m.groups || {}, query, body, headers: req.headers, user: null, token: null };
      if (r.auth) {
        const auth = String(req.headers.authorization || ''); const token = auth.startsWith('Bearer ') ? auth.slice(7) : null;
        const s = token && db.prepare('select user_id from sessions where token = ?').get(token);
        if (!s) return send(401, { error: 'sign in first' }, cors());
        ctx.user = { id: s.user_id }; ctx.token = token;
      }
      const out = await r.handler(ctx);
      return send(200, out ?? { ok: true }, cors());
    } catch (e) {
      const status = e.status || (e instanceof SyntaxError ? 400 : 500);
      if (status === 500) console.error(e);
      return send(status, { error: status === 500 ? 'something broke on our side' : e.message }, cors());
    }
  }
  if (url.pathname.startsWith('/api/')) return send(404, { error: 'no such endpoint' }, cors());
  return serveStatic(url.pathname, res);
}
const cors = () => ({ 'access-control-allow-origin': process.env.UG_CORS_ORIGIN || '*', 'access-control-allow-headers': 'authorization, content-type, verif-hash', 'access-control-allow-methods': 'GET,POST,PUT,PATCH,DELETE,OPTIONS' });
function readBody(req, limit) { return new Promise((resolve, reject) => { let data = ''; req.on('data', (c) => { data += c; if (data.length > limit) { reject(httpError(413, 'body too large')); req.destroy(); } }); req.on('end', () => resolve(data)); req.on('error', reject); }); }
