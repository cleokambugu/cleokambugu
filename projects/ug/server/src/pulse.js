// Pulse: where paid demand and willing supply are, per town and corridor. Rules now, a model when there are fills.
import { ROUTES, PLACES, route } from './model.js';

export function pulse(db, role = 'rider') {
  const stages = db.prepare(`select s.*, (select count(*) from intents i where i.stage_id = s.id and i.state in ('held','manufactured','accepted')) seats from stages s where s.status in ('filling','full')`).all();
  const drivers = db.prepare(`select comfort from users where comfort is not null and roles like '%driver%'`).all().map((d) => JSON.parse(d.comfort));
  const byTown = {};
  for (const p of PLACES.filter((x) => !x.park)) byTown[p.name] = { town: p.name, lon: p.lon, lat: p.lat, demand_seats: 0, seats_open: 0, drivers_near: 0, stages: 0 };
  for (const s of stages) {
    const r = route(s.route); if (!r) continue;
    const town = r.to.split(' (')[0]; const t = byTown[town] || byTown['Kampala']; if (!t) continue;
    t.demand_seats += Number(s.seats); t.seats_open += Math.max(0, s.cap - Number(s.seats)); t.stages++;
    if (s.status === 'full' && !s.driver_id) t.gap = (t.gap || 0) + 1;
  }
  for (const c of drivers) for (const cid of c.corridors || []) { const r = route(cid); if (!r) continue; const town = r.to.split(' (')[0]; if (byTown[town]) byTown[town].drivers_near++; }
  const rows = Object.values(byTown).map((t) => ({ ...t, gap: t.gap || 0, score: role === 'driver' ? t.gap * 10 + t.demand_seats - t.drivers_near : t.seats_open ? t.demand_seats / (t.seats_open + t.demand_seats) : 0 }));
  return rows.filter((t) => t.stages || t.drivers_near).sort((a, b) => b.score - a.score);
}

export function pulseGeoJSON(db) {
  const rows = pulse(db, 'driver');
  const K = PLACES.find((p) => p.name === 'Kampala');
  return {
    type: 'FeatureCollection',
    features: [
      ...rows.map((t) => ({ type: 'Feature', geometry: { type: 'Point', coordinates: [t.lon, t.lat] }, properties: { town: t.town, demand_seats: t.demand_seats, seats_open: t.seats_open, drivers_near: t.drivers_near, gap: t.gap, stages: t.stages } })),
      ...ROUTES.filter((r) => r.inter || r.entebbe).map((r) => { const p = PLACES.find((x) => r.to.startsWith(x.name)); return p && K ? { type: 'Feature', geometry: { type: 'LineString', coordinates: [[K.lon, K.lat], [p.lon, p.lat]] }, properties: { corridor: r.id, km: r.km } } : null; }).filter(Boolean),
    ],
  };
}
