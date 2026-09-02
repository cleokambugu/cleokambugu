// One-time codes by SMS. Providers: console (sandbox, code returned to the client), Africa's Talking (HTTP), or any
// gateway that accepts a POST with {to, message} through the generic provider. Codes expire in 10 minutes, 5 attempts.
import { randomInt } from 'node:crypto';
import { now } from './db.js';

export class Otp {
  constructor(db, { provider = process.env.SMS_PROVIDER || 'console', fetchImpl = globalThis.fetch, sandbox = true } = {}) {
    this.db = db; this.provider = provider; this.fetch = fetchImpl; this.sandbox = sandbox;
  }
  normalise(phone) {
    const p = String(phone || '').replace(/[^\d+]/g, '');
    if (/^0\d{9}$/.test(p)) return '+256' + p.slice(1);
    if (/^256\d{9}$/.test(p)) return '+' + p;
    if (/^\+256\d{9}$/.test(p)) return p;
    return null;
  }
  async send(phone) {
    const to = this.normalise(phone); if (!to) throw Object.assign(new Error('enter a Ugandan mobile number'), { status: 400 });
    const code = String(randomInt(1000, 9999));
    this.db.prepare('insert into otps (phone, code, expires_at, attempts) values (?,?,?,0) on conflict(phone) do update set code = excluded.code, expires_at = excluded.expires_at, attempts = 0').run(to, code, now() + 10 * 60 * 1000);
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
    console.log(`[otp] ${to} → ${code}`);
    return { sent: true, to, sandboxCode: this.sandbox ? code : undefined };
  }
  check(phone, code) {
    const to = this.normalise(phone); if (!to) return { ok: false, why: 'bad number' };
    const row = this.db.prepare('select * from otps where phone = ?').get(to);
    if (!row) return { ok: false, why: 'no code sent' };
    if (row.expires_at < now()) return { ok: false, why: 'code expired' };
    if (row.attempts >= 5) return { ok: false, why: 'too many attempts' };
    if (row.code !== String(code)) { this.db.prepare('update otps set attempts = attempts + 1 where phone = ?').run(to); return { ok: false, why: 'wrong code' }; }
    this.db.prepare('delete from otps where phone = ?').run(to);
    return { ok: true, to };
  }
}
