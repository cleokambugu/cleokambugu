// SQLite through node:sqlite (Node 22.13+). One file, WAL mode, migrations in order.
import { DatabaseSync } from 'node:sqlite';
import { mkdirSync } from 'node:fs';
import { dirname } from 'node:path';

const SCHEMA = [
`create table if not exists users (
  id text primary key, phone text unique not null, name text, roles text not null default '["rider"]',
  verification text not null default 'none', vouches integer not null default 0, agent integer not null default 0,
  rider text, owner text, comfort text, documents text, payout_limit_ugx integer not null default 200000,
  created_at integer not null, number_changed_at integer
)`,
`create table if not exists sessions (token text primary key, user_id text not null, device text, created_at integer not null)`,
`create table if not exists otps (phone text primary key, code text not null, expires_at integer not null, attempts integer not null default 0)`,
`create table if not exists vouches (voucher_id text not null, driver_id text not null, circle text, created_at integer not null, primary key (voucher_id, driver_id))`,
`create table if not exists stages (
  id text primary key, route text not null, day text not null, win text not null, cutoff text not null, pickup text,
  cap integer not null, min_fill integer not null, guarantee integer not null default 0, status text not null default 'filling',
  driver_id text, driver_label text, created_by text, created_at integer not null, departed_at integer, circles text
)`,
`create table if not exists intents (
  id text primary key, stage_id text not null, user_id text not null, state text not null default 'queued',
  amount_ugx integer not null, tx_ref text unique not null, flw_id text, created_at integer not null, updated_at integer not null
)`,
`create table if not exists offers (
  id text primary key, stage_id text not null, driver_id text not null, pay_ugx integer not null, road_ugx integer not null, wage_ugx integer not null,
  status text not null default 'open', created_at integer not null, expires_at integer not null
)`,
`create table if not exists journal (id integer primary key autoincrement, ref text not null, memo text, created_at integer not null)`,
`create table if not exists postings (journal_id integer not null, account text not null, debit integer not null default 0, credit integer not null default 0)`,
`create index if not exists postings_account on postings(account)`,
`create table if not exists bookings (
  id text primary key, user_id text not null, kind text not null, partner text not null, partner_sub text, colour text, title text not null,
  price_ugx integer not null, eta_min integer, driver text, plate text, step integer not null default 0, status text not null default 'active',
  tx_ref text, created_at integer not null, updated_at integer not null
)`,
`create table if not exists fare_samples (id integer primary key autoincrement, user_id text, route text not null, provider text not null, paid_ugx integer not null, at integer not null)`,
`create table if not exists feedback (id integer primary key autoincrement, user_id text, booking_id text, text text, tags text, rating integer, at integer not null)`,
`create table if not exists plugins (user_id text not null, plugin text not null, endpoint text, consent integer not null default 0, connected_at integer not null, primary key (user_id, plugin))`,
`create table if not exists events (id integer primary key autoincrement, kind text not null, ref text, payload text, at integer not null)`,
`create table if not exists commitments (user_id text not null, town text not null, vehicle text not null, day text not null, on_ integer not null default 1, at integer not null, primary key (user_id, town, vehicle, day))`,
`create table if not exists events_calendar (id integer primary key autoincrement, name text not null, town text not null, month integer not null, day integer not null, days integer default 1, people integer not null, vehicle text not null, note text, created_by text, at integer not null)`,
];

export function openDb(path = process.env.UG_DB || './data/ug.sqlite') {
  if (path !== ':memory:') mkdirSync(dirname(path), { recursive: true });
  const db = new DatabaseSync(path);
  db.exec('pragma journal_mode = wal; pragma foreign_keys = on;');
  for (const s of SCHEMA) db.exec(s);
  try { db.exec('alter table users add column lang text'); } catch {}
  return db;
}

export const now = () => Date.now();
export const id = (p = '') => p + Math.random().toString(36).slice(2, 10) + Date.now().toString(36).slice(-4);
