// Foresight: predicted demand per day, place and vehicle class from three calendars (seasons, venue rhythms,
// named events) read from ../data/foresight.json (exported from the site so both agree), plus commitments
// from drivers ("I'll be there") so the gap between need and promise is visible. Rules now; a model once
// the ledger holds enough departed stages and completed bookings to learn from.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { now } from './db.js';
import { PLACES } from './model.js';

const here = dirname(fileURLToPath(import.meta.url));
const dataDir = process.env.UG_DATA_DIR || join(here, '..', '..', 'data');
const F = JSON.parse(readFileSync(join(dataDir, 'foresight.json'), 'utf8'));
const perVehicle = { boda: 1.2, car: 3.5, minibus: 14, pickup: 14, lorry: 40, bus: 40 };

export function forecast(db, { days = 7, from = new Date() } = {}) {
  const rows = [];
  for (let d = 0; d < days; d++) {
    const day = new Date(from.getFullYear(), from.getMonth(), from.getDate() + d); const m = day.getMonth() + 1, dow = day.getDay(); const key = day.toISOString().slice(0, 10);
    for (const s of F.seasons) { if (!s.months.includes(m)) continue; const peak = s.months.indexOf(m) === 0 ? 0.8 : 1; for (const t of s.towns) { if (!PLACES.find((p) => p.name === t)) continue; rows.push({ kind: 'season', day: key, town: t, what: `${s.crop} · harvest`, vehicle: s.vehicle, loads: Math.round(s.loadsPerDay * peak / s.towns.length), confidence: 0.6, note: s.note }); } }
    for (const v of F.venues) { if (!v.days.includes(dow)) continue; rows.push({ kind: v.event ? 'event' : 'rhythm', day: key, town: v.town, what: v.name, hours: v.hours, vehicle: v.vehicle, loads: Math.round(v.people / (perVehicle[v.vehicle] || 3.5) / 10), people: v.people, confidence: v.event ? 0.45 : 0.75, note: v.note, lon: v.lon, lat: v.lat }); }
    for (const e of [...F.events, ...dbEvents(db)]) { const span = e.days || 1; const start = new Date(day.getFullYear(), e.month - 1, e.day); const diff = (day - start) / 86400000; if (diff < 0 || diff >= span) continue; rows.push({ kind: 'event', day: key, town: e.town, what: e.name, vehicle: e.vehicle, loads: Math.round(e.people / (perVehicle[e.vehicle] || 3.5) / 50), people: e.people, confidence: e.source === 'partner' ? 0.9 : 0.85, note: e.note }); }
  }
  // supply promised against each (town, vehicle, day)
  const promised = db.prepare(`select town, vehicle, day, count(*) n from commitments where on_ = 1 group by town, vehicle, day`).all();
  for (const r of rows) { const p = promised.find((x) => x.town === r.town && x.vehicle === r.vehicle && x.day === r.day); r.promised = p ? Number(p.n) : 0; r.gap = Math.max(0, r.loads - r.promised); }
  // learning hook: departed stages on a corridor raise confidence for that town
  const departed = db.prepare(`select route, count(*) n from stages where status = 'departed' group by route`).all();
  for (const r of rows) { const town = r.town; const n = departed.filter((x) => x.route.endsWith(town.toLowerCase().replace(/\s+/g, ''))).reduce((s, x) => s + Number(x.n), 0); if (n) r.confidence = Math.min(0.95, r.confidence + 0.02 * n); }
  return rows.sort((a, b) => a.day.localeCompare(b.day) || b.loads - a.loads);
}
function dbEvents(db) { try { return db.prepare('select * from events_calendar').all().map((e) => ({ ...e, source: 'partner' })); } catch { return []; } }

export function ensureForesightTables(db) {
  db.exec(`create table if not exists commitments (user_id text not null, town text not null, vehicle text not null, day text not null, on_ integer not null default 1, at integer not null, primary key (user_id, town, vehicle, day))`);
  db.exec(`create table if not exists events_calendar (id integer primary key autoincrement, name text not null, town text not null, month integer not null, day integer not null, days integer default 1, people integer not null, vehicle text not null, note text, created_by text, at integer not null)`);
}
export function commit(db, userId, { town, vehicle, day, on = true }) {
  if (!PLACES.find((p) => p.name === town)) throw Object.assign(new Error('unknown town'), { status: 400 });
  if (!perVehicle[vehicle]) throw Object.assign(new Error('unknown vehicle class'), { status: 400 });
  db.prepare('insert into commitments (user_id, town, vehicle, day, on_, at) values (?,?,?,?,?,?) on conflict(user_id, town, vehicle, day) do update set on_ = excluded.on_, at = excluded.at').run(userId, town, vehicle, String(day).slice(0, 10), on ? 1 : 0, now());
  return { ok: true };
}
export function addEvent(db, userId, e) {
  if (!PLACES.find((p) => p.name === e.town)) throw Object.assign(new Error('unknown town'), { status: 400 });
  db.prepare('insert into events_calendar (name, town, month, day, days, people, vehicle, note, created_by, at) values (?,?,?,?,?,?,?,?,?,?)').run(String(e.name).slice(0, 80), e.town, Number(e.month), Number(e.day), Number(e.days) || 1, Number(e.people) || 0, perVehicle[e.vehicle] ? e.vehicle : 'car', String(e.note || '').slice(0, 200), userId, now());
  return { ok: true };
}
export function foresightGeoJSON(db) {
  const rows = forecast(db, { days: 2 }); const agg = {};
  for (const r of rows) { const p = PLACES.find((x) => x.name === r.town); if (!p) continue; const a = (agg[r.town] = agg[r.town] || { town: r.town, lon: r.lon || p.lon, lat: r.lat || p.lat, loads: 0, promised: 0, vehicles: {} }); a.loads += r.loads; a.promised += r.promised; a.vehicles[r.vehicle] = (a.vehicles[r.vehicle] || 0) + r.loads; }
  return { type: 'FeatureCollection', features: Object.values(agg).map((a) => ({ type: 'Feature', geometry: { type: 'Point', coordinates: [a.lon, a.lat] }, properties: { town: a.town, loads: a.loads, promised: a.promised, gap: Math.max(0, a.loads - a.promised), vehicles: a.vehicles } })) };
}
