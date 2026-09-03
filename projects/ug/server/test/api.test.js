import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
process.env.UG_SANDBOX = '1'; process.env.UG_DEMO_SEED = '1';
const { buildApp } = await import('../src/index.js');
const { handle } = await import('../src/api.js');

const app = buildApp({ dbPath: ':memory:' });
const server = http.createServer((req, res) => handle(app.api, app.db, req, res, { serveStatic: (p, r) => { r.writeHead(200, { 'content-type': 'text/plain' }); r.end('static ' + p); } }));
await new Promise((r) => server.listen(0, r));
const base = `http://127.0.0.1:${server.address().port}`;
after(() => server.close());
const call = async (method, path, body, token) => { const res = await fetch(base + path, { method, headers: { 'content-type': 'application/json', ...(token ? { authorization: 'Bearer ' + token } : {}) }, body: body ? JSON.stringify(body) : undefined }); return { status: res.status, body: await res.json() }; };

test('health, otp, session, comfort, a seat, an offer, the rail', async () => {
  const h = await call('GET', '/api/health'); assert.equal(h.body.ok, true); assert.equal(h.body.sandbox, true);
  const o = await call('POST', '/api/auth/otp', { phone: '0772 123 456' }); assert.equal(o.status, 200);
  // the code is never in the response: an operator reads it from the log, a test reads it from the table
  assert.equal(o.body.sandboxCode, undefined);
  const code = app.db.prepare('select code from otps where phone = ?').get('+256772123456').code;
  assert.match(code, /^\d{6}$/);
  const bad = await call('POST', '/api/auth/verify', { phone: '0772123456', code: '000000' }); assert.equal(bad.status, 401);
  const v = await call('POST', '/api/auth/verify', { phone: '0772123456', code, name: 'Brenda' }); assert.equal(v.status, 200); const tok = v.body.token; assert.equal(v.body.me.name, 'Brenda');
  const unauth = await call('GET', '/api/me'); assert.equal(unauth.status, 401);
  const c = await call('PUT', '/api/comfort', { base: 'Ntinda', radius: 15, corridors: ['kampala-jinja', 'nope'], vehicle: 'RAV4', plate: 'ubh 123x' }, tok); assert.deepEqual(c.body.corridors, ['kampala-jinja']); assert.equal(c.body.plate, 'UBH 123X');
  const me = await call('GET', '/api/me', null, tok); assert.ok(me.body.roles.includes('driver'));
  const stages = await call('GET', '/api/stages'); assert.ok(stages.body.length >= 6); const jinja = stages.body.find((s) => s.route === 'kampala-jinja'); assert.equal(jinja.seats, 3);
  const q = await call('POST', `/api/stages/${jinja.id}/intents`, {}, tok); assert.equal(q.status, 200); assert.equal(q.body.charge.currency, 'UGX');
  const held = await call('POST', `/api/intents/${q.body.intent.id}/confirm`, {}, tok); assert.equal(held.body.state, 'manufactured');
  const full = await call('GET', `/api/stages/${jinja.id}`); assert.equal(full.body.status, 'full');
  // Brenda is the driver too (comfort map covers Jinja) but not verified: offer exists, accept refused
  const offers = await call('GET', '/api/offers', null, tok); assert.ok(offers.body.length >= 1);
  const refused = await call('POST', `/api/offers/${offers.body[0].id}/accept`, {}, tok); assert.equal(refused.status, 403);
  await call('POST', '/api/me/verify-sandbox', {}, tok);
  const acc = await call('POST', `/api/offers/${offers.body[0].id}/accept`, {}, tok); assert.equal(acc.status, 200); assert.equal(acc.body.status, 'funded');
  const b = await call('POST', '/api/bookings', { kind: 'ride', partner: 'Faras', partner_sub: 'Boda', title: 'Ntinda → Downtown Kampala', price_ugx: 7000 }, tok); assert.equal(b.status, 200);
  const bh = await call('POST', `/api/bookings/${b.body.booking.id}/confirm`, {}, tok); assert.equal(bh.body.step, 1);
  const cur = await call('GET', '/api/bookings/current', null, tok); assert.equal(cur.body.id, b.body.booking.id);
  const p = await call('GET', '/api/pulse?role=driver'); assert.ok(Array.isArray(p.body)); assert.ok(p.body.find((t) => t.town === 'Jinja'));
  const g = await call('GET', '/api/pulse.geojson'); assert.equal(g.body.type, 'FeatureCollection');
  const wh = await call('POST', '/api/webhooks/flutterwave', { event: 'charge.completed' }); assert.equal(wh.status, 401);
  const out = await call('DELETE', '/api/session', {}, tok); assert.equal(out.body.ok, true);
  const gone = await call('GET', '/api/me', null, tok); assert.equal(gone.status, 401);
});
