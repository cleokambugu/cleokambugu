// The Virtual Stage: intents, fill, manufacture, offers, acceptance, departure, settlement.
// Intent states: queued → held → manufactured → accepted → departed → settled | refunded
import { id, now } from './db.js';
import { route, seatPrice, fullPrice, minFill, poolSeatCost, capFor } from './model.js';
import { scheduleTimes, cutoffSentence } from './schedule.js';

export class Stages {
  constructor(db, ledger, opts = {}) { this.db = db; this.ledger = ledger; this.sandbox = !!opts.sandbox; this._swept = 0; }

  /* Lazily, at most once a minute, so a stopped timer cannot leave money sitting in a car that never left. */
  sweepIfDue(at = now()) { if (at - this._swept < 60 * 1000) return 0; this._swept = at; return this.sweepCutoffs(at); }

  list(filter = {}) {
    this.sweepIfDue();
    let sql = 'select * from stages'; const w = []; const args = [];
    if (filter.status) { w.push('status = ?'); args.push(filter.status); }
    if (filter.route) { w.push('route = ?'); args.push(filter.route); }
    if (w.length) sql += ' where ' + w.join(' and ');
    sql += ' order by created_at desc';
    return this.db.prepare(sql).all(...args).map((s) => this.decorate(s));
  }
  get(stageId) { const s = this.db.prepare('select * from stages where id = ?').get(stageId); return s ? this.decorate(s) : null; }

  decorate(s) {
    const seats = this.db.prepare(`select count(*) c from intents where stage_id = ? and state in ('held','manufactured','accepted','departed','settled')`).get(s.id).c;
    const riders = this.db.prepare(`select u.name from intents i join users u on u.id = i.user_id where i.stage_id = ? and i.state in ('held','manufactured','accepted','departed','settled')`).all(s.id).map((r) => (r.name || 'U').slice(0, 2).toUpperCase());
    const st = { ...s, seats: Number(seats), riders, circles: JSON.parse(s.circles || '[]'), guarantee: !!s.guarantee };
    const r = route(s.route);
    st.km = r?.km; st.min = r?.min; st.from = r?.from; st.to = r?.to;
    st.seat_price_ugx = seatPrice(st); st.price_when_full_ugx = fullPrice(st);
    st.cutoff_at = s.cutoff_at || null; st.depart_by = s.depart_by || null;
    st.cutoff_promise = cutoffSentence(s.cutoff_at);
    return st;
  }

  create(userId, body) {
    const r = route(body.route); if (!r) throw httpError(400, 'unknown route');
    const s = { id: id('s'), route: r.id, day: body.day || 'Sat', win: body.win || '06:00–08:00', cutoff: body.cutoff || 'the evening before', pickup: body.pickup || null,
      cap: Math.min(6, Math.max(2, Number(body.cap) || 4)), min_fill: minFill(r), guarantee: r.entebbe ? 1 : 0, status: 'filling', created_by: userId, created_at: now(), circles: JSON.stringify(body.circles || []) };
    Object.assign(s, scheduleTimes(s, s.created_at));
    this.db.prepare('insert into stages (id, route, day, win, cutoff, pickup, cap, min_fill, guarantee, status, created_by, created_at, circles, cutoff_at, depart_by) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)')
      .run(s.id, s.route, s.day, s.win, s.cutoff, s.pickup, s.cap, s.min_fill, s.guarantee, s.status, s.created_by, s.created_at, s.circles, s.cutoff_at, s.depart_by);
    return this.get(s.id);
  }

  // A rider queues money. Returns the intent and the charge the client must complete.
  queue(userId, stageId) {
    const st = this.get(stageId); if (!st) throw httpError(404, 'no such stage');
    if (st.status !== 'filling') throw httpError(409, 'stage is not filling');
    if (st.seats >= st.cap) throw httpError(409, 'stage is full');
    const dup = this.db.prepare(`select id from intents where stage_id = ? and user_id = ? and state not in ('refunded','oversold','expired')`).get(stageId, userId);
    if (dup) throw httpError(409, 'you already have a seat on this stage');
    const amount = st.seat_price_ugx; // the ceiling at the current fill; the rebate as the car fills is paid after departure
    const it = { id: id('i'), stage_id: stageId, user_id: userId, state: 'queued', amount_ugx: amount, tx_ref: `UG-${Date.now().toString(36).toUpperCase()}-${id('').slice(0, 6).toUpperCase()}`, created_at: now(), updated_at: now() };
    this.db.prepare('insert into intents (id, stage_id, user_id, state, amount_ugx, tx_ref, created_at, updated_at) values (?,?,?,?,?,?,?,?)').run(it.id, it.stage_id, it.user_id, it.state, it.amount_ugx, it.tx_ref, it.created_at, it.updated_at);
    return { intent: it, charge: { tx_ref: it.tx_ref, amount: amount, currency: 'UGX', payment_options: 'mobilemoneyuganda' } };
  }

  /* The processor confirmed the charge (verified server-side, or sandbox). Money is held; the stage may fill.
   *
   * `queue()` guards capacity, but a queued intent is not a seat — `decorate()` counts only intents that
   * hold money. So any number of riders could sit at the checkout sheet and every one of them could pay:
   * ten riders funded a four-seat car, and six seats' worth of escrow had no path out. Capacity is now
   * checked where the money lands, in the same transaction as the state change, and money that arrives
   * after the car has filled is recorded and sent straight back rather than kept.
   *
   * The read-then-write it replaces was safe only because node:sqlite is synchronous and single-process.
   * A webhook retry and a client confirm are two writers, which is where that stops being true. */
  hold(intentId, { flwId = null, amount } = {}) {
    this.db.prepare('begin immediate').run();
    let outcome;
    try {
      const it = this.db.prepare('select * from intents where id = ?').get(intentId);
      if (!it) throw httpError(404, 'no such intent');
      if (it.state !== 'queued') { this.db.prepare('commit').run(); return this.intent(intentId); }
      if (amount != null && Number(amount) !== it.amount_ugx) throw httpError(409, 'amount mismatch');
      const seats = this.db.prepare(`select count(*) c from intents where stage_id = ? and state in ('held','manufactured','accepted','departed','settled')`).get(it.stage_id).c;
      const st = this.db.prepare('select cap, status from stages where id = ?').get(it.stage_id);
      if (Number(seats) >= st.cap || st.status !== 'filling') {
        this.ledger.hold(it.id, it.amount_ugx, it.tx_ref);        // the processor did take it
        this.ledger.refund(it.id, it.amount_ugx, it.user_id);      // and it goes straight back
        this.db.prepare(`update intents set state = 'oversold', flw_id = ?, updated_at = ? where id = ? and state = 'queued'`).run(flwId, now(), it.id);
        outcome = 'oversold';
      } else {
        const r = this.db.prepare(`update intents set state = 'held', flw_id = ?, updated_at = ? where id = ? and state = 'queued'`).run(flwId, now(), it.id);
        if (r.changes !== 1) { this.db.prepare('rollback').run(); return this.intent(intentId); }   // lost the race
        this.ledger.hold(it.id, it.amount_ugx, it.tx_ref);
        outcome = 'held';
      }
      this.db.prepare('commit').run();
    } catch (e) { try { this.db.prepare('rollback').run(); } catch {} throw e; }
    if (outcome === 'held') this.maybeManufacture(this.intent(intentId).stage_id);
    return this.intent(intentId);
  }
  intent(intentId) { return this.db.prepare('select * from intents where id = ?').get(intentId); }

  // Full → manufacture the trip and offer it to drivers whose Comfort Map covers the corridor.
  maybeManufacture(stageId) {
    const st = this.get(stageId);
    if (st.seats < st.cap || st.status !== 'filling') return;
    this.db.prepare(`update stages set status = 'full' where id = ?`).run(stageId);
    this.db.prepare(`update intents set state = 'manufactured', updated_at = ? where stage_id = ? and state = 'held'`).run(now(), stageId);
    const r = route(st.route); const cost = poolSeatCost(r, st.cap);
    const drivers = this.db.prepare(`select id, comfort, verification from users where comfort is not null and roles like '%driver%'`).all()
      .filter((u) => { const c = JSON.parse(u.comfort); return (c.corridors || []).includes(st.route) || (!r.inter && !r.entebbe && r.km <= (c.radius || 0)); });
    // ordering: verified first, then acceptance rate (accepted / (accepted+declined)), then recency
    const rate = (uid) => { const a = this.db.prepare(`select sum(status='accepted') a, sum(status='declined') d from offers where driver_id = ?`).get(uid); const n = Number(a.a || 0) + Number(a.d || 0); return n ? Number(a.a || 0) / n : 0.5; };
    drivers.sort((x, y) => (y.verification === 'verified') - (x.verification === 'verified') || rate(y.id) - rate(x.id));
    for (const d of drivers.slice(0, 3)) {
      this.db.prepare('insert into offers (id, stage_id, driver_id, pay_ugx, road_ugx, wage_ugx, status, created_at, expires_at) values (?,?,?,?,?,?,?,?,?)')
        .run(id('o'), stageId, d.id, cost.driverKeeps, Math.round(cost.road), Math.round(cost.wage), 'open', now(), now() + 3 * 60 * 1000);
    }
    return this.get(stageId);
  }

  offersFor(driverId) {
    return this.db.prepare(`select o.*, s.route, s.day, s.win, s.cap, s.pickup, s.status stage_status from offers o join stages s on s.id = o.stage_id where o.driver_id = ? order by o.created_at desc limit 30`).all(driverId)
      .map((o) => { const r = route(o.route); return { ...o, from: r.from, to: r.to, km: r.km }; });
  }

  accept(driverId, offerId) {
    const o = this.db.prepare('select * from offers where id = ? and driver_id = ?').get(offerId, driverId); if (!o) throw httpError(404, 'no such offer');
    const u = this.db.prepare('select * from users where id = ?').get(driverId);
    if (u.verification !== 'verified') throw httpError(403, 'documents must clear before you can accept a funded trip');
    if (o.status !== 'open') throw httpError(409, `offer is ${o.status}`);
    const st = this.get(o.stage_id); if (st.status !== 'full') throw httpError(409, 'stage already taken');
    const c = JSON.parse(u.comfort || '{}');
    this.db.prepare(`update offers set status = 'accepted' where id = ?`).run(offerId);
    this.db.prepare(`update offers set status = 'expired' where stage_id = ? and id != ? and status = 'open'`).run(o.stage_id, offerId);
    this.db.prepare(`update stages set status = 'funded', driver_id = ?, driver_label = ? where id = ?`).run(driverId, `${u.name} · ${c.vehicle || 'car'} · ${c.plate || 'plate pending'}`, o.stage_id);
    this.db.prepare(`update intents set state = 'accepted', updated_at = ? where stage_id = ? and state = 'manufactured'`).run(now(), o.stage_id);
    return this.get(o.stage_id);
  }
  decline(driverId, offerId) { this.db.prepare(`update offers set status = 'declined' where id = ? and driver_id = ? and status = 'open'`).run(offerId, driverId); }

  // Departure confirmed by a rider's device or the driver. Escrow releases to the driver's payable (T+1 hold applies at payout).
  depart(userId, stageId) {
    const st = this.get(stageId); if (!st) throw httpError(404, 'no such stage');
    if (st.status !== 'funded') throw httpError(409, 'stage is not funded');
    const mine = st.driver_id === userId || this.db.prepare(`select id from intents where stage_id = ? and user_id = ? and state = 'accepted'`).get(stageId, userId);
    if (!mine) throw httpError(403, 'only riders on this stage or its driver can confirm departure');
    const r = route(st.route); const cost = poolSeatCost(r, st.cap); const feePerSeat = Math.round(cost.perSeat * 0.10);
    const intents = this.db.prepare(`select * from intents where stage_id = ? and state = 'accepted'`).all(stageId);
    for (const it of intents) {
      this.ledger.release(it.id, it.amount_ugx, st.driver_id, feePerSeat);
      // the ceiling was charged; the difference to the full-car price is a rebate
      const rebate = it.amount_ugx - st.price_when_full_ugx;
      if (rebate > 0) this.ledger.post(`rebate:${it.id}`, 'rebate as the car filled', [{ account: `payable:driver:${st.driver_id}`, debit: rebate }, { account: `payable:refund:${it.user_id}`, credit: rebate }]);
      this.db.prepare(`update intents set state = 'settled', updated_at = ? where id = ?`).run(now(), it.id);
    }
    this.db.prepare(`update stages set status = 'departed', departed_at = ? where id = ?`).run(now(), stageId);
    return this.get(stageId);
  }

  // Cancel before the stage is funded: full refund. After: per policy (50%), never after departure.
  cancel(userId, intentId) {
    const it = this.intent(intentId); if (!it || it.user_id !== userId) throw httpError(404, 'no such intent');
    if (it.state === 'queued') { this.db.prepare(`update intents set state = 'refunded', updated_at = ? where id = ?`).run(now(), it.id); return this.intent(intentId); }
    if (['settled', 'refunded'].includes(it.state)) throw httpError(409, `intent is ${it.state}`);
    const st = this.get(it.stage_id);
    const amount = st.status === 'funded' ? Math.round(it.amount_ugx * 0.5) : it.amount_ugx;
    this.ledger.refund(it.id, it.amount_ugx, it.user_id);
    if (amount !== it.amount_ugx) this.ledger.post(`cancelfee:${it.id}`, 'late cancellation fee', [{ account: `payable:refund:${it.user_id}`, debit: it.amount_ugx - amount }, { account: 'revenue:ug', credit: it.amount_ugx - amount }]);
    this.db.prepare(`update intents set state = 'refunded', updated_at = ? where id = ?`).run(now(), it.id);
    if (st.status === 'full') { this.db.prepare(`update stages set status = 'filling' where id = ?`).run(st.id); this.db.prepare(`update offers set status = 'expired' where stage_id = ? and status = 'open'`).run(st.id); this.db.prepare(`update intents set state = 'held' where stage_id = ? and state = 'manufactured'`).run(st.id); }
    return this.intent(intentId);
  }

  /* Cut-off sweep: a filling stage past its cut-off and below minimum fill refunds everyone. Airport
     stages carry the guarantee, so they go to a human rather than refunding.
     Run it on a timer AND lazily on every stage read, so a cron outage never strands money. */
  sweepCutoffs(at = now()) {
    const dead = this.db.prepare(`
      select s.id, s.guarantee, s.min_fill,
             (select count(*) from intents i where i.stage_id = s.id and i.state in ('held','manufactured')) as funded
        from stages s
       where s.status = 'filling' and s.cutoff_at is not null and s.cutoff_at < ?`).all(at)
      .filter((s) => Number(s.funded) < s.min_fill);
    let refunded = 0;
    for (const s of dead) {
      if (s.guarantee) { this.db.prepare(`update stages set status = 'guarantee_pending' where id = ?`).run(s.id); continue; }
      const its = this.db.prepare(`select * from intents where stage_id = ? and state in ('held','manufactured')`).all(s.id);
      for (const it of its) {
        this.ledger.refund(it.id, it.amount_ugx, it.user_id);
        this.db.prepare(`update intents set state = 'refunded', updated_at = ? where id = ?`).run(at, it.id);
        refunded++;
      }
      this.db.prepare(`update intents set state = 'expired', updated_at = ? where stage_id = ? and state = 'queued'`).run(at, s.id);
      this.db.prepare(`update offers set status = 'expired' where stage_id = ? and status = 'open'`).run(s.id);
      this.db.prepare(`update stages set status = 'expired' where id = ?`).run(s.id);
    }
    return refunded;
  }
}

export function httpError(status, message) { const e = new Error(message); e.status = status; return e; }
