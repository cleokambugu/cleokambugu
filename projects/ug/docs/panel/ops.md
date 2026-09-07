# UG v1 Virtual Stage: operations critique

## Does the Virtual Stage work operationally

**Liquidity.** business-plan.md models 10,000 MAU × 0.6 seats = 6,000 seats/month, roughly 200/day across every corridor and window. A two-hour Friday Jinja bucket will see three to five intents on a good week. Four-seat cars need three or four intents landing in the *same* window inside the *same* driver's map. Most buckets will not fill; the default state of the board is half-empty fill bars and refunds.

**Cold start is double-sided and costs money.** Riders escrow, no driver accepts, UG refunds. business-plan.md already shows processing at 3.5% of collected value dominating contribution; every failed stage pays MoMo fees twice for zero revenue. Refunds must land in the UG wallet, not back to MoMo, or the failure mode bankrupts the pilot.

**Driver economics are broken.** arbitrage-model.md says `driver_keeps = per_seat × (seats − 1)` with the driver counted as a seat; v0.html's `poolSeatCost` returns `driverKeeps: perSeat`, and `quoteAll` comments "driver excluded". Three different answers, and all three are pure cost recovery. A driver who was not already going to Jinja earns nothing by accepting a "funded" trip. v1-concept.md's "earning within minutes" is false under this formula. The Virtual Stage manufactures trips for drivers who only said where they are *comfortable*; that is a demand-responsive taxi, which needs a wage and (per business-plan.md's own risk list) a PSV licence, not BlaBlaCar cost-sharing.

**Cut-off, no-shows, cancels.** v1-concept.md says "not full at cut-off, top up from the empty-leg pool or refund". The empty-leg pool has no seats in the hour before a manufactured departure. No pickup-point rule exists: a 15 km "radius" with door-to-door pickups turns a 17:30 departure into 18:40. Driver cancel after accept is the worst case: money is escrowed, riders have cancelled other plans, and the offer feed re-runs from zero.

**4 a.m. airport.** Intents for "airport any night" almost never align three-deep. The rider with a 6 a.m. flight gets a 2 a.m. refund and no car. Refunding a flight is a product-killing event; this case cannot use the stage rule at all.

## Matching rules I would write

- **Minimum fill:** 3 rider seats on intercity, 2 on airport; the driver's seat is never counted.
- **Pricing:** quote one ceiling price (road cost ÷ 3 × 1.10 + driver wage). Everyone escrows the ceiling; the fourth seat rebates the difference to every rider's wallet at departure. Never charge early riders more than late ones.
- **Cut-off:** T-90 intercity, T-45 airport. Below minimum at cut-off: riders get a one-tap "pay ceiling for the empty seats" split, else full wallet refund plus the arbitrage desk's cheapest fallback. Airport-night stages carry a UG guarantee: special hire at a published cap, difference budgeted.
- **Driver offer ordering:** comfort-map fit → acceptance rate → rating → distance to the stage at T-60. One driver at a time, three-minute window, then three in parallel. Acceptance only after documents clear; Vouch does not override this for stages.
- **Penalties:** driver cancel inside 12 h of departure forfeits 20% of trip value from future payouts and drops ordering rank; two in 30 days suspends stage offers. Riders: full wallet refund before cut-off, 50% after, zero at departure. One fixed pickup point per stage.

## Comfort Map: what to add and what to drop

**Add:** driver type ("going anyway" vs "for hire", priced differently); minimum payout per trip; preferred pickup points; luggage capacity; response window; a backup-driver flag; verification status shown next to every corridor.

**Drop:** the 15 km in-town radius for pooling. Swvl and Via needed fleets to make in-town pooling work; a private-car stage will not. v1 should be intercity and airport only. Drop "any night" as a corridor value; hours must be explicit.

## Empty Legs: real or fantasy

Real for one case: Entebbe drop-offs, where a driver is back on the expressway within an hour and inbound demand exists. Fantasy for everything else. A pool driver's return is already on their comfort map; a chauffeured three-day rental keeps the driver at the destination; a Jinja special hire returning at 20:00 Friday meets no demand. "40% the moment the outbound is booked" (v1-concept.md) prices a seat at 10% of road cost with an uncertain departure. Ship it for the airport corridor, nothing else.

## Vouch: safety holes

Circles are self-declared; nothing verifies that the two vouchers belong to the employer or church, so two accounts can vouch a driver into a circle with escrowed money in an hour. An unverified driver has no PSV, no third-party insurance, no police report (onboarding.md lists all three). If a crash happens on a vouched trip, UG held the money and chose the driver. Fixes: vouchers stake their rating and a deposit; circles need a verified anchor (employer email domain, chairman account per onboarding.md's SafeBoda lesson); vouched drivers get daytime, in-town, under-50 km trips only, capped at five trips before documents clear.

## Six recommendations for v2

1. Put a driver wage in the formula and reconcile the three `poolSeatCost` definitions; cost-recovery drivers will not accept manufactured trips.
2. Launch on two corridors (Friday Jinja, nightly Entebbe) with ten contracted anchor drivers before opening the offer feed.
3. All refunds and rebates to the wallet; never round-trip MoMo on a failed stage.
4. Airport-night stages carry a guaranteed special-hire fallback, never a refund.
5. Fixed stage pickup points; kill door-to-door and the in-town radius.
6. Vouch limited to verified circles, staked vouchers, daytime short trips, five-trip cap.
