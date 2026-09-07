// The front door. Each of these is a break that shipped, written as the invariant rather than the symptom.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { openDb, now } from '../src/db.js';
import { Otp, OTP_LIMITS } from '../src/otp.js';

const fresh = () => openDb(':memory:');
const codeFor = (db, to) => db.prepare('select code from otps where phone = ?').get(to).code;
// a clock the limiter can be walked past, so the test does not sleep
const past = (db, to, ms) => db.prepare('update otp_sends set at = at - ? where phone = ?').run(ms, to);

test('the code never travels in a response body', async () => {
  const db = fresh(); const otp = new Otp(db, { sandbox: true });
  const r = await otp.send('0772 123 456');
  assert.deepEqual(Object.keys(r).sort(), ['sent', 'to']);
  assert.equal(r.to, '+256772123456');
});

test('the code is six digits, not four', async () => {
  const db = fresh(); const otp = new Otp(db, { sandbox: true });
  await otp.send('0772123456');
  assert.match(codeFor(db, '+256772123456'), /^\d{6}$/);
});

test('a resend does not refund the guess budget', async () => {
  const db = fresh(); const otp = new Otp(db, { sandbox: true });
  const to = '+256772123456';
  await otp.send(to);
  for (let i = 0; i < OTP_LIMITS.attempts; i++) assert.equal(otp.check(to, '000000').ok, false);
  assert.equal(otp.check(to, codeFor(db, to)).why, 'too many attempts'); // spent, even with the right code

  past(db, to, OTP_LIMITS.coolDown + 1);
  await otp.send(to);                                     // a new code, and the old budget
  const real = codeFor(db, to);
  const r = otp.check(to, real);
  assert.equal(r.ok, false, 'resending must not reset attempts — that is unlimited guesses per number');
  assert.equal(r.why, 'too many attempts');
});

test('sends are capped per number, per hour and per day', async () => {
  const db = fresh(); const otp = new Otp(db, { sandbox: true });
  const to = '+256772123456';
  await otp.send(to);
  await assert.rejects(() => otp.send(to), (e) => e.status === 429 && /just sent/.test(e.message));   // cool-down

  for (let i = 1; i < OTP_LIMITS.perHour; i++) { past(db, to, OTP_LIMITS.coolDown + 1); await otp.send(to); }
  past(db, to, OTP_LIMITS.coolDown + 1);
  await assert.rejects(() => otp.send(to), (e) => e.status === 429 && /last hour/.test(e.message));

  // walk the hour window past, and the day cap is what holds
  db.prepare('update otp_sends set at = at - ? where phone = ?').run(2 * 60 * 60 * 1000, to);
  for (let i = OTP_LIMITS.perHour; i < OTP_LIMITS.perDay; i++) {
    await otp.send(to);
    db.prepare('update otp_sends set at = at - ? where phone = ? and at > ?').run(2 * 60 * 60 * 1000, to, now() - 60 * 1000);
  }
  await assert.rejects(() => otp.send(to), (e) => e.status === 429 && /today/.test(e.message));
});

test('one caller cannot farm codes across many numbers', async () => {
  const db = fresh(); const otp = new Otp(db, { sandbox: true });
  const ip = '102.0.0.1';
  for (let i = 0; i < OTP_LIMITS.ipPerHour; i++) await otp.send('077200' + String(i).padStart(4, '0'), { ip });
  await assert.rejects(() => otp.send('0772999999', { ip }), (e) => e.status === 429 && /this device/.test(e.message));
  await otp.send('0772999999', { ip: '102.0.0.2' });   // a different caller is unaffected
});

test('an expired code is gone, not merely refused', async () => {
  const db = fresh(); const otp = new Otp(db, { sandbox: true });
  const to = '+256772123456';
  await otp.send(to);
  db.prepare('update otps set expires_at = ? where phone = ?').run(now() - 1, to);
  assert.equal(otp.check(to, codeFor(db, to)).why, 'code expired');
  assert.equal(db.prepare('select count(*) n from otps where phone = ?').get(to).n, 0);
});

test('the sandbox flag is a choice, never a consequence of a missing key', async () => {
  const src = await import('node:fs').then((fs) => fs.readFileSync(new URL('../src/index.js', import.meta.url), 'utf8'));
  assert.ok(!/sandbox\s*=\s*[^;]*!process\.env\.FLW_SECRET_KEY/.test(src),
    'a missing Flutterwave key must not put the server in sandbox');
  assert.match(src, /FLW_SECRET_KEY is required outside the sandbox/);
  assert.match(src, /refusing to run the sandbox in production/);
});
