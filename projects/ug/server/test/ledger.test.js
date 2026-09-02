import { test } from 'node:test';
import assert from 'node:assert/strict';
import { openDb } from '../src/db.js';
import { Ledger } from '../src/ledger.js';

test('a journal must balance and is idempotent on its ref', () => {
  const db = openDb(':memory:'); const L = new Ledger(db);
  assert.throws(() => L.post('x', 'bad', [{ account: 'a', debit: 10 }, { account: 'b', credit: 5 }]), /does not balance/);
  const j1 = L.hold('i1', 25000, 'TX1'); const j2 = L.hold('i1', 25000, 'TX1');
  assert.equal(j1, j2);
  assert.equal(L.balance('escrow:intent:i1'), 25000);
  assert.equal(L.balance('processor:clearing'), -25000);
});

test('hold, release and rebate leave every account consistent', () => {
  const db = openDb(':memory:'); const L = new Ledger(db);
  L.hold('i1', 26000, 'TX1'); L.release('i1', 26000, 'drv', 2400);
  assert.equal(L.balance('escrow:intent:i1'), 0);
  assert.equal(L.balance('payable:driver:drv'), 23600);
  assert.equal(L.balance('revenue:ug'), 2400);
  L.refund('i2', 0 + 10000, 'rider'); // refund of an unrelated hold
  const sum = db.prepare('select sum(debit) d, sum(credit) c from postings').get();
  assert.equal(Number(sum.d), Number(sum.c));
});
