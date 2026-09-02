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
