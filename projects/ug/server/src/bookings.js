// Partner bookings on the trip rail. The concierge is an adapter: `sim` advances states on a clock (the prototype);
// production adapters call a partner channel (Bolt Ride Booker console, a SafeBoda business line, a staffed phone) and
// update the step from their callbacks. Steps: 0 requested · 1 placed · 2 driver assigned · 3 arriving · 4 on trip · 5 done.
import { id, now } from './db.js';

const SIM_DELAYS = [0, 1800, 4200, 8500, 11500, 17000];
const DRIVERS = [['Moses K.', 'UBM 442K'], ['Sarah A.', 'UBH 123X'], ['Denis O.', 'UBJ 908L'], ['Grace N.', 'UBK 331P'], ['Isaac T.', 'UAX 777Q']];

export class Bookings {
  constructor(db, ledger, { adapter = 'sim' } = {}) { this.db = db; this.ledger = ledger; this.adapter = adapter; }

  create(userId, body) {
    const price = Math.max(500, Math.round(Number(body.price_ugx) || 0));
    const d = DRIVERS[Math.floor(Math.random() * DRIVERS.length)];
    const b = { id: id('b'), user_id: userId, kind: body.kind === 'parcel' ? 'parcel' : 'ride', partner: String(body.partner || 'UG').slice(0, 60), partner_sub: String(body.partner_sub || '').slice(0, 80), colour: String(body.colour || '#D2202F').slice(0, 9),
      title: String(body.title || 'Trip').slice(0, 120), price_ugx: price, eta_min: Number(body.eta_min) || 6, driver: d[0], plate: d[1], step: 0, status: 'active', tx_ref: `UGB-${Date.now().toString(36).toUpperCase()}`, created_at: now(), updated_at: now() };
    this.db.prepare('insert into bookings (id, user_id, kind, partner, partner_sub, colour, title, price_ugx, eta_min, driver, plate, step, status, tx_ref, created_at, updated_at) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)')
      .run(b.id, b.user_id, b.kind, b.partner, b.partner_sub, b.colour, b.title, b.price_ugx, b.eta_min, b.driver, b.plate, b.step, b.status, b.tx_ref, b.created_at, b.updated_at);
    return { booking: b, charge: { tx_ref: b.tx_ref, amount: price, currency: 'UGX', payment_options: 'mobilemoneyuganda' } };
  }
  hold(bookingId, flwId = null) { const b = this.get(bookingId); if (!b) return null; this.ledger.holdBooking(b.id, b.price_ugx, b.tx_ref); this.db.prepare('update bookings set step = max(step, 1), updated_at = ? where id = ?').run(now(), b.id); return this.get(b.id); }
  get(bookingId) { const b = this.db.prepare('select * from bookings where id = ?').get(bookingId); return b ? this.advance(b) : null; }
  current(userId) { const b = this.db.prepare(`select * from bookings where user_id = ? and status = 'active' order by created_at desc limit 1`).get(userId); return b ? this.advance(b) : null; }

  // The simulated concierge: the step is a function of elapsed time; settlement posts once at step 5.
  advance(b) {
    if (this.adapter !== 'sim' || b.status !== 'active' || b.step < 1) return b;
    const elapsed = now() - b.created_at; let step = b.step;
    for (let k = 1; k < SIM_DELAYS.length; k++) if (elapsed >= SIM_DELAYS[k]) step = k;
    if (step !== b.step) {
      this.db.prepare('update bookings set step = ?, updated_at = ? where id = ?').run(step, now(), b.id); b.step = step;
      if (step === 5) { this.ledger.settleBooking(b.id, b.price_ugx, b.partner, Math.round(b.price_ugx * 0.05)); this.db.prepare(`update bookings set status = 'done' where id = ?`).run(b.id); b.status = 'done'; }
    }
    return b;
  }
  cancel(userId, bookingId) {
    const b = this.get(bookingId); if (!b || b.user_id !== userId) throw Object.assign(new Error('no such booking'), { status: 404 });
    if (b.step >= 2) throw Object.assign(new Error('a driver is already assigned; call them instead'), { status: 409 });
    if (b.step >= 1) this.ledger.refundBooking(b.id, b.price_ugx, userId);
    this.db.prepare(`update bookings set status = 'cancelled', updated_at = ? where id = ?`).run(now(), b.id);
    return this.get(b.id);
  }
}
