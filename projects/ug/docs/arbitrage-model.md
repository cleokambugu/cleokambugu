# The arbitrage desk: how UG quotes and ranks

Source of truth is the `PROVIDERS`, `ROUTES`, and `FLEET` blocks at the top of the site script
(`projects/ug/site/index.html`) and the JSON exports in `projects/ug/data/`. This document
explains the arithmetic and records where each number came from.

## The formula

For an app-hailed ride (Uber, Bolt, SafeBoda, Faras, Yango, Tinka):

```
fare = max(min_fare, base + per_km × km + per_min × minutes × peak_minute_factor)
fare += entebbe_surcharge            # Uber only: UGX 1,200/km after the 5th km on Entebbe trips (snippet)
fare ×= surge                        # provider's surge multiplier when rush hour or night, ×1.1 more in rain
fare = round_down_500(fare)          # Tinka only (snippet: it advertises this)
fare += tolls                        # cars on the Entebbe expressway: UGX 5,000 (snippet)
vehicles = ceil(passengers / seats)  # 2 on a boda, 4 in a car
quote = fare × vehicles
```

Peak minutes are multiplied by 1.45 because the trip takes longer, not because the tariff
changes. Rush hour is 07:00–10:00 and 17:00–20:00; night is 21:00–05:00. Both are switches on
the compare panel and are set automatically from the booking strip's time field.

Filters that remove a provider from a route:

- bodas are not quoted beyond 60 km;
- hailing apps are not quoted beyond 120 km (drivers rarely accept), special hire is;
- matatus are not quoted to the airport or beyond 300 km;
- buses and UG Rent are quoted only on intercity routes.

For **UG Pool** the price is a cost split, not a tariff:

```
road_cost   = km / km_per_litre × fuel_price + km × 250 (wear) + tolls + ferry
per_seat    = road_cost / seats_filled           # driver counts as a seat
rider_pays  = per_seat × 1.10                    # UG's 10% on the rider share
driver_keeps = per_seat × (seats_filled − 1)     # driver's own seat is their own cost
```

For **UG Rent** on a compare screen: day rate × days (a day per five driving hours) + fuel for
the distance + tolls, on the RAV4.

Ranking is by total price ascending. The split toggle divides every quote by passengers so a
boda for one and a pooled seat for four compare fairly per head.

## Provenance table

| Provider | Base | Per km | Per min | Minimum | Surge | Provenance |
| --- | --- | --- | --- | --- | --- | --- |
| Uber (UberX) | 1,250 | 850 | 130 | 6,000 | 1.35 | *snippet* of Uber Uganda's blog post on January 2020 fare changes. Old. |
| Uber (UberBoda) | 500 | 450 | 70 | 1,500 | 1.25 | *snippet* of Uber Uganda blog. Undated. |
| Bolt car | 1,000 | 800 | 120 | 5,000 | 1.40 | *modelled*; no public tariff found. Commission 15–20% *(snippet)*. |
| Bolt Boda | 500 | 400 | 60 | 1,500 | 1.30 | *modelled*. |
| SafeBoda | 500 | 450 | 60 | 1,500 | 1.20 | base fare *(snippet)*; per km and per minute *modelled*; commission ~15% *(snippet)*. |
| Faras boda | 500 | 400 | 55 | 1,500 | 1.20 | commission 10% *(snippet)*; tariff *modelled*. |
| Faras car | 1,000 | 750 | 110 | 5,000 | 1.30 | *modelled*. |
| Yango | 1,200 | 800 | 120 | 5,500 | 1.40 | *modelled*. |
| Tinka | 1,000 | 700 | 100 | 4,500 | 1.25 | rounding-down and free first 500 m claims *(snippet, Tinka's own comparison pages)*; tariff *modelled*. |
| Street boda | 1,000 | 700 | 0 | 2,000 | 1.30 | *snippet*: UGX 3,000–15,000 for in-town trips; haggle band ±20% *modelled*. |
| Special hire | 3,000 | 1,200 | 0 | 10,000 | 1.20 | *modelled*. |
| Matatu | 1,000 | 150 | 0 | 1,000 | 1.00 | *snippet*: Kampala–Jinja UGX 20,000–30,000 (2026). |
| Intercity bus | per route | | | | 1.00 | *snippet*: 2–3 h trips UGX 20–30k, longer UGX 40–60k (2026). |
| UG Pool | cost split | | | | none | UG model: fuel UGX 6,300/L *(snippet range 6,000–6,600)*, wear UGX 250/km *(modelled)*. |
| UG Rent | 165,000/day | | | | none | *snippet*: self-drive RAV4 about US$45–50/day; converted at UGX 3,700 *(modelled)*. |

Other constants: Entebbe expressway light-vehicle toll UGX 5,000 *(snippet, KEE toll page
summary)*; Uber's Entebbe surcharge *(snippet)*; distances and durations are UG estimates for a
normal day.

## What live accuracy needs

1. **Partner price APIs.** Uber and Bolt expose price-estimate endpoints to approved partners;
   Faras, SafeBoda, Tinka and Yango would need direct agreements.
2. **Crowd sampling.** Riders submit the quote screen from another app for wallet credit; UG
   fits the tariff by regression per provider, per hour, per zone. Two hundred samples a day
   would keep the model within a few hundred shillings.
3. **A published index.** Publish the model weekly. Being wrong in public and correcting fast
   is the trust strategy; hidden numbers are the alternative and nobody believes those.

## Why call it arbitrage

Because the spread is real money: on a 7 km Ntinda to CBD run at rush hour the model spreads
from about UGX 2,000 (matatu) to about UGX 18,000 (surged app car). The rider does not need a
different product to save; they need the spread shown. UG's own products sit in the same list
and win only when they are cheaper.
