// One-time codes by SMS. Providers: console (sandbox, code goes to the log), Africa's Talking (HTTP), or any
// gateway that accepts a POST with {to, message} through the generic provider. Codes expire in 10 minutes.
//
// The phone line is the account and the account is the wallet, so this file is the whole front door. Two
// things here were wrong and are worth naming, because both looked fine and neither was:
//
//   The code was four digits and every resend reset `attempts` to zero. Five guesses per code became
//   unlimited guesses per number: about 1,800 resends to walk 9,000 codes. Attempts now survive a resend,
//   and a wrong guess is charged against the number until a correct one or an expiry clears it.
//
//   Sends were unlimited. That is a guaranteed compromise, an SMS bill anyone can run up, and a way to
//   make one person's phone ring all night. Sends are capped per number and per caller, with a cool-down
//   between them.
import { randomInt, timingSafeEqual } from 'node:crypto';
import { now } from './db.js';

const MINUTE = 60 * 1000, HOUR = 60 * MINUTE, DAY = 24 * HOUR;
export const OTP_LIMITS = {
  ttl: 10 * MINUTE,     // how long a code lives
  attempts: 5,          // wrong guesses per number, across resends
  coolDown: 45 * 1000,  // between two sends to the same number
  perHour: 3,           // sends per number per hour
  perDay: 10,           // sends per number per day
  ipPerHour: 20,        // sends per caller per hour, across all numbers
  keep: 2 * DAY,        // how long the send log is kept
};

export class Otp {
  constructor(db, { provider = process.env.SMS_PROVIDER || 'console', fetchImpl = globalThis.fetch, sandbox = true, limits = OTP_LIMITS } = {}) {
    this.db = db; this.provider = provider; this.fetch = fetchImpl; this.sandbox = sandbox; this.limits = limits;
  }
  normalise(phone) {
    const p = String(phone || '').replace(/[^\d+]/g, '');
    if (/^0\d{9}$/.test(p)) return '+256' + p.slice(1);
    if (/^256\d{9}$/.test(p)) return '+' + p;
    if (/^\+256\d{9}$/.test(p)) return p;
    return null;
  }
  /* Sends allowed right now, and the reason if not. Separate from send() so the shape is testable. */
  budget(to, ip = null, at = now()) {
    const L = this.limits;
    const count = (sql, ...a) => Number(this.db.prepare(sql).get(...a).n);
    const last = this.db.prepare('select max(at) as at from otp_sends where phone = ?').get(to).at;
    if (last && at - last < L.coolDown) return { ok: false, retryIn: Math.ceil((L.coolDown - (at - last)) / 1000), why: 'a code was just sent — wait a moment before asking for another' };
    if (count('select count(*) n from otp_sends where phone = ? and at > ?', to, at - HOUR) >= L.perHour) return { ok: false, retryIn: 3600, why: 'too many codes for this number in the last hour' };
    if (count('select count(*) n from otp_sends where phone = ? and at > ?', to, at - DAY) >= L.perDay) return { ok: false, retryIn: 86400, why: 'too many codes for this number today' };
    if (ip && count('select count(*) n from otp_sends where ip = ? and at > ?', ip, at - HOUR) >= L.ipPerHour) return { ok: false, retryIn: 3600, why: 'too many codes from this device in the last hour' };
    return { ok: true };
  }
  async send(phone, { ip = null } = {}) {
    const to = this.normalise(phone); if (!to) throw Object.assign(new Error('enter a Ugandan mobile number'), { status: 400 });
    const at = now();
    const b = this.budget(to, ip, at);
    if (!b.ok) throw Object.assign(new Error(b.why), { status: 429, retryIn: b.retryIn });
    const code = String(randomInt(100000, 1000000));
    /* A resend replaces the code and extends the window. It does NOT clear `attempts`: the guess budget
       belongs to the number, not to the code, or resending is a free reset. */
    this.db.prepare('insert into otps (phone, code, expires_at, attempts) values (?,?,?,0) on conflict(phone) do update set code = excluded.code, expires_at = excluded.expires_at').run(to, code, at + this.limits.ttl);
    this.db.prepare('insert into otp_sends (phone, ip, at) values (?,?,?)').run(to, ip, at);
    this.db.prepare('delete from otp_sends where at < ?').run(at - this.limits.keep);
    const message = `${code} is your UG code. It expires in 10 minutes.`;
    if (this.provider === 'africastalking') {
      const res = await this.fetch('https://api.africastalking.com/version1/messaging', { method: 'POST', headers: { apiKey: process.env.AT_API_KEY, 'content-type': 'application/x-www-form-urlencoded', accept: 'application/json' },
        body: new URLSearchParams({ username: process.env.AT_USERNAME, to, message, from: process.env.AT_SENDER || '' }) });
      if (!res.ok) throw new Error('sms send failed');
      return { sent: true, to };
    }
    if (this.provider === 'generic' && process.env.SMS_URL) {
      const res = await this.fetch(process.env.SMS_URL, { method: 'POST', headers: { 'content-type': 'application/json', authorization: process.env.SMS_AUTH || '' }, body: JSON.stringify({ to, message }) });
      if (!res.ok) throw new Error('sms send failed');
      return { sent: true, to };
    }
    /* The console provider is the sandbox SMS gateway: the log is where the operator reads the code. It is
       never in the response — a response body travels to whoever asked, and asking is free. */
    console.log(`[otp] ${to} → ${code}`);
    return { sent: true, to };
  }
  check(phone, code) {
    const to = this.normalise(phone); if (!to) return { ok: false, why: 'bad number' };
    const row = this.db.prepare('select * from otps where phone = ?').get(to);
    if (!row) return { ok: false, why: 'no code sent' };
    if (row.expires_at < now()) { this.db.prepare('delete from otps where phone = ?').run(to); return { ok: false, why: 'code expired' }; }
    if (row.attempts >= this.limits.attempts) return { ok: false, why: 'too many attempts' };
    const a = Buffer.from(String(row.code)), b = Buffer.from(String(code ?? ''));
    if (a.length !== b.length || !timingSafeEqual(a, b)) { this.db.prepare('update otps set attempts = attempts + 1 where phone = ?').run(to); return { ok: false, why: 'wrong code' }; }
    this.db.prepare('delete from otps where phone = ?').run(to);
    return { ok: true, to };
  }
}
