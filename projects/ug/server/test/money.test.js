// Money that arrived after the car filled, and money in a car that never left. Both were measurable
// while `debits == credits` stayed true, which is the point: a balanced ledger can still disagree with
// the world. Each test asserts the invariant, then re-runs assertInvariants over the whole database.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { openDb, now, id } from '../src/db.js';
import { Ledger, assertInvariants } from '../src/ledger.js';
import { Stages } from '../src/stages.js';
import { scheduleTimes, windowStart, cutoffLead, EAT_OFFSET } from '../src/schedule.js';

function world() {
  const db = openDb(':memory:');
  const ledger = new Ledger(db);
  const stages = new Stages(db, ledger, { sandbox: true });
  const rider = (n) => { const uid = id('u'); db.prepare('insert into users (id, phone, name, roles, created_at) values (?,?,?,?,?)').run(uid, '+2567721000' + String(n).padStart(2, '0'), 'R' + n, '["rider"]', now()); return uid; };
  return { db, ledger, stages, rider };
}

test('ten riders cannot fund a four-seat car', async () => {
  const { db, ledger, stages, rider } = world();
  const st = stages.create(rider(0), { route: 'kampala-jinja', cap: 4 });

  const intents = [];
  for (let i = 1; i <= 10; i++) intents.push(stages.queue(rider(i), st.id).intent);   // queueing is free; a queued intent is not a seat
  for (const it of intents) stages.hold(it.id, { flwId: 'sandbox' });                  // every one of them pays

  const held = intents.map((it) => stages.intent(it.id).state);
  assert.equal(held.filter((s) => s === 'held' || s === 'manufactured').length, 4, 'exactly the car');
  assert.equal(held.filter((s) => s === 'oversold').length, 6, 'the rest are oversold, not silently kept');

  // and the six are not merely labelled — the money is on its way back
  for (const it of intents) {
    if (stages.intent(it.id).state !== 'oversold') continue;
    assert.equal(ledger.balance(`escrow:intent:${it.id}`), 0, 'no escrow left on an oversold seat');
    assert.equal(ledger.balance(`payable:refund:${stages.intent(it.id).user_id}`), it.amount_ugx);
  }
  assertInvariants(db);
});

test('a car that never fills gives the money back at its cut-off', async () => {
  const { db, ledger, stages, rider } = world();
  const st = stages.create(rider(0), { route: 'kampala-jinja', cap: 4, day: 'Sat', win: '06:00–08:00', cutoff: 'the evening before' });
  assert.ok(st.cutoff_at, 'the cut-off is a timestamp, not only prose');
  assert.ok(st.cutoff_at < st.depart_by);
  assert.match(st.cutoff_promise, /your money comes back automatically/);

  const a = stages.queue(rider(1), st.id).intent, b = stages.queue(rider(2), st.id).intent;
  stages.hold(a.id, { flwId: 'sandbox' }); stages.hold(b.id, { flwId: 'sandbox' });
  const total = a.amount_ugx + b.amount_ugx;
  assert.equal(ledger.balance(`escrow:intent:${a.id}`) + ledger.balance(`escrow:intent:${b.id}`), total);

  assert.equal(stages.sweepCutoffs(st.cutoff_at - 1), 0, 'nothing sweeps before the cut-off');
  assert.equal(stages.sweepCutoffs(st.cutoff_at + 1), 2, 'both seats refunded after it');

  assert.equal(stages.get(st.id).status, 'expired');
  assert.equal(ledger.balance(`escrow:intent:${a.id}`), 0);
  assert.equal(ledger.balance(`escrow:intent:${b.id}`), 0);
  assert.equal(ledger.balance(`payable:refund:${a.user_id}`), a.amount_ugx);
  assertInvariants(db);
});

test('a stage that reached its minimum is left alone at the cut-off', async () => {
  const { db, stages, rider } = world();
  const st = stages.create(rider(0), { route: 'kampala-jinja', cap: 4 });
  const seats = [];
  for (let i = 1; i <= st.min_fill; i++) { const it = stages.queue(rider(i), st.id).intent; stages.hold(it.id, { flwId: 'sandbox' }); seats.push(it); }
  assert.equal(stages.sweepCutoffs(st.cutoff_at + 1), 0);
  assert.equal(stages.get(st.id).status, 'filling');
  assertInvariants(db);
});

test('assertInvariants catches a refund of money that was never held', () => {
  const db = openDb(':memory:'); const ledger = new Ledger(db);
  ledger.refund('i-never-held', 10000, 'u1');   // balances perfectly, and is nonsense
  const s = db.prepare('select sum(debit) d, sum(credit) c from postings').get();
  assert.equal(Number(s.d), Number(s.c), 'the old check passes');
  assert.throws(() => assertInvariants(db), /negative liability escrow:intent:i-never-held/);
});

test('the cut-off timestamps read the prose the rider was shown', () => {
  assert.equal(windowStart('06:00–08:00'), 360);
  assert.equal(windowStart('7am'), 420);
  assert.equal(windowStart('nonsense'), null);
  assert.equal(cutoffLead('2 hours before'), 2 * 60 * 60 * 1000);
  assert.equal(cutoffLead('45 min before'), 45 * 60 * 1000);
  assert.equal(cutoffLead('the evening before'), null);   // a wall-clock time, not a lead

  // Friday 2026-09-04 09:00 EAT → the Saturday 06:00 slot, cut off at 20:00 Friday
  const from = Date.UTC(2026, 8, 4, 9, 0) - EAT_OFFSET;
  const { depart_by, cutoff_at } = scheduleTimes({ day: 'Sat', win: '06:00–08:00', cutoff: 'the evening before' }, from);
  const eat = (t) => new Date(t + EAT_OFFSET).toISOString().slice(0, 16);
  assert.equal(eat(depart_by), '2026-09-05T06:00');
  assert.equal(eat(cutoff_at), '2026-09-04T20:00');

  // asked on the departure day after the window opens, it means next week, not the past
  const late = scheduleTimes({ day: 'Sat', win: '06:00–08:00', cutoff: '2 hours before' }, Date.UTC(2026, 8, 5, 7, 0) - EAT_OFFSET);
  assert.equal(eat(late.depart_by), '2026-09-12T06:00');
  assert.equal(eat(late.cutoff_at), '2026-09-12T04:00');
});
