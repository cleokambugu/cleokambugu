import { test } from 'node:test';
import assert from 'node:assert/strict';
import { openDb, id, now } from '../src/db.js';
import { Ledger } from '../src/ledger.js';
import { Stages } from '../src/stages.js';
import { poolSeatCost, route } from '../src/model.js';

function world() {
  const db = openDb(':memory:'); const L = new Ledger(db); const S = new Stages(db, L, { sandbox: true });
  const mk = (name, roles, extra = {}) => { const uid = id('u'); db.prepare('insert into users (id, phone, name, roles, verification, comfort, created_at) values (?,?,?,?,?,?,?)').run(uid, '+2567' + Math.random().toString().slice(2, 10), name, JSON.stringify(roles), extra.verification || 'none', extra.comfort ? JSON.stringify(extra.comfort) : null, now()); return uid; };
  return { db, L, S, mk };
}

test('the stage fills, manufactures a funded offer, and settles to the driver after departure', () => {
  const { db, L, S, mk } = world();
  const riders = [mk('A', ['rider']), mk('B', ['rider']), mk('C', ['rider']), mk('D', ['rider'])];
  const driver = mk('Moses', ['rider', 'driver'], { verification: 'verified', comfort: { corridors: ['kampala-jinja'], radius: 10, vehicle: 'RAV4', plate: 'UBH 123X' } });
  const st = S.create(riders[0], { route: 'kampala-jinja', cap: 4 });
  assert.equal(st.min_fill, 3);
  const r = route('kampala-jinja');
  // the first rider pays the ceiling (priced at minimum fill), not a price for one
  const q1 = S.queue(riders[0], st.id); assert.equal(q1.charge.amount, poolSeatCost(r, 3).riderPays);
  S.hold(q1.intent.id, { flwId: 'x' });
  assert.throws(() => S.queue(riders[0], st.id), /already have a seat/);
  for (const u of riders.slice(1)) { const q = S.queue(u, st.id); S.hold(q.intent.id, { flwId: 'x' }); }
  const full = S.get(st.id); assert.equal(full.status, 'full'); assert.equal(full.seats, 4);
  const offers = S.offersFor(driver); assert.equal(offers.length, 1);
  assert.equal(offers[0].pay_ugx, poolSeatCost(r, 4).driverKeeps);
  const funded = S.accept(driver, offers[0].id); assert.equal(funded.status, 'funded'); assert.match(funded.driver_label, /UBH 123X/);
  const departed = S.depart(riders[1], st.id); assert.equal(departed.status, 'departed');
  const payable = L.balance(`payable:driver:${driver}`);
  const full4 = poolSeatCost(r, 4);
  // driver gets the whole car less UG's fee; riders who paid the 3-seat ceiling get the difference back
  assert.ok(payable > full4.driverKeeps - full4.ugFee - 5 && payable < full4.driverKeeps + 5, `payable ${payable} vs ${full4.driverKeeps}`);
  assert.ok(L.balance(`payable:refund:${riders[0]}`) > 0, 'rebate owed to the early rider');
  const sum = db.prepare('select sum(debit) d, sum(credit) c from postings').get(); assert.equal(Number(sum.d), Number(sum.c));
});

test('an unverified driver cannot accept a funded trip', () => {
  const { S, mk } = world();
  const riders = [mk('A', ['rider']), mk('B', ['rider'])];
  const driver = mk('New', ['driver'], { verification: 'vouched', comfort: { corridors: ['cbd-entebbe'], radius: 10 } });
  const st = S.create(riders[0], { route: 'cbd-entebbe', cap: 2 });
  for (const u of riders) { const q = S.queue(u, st.id); S.hold(q.intent.id); }
  const o = S.offersFor(driver)[0]; assert.ok(o);
  assert.throws(() => S.accept(driver, o.id), /documents must clear/);
});

test('cancelling before funding refunds in full and reopens a full stage', () => {
  const { L, S, mk } = world();
  const riders = [mk('A', ['rider']), mk('B', ['rider'])];
  const st = S.create(riders[0], { route: 'cbd-entebbe', cap: 2 });
  const q = riders.map((u) => S.queue(u, st.id)); q.forEach((x) => S.hold(x.intent.id));
  assert.equal(S.get(st.id).status, 'full');
  S.cancel(riders[1], q[1].intent.id);
  assert.equal(S.get(st.id).status, 'filling');
  assert.equal(L.balance(`payable:refund:${riders[1]}`), q[1].charge.amount);
});
