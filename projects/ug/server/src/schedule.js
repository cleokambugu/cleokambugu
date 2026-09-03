/* When a stage actually leaves, and when it stops waiting.
 *
 * A stage was created with prose — day "Sat", window "06:00–08:00", cutoff "the evening before" — and
 * `sweepCutoffs()` was a stub returning 0 because there was nothing to compare against. So a car that
 * never filled held its riders' money for good. Prose is what a person should read; a timestamp is what
 * the sweep needs. Both, from the same fields.
 *
 * Uganda keeps one clock all year: EAT, UTC+3, no daylight saving. So the offset is a constant, not a
 * timezone database.
 */
export const EAT_OFFSET = 3 * 60 * 60 * 1000;
const DAYS = { sun: 0, mon: 1, tue: 2, wed: 3, thu: 4, fri: 5, sat: 6 };
const DAY = 24 * 60 * 60 * 1000;

/* Minutes past midnight for the start of a window like "06:00–08:00" or "6am". Null if unreadable. */
export function windowStart(win) {
  const s = String(win || '');
  let m = s.match(/(\d{1,2})[:.](\d{2})/);
  if (m) return Number(m[1]) * 60 + Number(m[2]);
  m = s.match(/(\d{1,2})\s*(am|pm)/i);
  if (m) { const h = Number(m[1]) % 12; return (h + (/pm/i.test(m[2]) ? 12 : 0)) * 60; }
  return null;
}

/* How long before departure the stage stops accepting seats, in ms. The prose is read where it is
   readable and otherwise falls back to ninety minutes, which is the number the old signature carried. */
export function cutoffLead(cutoff, fallbackMs = 90 * 60 * 1000) {
  const s = String(cutoff || '').toLowerCase();
  let m = s.match(/(\d+)\s*(hour|hr)/); if (m) return Number(m[1]) * 60 * 60 * 1000;
  m = s.match(/(\d+)\s*(min)/); if (m) return Number(m[1]) * 60 * 1000;
  if (/(day|night|evening) before/.test(s)) return null;   // handled as a wall-clock time, not a lead
  if (/^noon|midday/.test(s)) return null;
  return fallbackMs;
}

/* depart_by: the next occurrence of the stage's day at the start of its window, in EAT.
   cutoff_at:  the lead applied, or 20:00 EAT the evening before where the prose says so. */
export function scheduleTimes({ day, win, cutoff }, from = Date.now()) {
  const wd = DAYS[String(day || '').slice(0, 3).toLowerCase()];
  const mins = windowStart(win);
  if (wd == null || mins == null) return { depart_by: null, cutoff_at: null };
  // work in EAT wall-clock by shifting the epoch, so getUTC* reads as local Kampala time
  const local = new Date(from + EAT_OFFSET);
  const midnight = Date.UTC(local.getUTCFullYear(), local.getUTCMonth(), local.getUTCDate());
  let departLocal = midnight + ((wd - local.getUTCDay() + 7) % 7) * DAY + mins * 60 * 1000;
  if (departLocal <= from + EAT_OFFSET) departLocal += 7 * DAY;    // today's slot has gone; take next week's
  const depart_by = departLocal - EAT_OFFSET;
  const lead = cutoffLead(cutoff);
  const s = String(cutoff || '').toLowerCase();
  let cutoff_at;
  if (lead != null) cutoff_at = depart_by - lead;
  else if (/(day|night|evening) before/.test(s)) cutoff_at = (departLocal - departLocal % DAY) - DAY + 20 * 60 * 60 * 1000 - EAT_OFFSET;
  else cutoff_at = (departLocal - departLocal % DAY) + 12 * 60 * 60 * 1000 - EAT_OFFSET;  // noon
  return { depart_by, cutoff_at: Math.min(cutoff_at, depart_by) };
}

/* What to tell a rider before they pay. The deadline is the product, not a footnote. */
export function cutoffSentence(cutoff_at) {
  if (!cutoff_at) return null;
  const d = new Date(cutoff_at + EAT_OFFSET);
  const day = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][d.getUTCDay()];
  const hh = String(d.getUTCHours()).padStart(2, '0'), mm = String(d.getUTCMinutes()).padStart(2, '0');
  return `If this car has not filled by ${day} ${hh}:${mm}, your money comes back automatically.`;
}
