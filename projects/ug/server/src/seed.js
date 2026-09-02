// Demo seed (UG_DEMO_SEED=1): a few riders and drivers and six filling stages, so the loop can be felt on day one.
import { id, now } from './db.js';

export function seed({ db, stages }) {
  if (db.prepare('select count(*) c from stages').get().c > 0) return;
  const mk = (name, phone, roles, extra = {}) => { const uid = id('u'); db.prepare('insert into users (id, phone, name, roles, verification, comfort, created_at) values (?,?,?,?,?,?,?)').run(uid, phone, name, JSON.stringify(roles), extra.verification || 'none', extra.comfort ? JSON.stringify(extra.comfort) : null, now()); return uid; };
  const riders = [mk('Brenda K.', '+256772000001', ['rider']), mk('Ivan T.', '+256772000002', ['rider']), mk('Aisha N.', '+256772000003', ['rider']), mk('Denis O.', '+256772000004', ['rider']), mk('Patience M.', '+256772000005', ['rider']), mk('Samuel N.', '+256772000006', ['rider'])];
  mk('Moses K.', '+256772000010', ['rider', 'driver'], { verification: 'verified', comfort: { base: 'Ntinda', radius: 15, corridors: ['kampala-jinja', 'cbd-entebbe', 'kampala-mbarara'], days: ['Fri', 'Sat', 'Sun'], hours: ['Mornings', 'Evenings'], vehicle: 'RAV4', plate: 'UBH 123X', nos: [] } });
  mk('Grace N.', '+256772000011', ['rider', 'driver'], { verification: 'verified', comfort: { base: 'Bugolobi', radius: 20, corridors: ['cbd-entebbe', 'kampala-gulu', 'kampala-murchison'], days: ['Sat', 'Sun'], hours: ['Nights', 'Mornings'], vehicle: 'Noah', plate: 'UBG 447L', nos: [] } });
  const seedStage = (route, day, win, cutoff, pickup, cap, filled, circles) => {
    const st = stages.create(riders[0], { route, day, win, cutoff, pickup, cap, circles });
    riders.slice(0, filled).forEach((uid) => { const { intent } = stages.queue(uid, st.id); stages.hold(intent.id, { flwId: 'seed' }); });
    return st;
  };
  seedStage('kampala-jinja', 'Fri', '17:00–19:00', 'Fri 15:30', 'Total Ntinda, 17:15', 4, 3, ['Stanbic circle']);
  seedStage('cbd-entebbe', 'Sun', '03:00–04:00', 'Sat 22:00', 'Shell Bugolobi, 03:00', 6, 5, ['Airport regulars']);
  seedStage('kampala-mbarara', 'Sat', '05:30–07:00', 'Fri 20:00', 'Shoprite Lubowa, 05:45', 6, 2, ['MUBS alumni']);
  seedStage('ntinda-cbd', 'Weekdays', '07:30', 'daily 06:30', 'Ntinda Shopping Centre, 07:25', 4, 4, ['Ntinda school run']);
  seedStage('kampala-murchison', 'Fri', '13:00', 'Thu 18:00', 'Acacia Mall, 13:00', 5, 1, ['Watoto circle']);
  seedStage('kampala-gulu', 'Sat', '06:00', 'Fri 20:00', 'Kalerwe stage, 06:00', 6, 4, ['Ministry of Health']);
}
