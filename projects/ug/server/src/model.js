// The shared fare model, read from ../data so the site and the server agree on every number.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const dataDir = process.env.UG_DATA_DIR || join(here, '..', '..', 'data');
const read = (f) => JSON.parse(readFileSync(join(dataDir, f), 'utf8'));

export const ROUTES = read('routes.json').routes;
export const FLEET = read('fleet.json').fleet;
export const PLACES = read('routes.json').places;
const constants = read('providers.json').constants;
export const FUEL_UGX_PER_L = constants.FUEL_UGX_PER_L;
export const DRIVER_WAGE_PER_KM = constants.DRIVER_WAGE_PER_KM || 300;
export const UG_FEE = 0.10;

export const route = (id) => ROUTES.find((r) => r.id === id);
export const minFill = (r) => (r.entebbe ? 2 : 3);
export const capFor = (vehicle) => vehicle === 'Boda' ? 1 : /Noah|Prado|V8|LC |Alphard/.test(vehicle || '') ? 6 : 4;

// One definition, identical to the site's poolSeatCost: riders are paying seats; the driver is never a seat.
export function poolSeatCost(r, riders, car) {
  car = car || FLEET.find((c) => c.id === 'rav4') || FLEET[0];
  const fuel = (r.km / car.kmPerL) * FUEL_UGX_PER_L;
  const wear = r.km * 250;
  const wage = r.km * DRIVER_WAGE_PER_KM;
  const road = fuel + wear + (r.tolls || 0) + (r.ferry || 0);
  const total = road + wage;
  const n = Math.max(1, riders);
  const perSeat = total / n;
  return { total, road, wage, perSeat, riderPays: Math.round(perSeat * (1 + UG_FEE)), driverKeeps: Math.round(total), ugFee: Math.round(perSeat * UG_FEE * n) };
}

export const seatPrice = (stage) => { const r = route(stage.route); return poolSeatCost(r, Math.max(minFill(r), stage.seats || 0)).riderPays; };
export const fullPrice = (stage) => poolSeatCost(route(stage.route), stage.cap).riderPays;
