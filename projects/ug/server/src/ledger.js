// Double-entry ledger. Balances are derived from postings, never stored. Every journal balances.
// Accounts (by convention):
//   processor:clearing        money collected by the processor on UG's behalf (asset)
//   escrow:intent:<id>        a rider's seat, held until departure (liability)
//   escrow:booking:<id>       a partner booking, held until done (liability)
//   payable:driver:<userId>   owed to a driver after departure (liability)
//   payable:refund:<userId>   owed back to a rider (liability)
//   revenue:ug                UG's fee (income)
//   payable:partner:<name>    owed to a partner for a concierge booking (liability)
import { now } from './db.js';

export class Ledger {
  constructor(db) { this.db = db; }

  post(ref, memo, lines) {
    const debit = lines.reduce((s, l) => s + (l.debit || 0), 0);
    const credit = lines.reduce((s, l) => s + (l.credit || 0), 0);
    if (debit !== credit) throw new Error(`journal does not balance: ${debit} vs ${credit} (${memo})`);
    if (!lines.length) throw new Error('empty journal');
    const dup = this.db.prepare('select id from journal where ref = ?').get(ref);
    if (dup) return dup.id; // idempotent on ref
    const tx = this.db.prepare('insert into journal (ref, memo, created_at) values (?, ?, ?)').run(ref, memo, now());
    const jid = Number(tx.lastInsertRowid);
    const ins = this.db.prepare('insert into postings (journal_id, account, debit, credit) values (?, ?, ?, ?)');
    for (const l of lines) ins.run(jid, l.account, l.debit || 0, l.credit || 0);
    return jid;
  }

  balance(account) {
    const r = this.db.prepare('select coalesce(sum(credit),0) c, coalesce(sum(debit),0) d from postings where account = ?').get(account);
    return Number(r.c) - Number(r.d); // liabilities and income positive when credited
  }

  journalFor(prefix) {
    return this.db.prepare(`select j.id, j.ref, j.memo, j.created_at, p.account, p.debit, p.credit from journal j join postings p on p.journal_id = j.id where p.account like ? order by j.id`).all(prefix + '%');
  }

  // --- the money movements UG makes ---
  hold(intentId, amount, txRef) {
    return this.post(`hold:${intentId}:${txRef}`, `seat held for intent ${intentId}`, [
      { account: 'processor:clearing', debit: amount },
      { account: `escrow:intent:${intentId}`, credit: amount },
    ]);
  }
  release(intentId, amount, driverId, fee) {
    return this.post(`release:${intentId}`, `seat released to driver ${driverId} after departure`, [
      { account: `escrow:intent:${intentId}`, debit: amount },
      { account: `payable:driver:${driverId}`, credit: amount - fee },
      { account: 'revenue:ug', credit: fee },
    ]);
  }
  refund(intentId, amount, userId) {
    return this.post(`refund:${intentId}`, `seat refunded to rider ${userId}`, [
      { account: `escrow:intent:${intentId}`, debit: amount },
      { account: `payable:refund:${userId}`, credit: amount },
    ]);
  }
  holdBooking(bookingId, amount, txRef) {
    return this.post(`hold:booking:${bookingId}:${txRef}`, `booking held ${bookingId}`, [
      { account: 'processor:clearing', debit: amount },
      { account: `escrow:booking:${bookingId}`, credit: amount },
    ]);
  }
  settleBooking(bookingId, amount, partner, fee) {
    return this.post(`settle:booking:${bookingId}`, `booking settled with ${partner}`, [
      { account: `escrow:booking:${bookingId}`, debit: amount },
      { account: `payable:partner:${partner}`, credit: amount - fee },
      { account: 'revenue:ug', credit: fee },
    ]);
  }
  refundBooking(bookingId, amount, userId) {
    return this.post(`refund:booking:${bookingId}`, `booking refunded`, [
      { account: `escrow:booking:${bookingId}`, debit: amount },
      { account: `payable:refund:${userId}`, credit: amount },
    ]);
  }
  payout(driverId, amount, transferRef) {
    return this.post(`payout:${transferRef}`, `payout to driver ${driverId}`, [
      { account: `payable:driver:${driverId}`, debit: amount },
      { account: 'processor:clearing', credit: amount },
    ]);
  }
}

/* The ledger enforces that every journal balances. That is necessary and it holds — but a ledger can
   balance perfectly while disagreeing with the world, and it did: ten riders funded a four-seat car,
   six seats' worth of escrow was stranded with no path out, and `debits == credits` stayed true the
   whole time. These are the checks that would have caught it. Run them in the test suite, after every
   write in development, and on a timer in production. */
export function assertInvariants(db) {
  const fail = [];
  const s = db.prepare('select coalesce(sum(debit),0) d, coalesce(sum(credit),0) c from postings').get();
  if (Number(s.d) !== Number(s.c)) fail.push(`ledger out of balance: ${s.d} debit vs ${s.c} credit`);

  // a liability that has gone negative means money was released or refunded that was never held
  const neg = db.prepare(`select account, sum(credit) - sum(debit) bal from postings
                           where account like 'escrow:%' or account like 'payable:%'
                           group by account having bal < 0`).all();
  for (const r of neg) fail.push(`negative liability ${r.account}: ${r.bal}`);

  // a stage that is over holds no money: everyone was paid, refunded, or the trip did not happen
  const stuck = db.prepare(`select s.id, s.status, count(i.id) n from stages s join intents i on i.stage_id = s.id
     where s.status in ('departed','expired','cancelled') and i.state in ('held','manufactured','accepted')
     group by s.id`).all();
  for (const r of stuck) fail.push(`escrow stranded on ${r.status} stage ${r.id}: ${r.n} intent(s)`);

  // seats that hold money never exceed the car
  const over = db.prepare(`select s.id, s.cap, count(i.id) seats from stages s join intents i on i.stage_id = s.id
     where i.state in ('held','manufactured','accepted','departed','settled')
     group by s.id having seats > s.cap`).all();
  for (const r of over) fail.push(`oversold stage ${r.id}: ${r.seats} seats in a car of ${r.cap}`);

  if (fail.length) throw new Error('ledger invariants violated:\n  ' + fail.join('\n  '));
  return true;
}

