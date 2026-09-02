# UG — Rent. Pool. Ride. Explore.

A Ugandan mobility and tourism marketplace for people who have places to be and a budget to
respect. UG puts every ride on the Kampala market on one screen (the **arbitrage desk**), pools
road trips so a Prado costs a quarter (**Pool**), rents the car when you need to arrive
(**Rent**), and prices the whole park weekend in one number (**Explore**). Payment is mobile
money through Flutterwave.

Status: **PROTOTYPE**. The site is a working single-file web app with a published fare model.
Nothing here is a live fare, a licensed service, or a production payment integration.

| Path | What it is |
| --- | --- |
| [`site/index.html`](site/index.html) | The full site and interactive prototype. Single file, no build step. Open it in a browser. |
| [`data/`](data/) | The fare model, routes, fleet, and destinations as JSON, with provenance tags. Exported from the site's data block. |
| [`docs/business-plan.md`](docs/business-plan.md) | Market, customer, product, revenue model, unit economics, go-to-market, risks. |
| [`docs/arbitrage-model.md`](docs/arbitrage-model.md) | How the compare engine computes and ranks quotes, and what each number's provenance is. |
| [`docs/brand.md`](docs/brand.md) | Identity: name, voice, palette, type, motion, the four verbs. |
| [`docs/payments-flutterwave.md`](docs/payments-flutterwave.md) | Checkout integration as built, what a production deployment must add. |
| [`docs/roadmap.md`](docs/roadmap.md) | Phases from this prototype to a licensed operation, plus regulatory notes. |
| [`../../notes/mobility-market/`](../../notes/mobility-market/) | Study notes on Sixt, Pool, SafariShare, Tinka, the Antigravity landing page, and Ugandan fares, with first-hand versus secondhand provenance marked. |

## Run it

```
# any static server works; no dependencies
cd projects/ug/site
python3 -m http.server 8080
# open http://localhost:8080
```

The page loads Three.js r128 from cdnjs and three Google Fonts. Without network access the 3D map
hides itself and the type falls back to the system stack; everything else works offline.

## What is real and what is modelled

- **Real, read first-hand:** the Flutterwave v3 inline checkout contract (from
  `Flutterwave/React-v3` on GitHub) and the Antigravity 3D landing-page technique (from
  `Emmancipated/antigravity-landingpage-clone`). Both were cloned and read.
- **Secondhand (search snippets, not verified on the operator's page):** Uber Kampala 2020
  tariff, UberBoda tariff, Faras and SafeBoda commission rates, UWA park fees to June 2026,
  Entebbe expressway toll, 2026 bus fare ranges, 2026 fuel price, rental day rates.
- **Modelled (UG's own assumption):** Bolt, Yango, Tinka and Faras-car tariffs, surge
  multipliers, pool cost split (fuel + UGX 250/km wear, divided by seats, plus 10% UG fee),
  lodge and meal budgets, USD rate of UGX 3,700.

Every quote card on the site carries a tag saying which of these it is. See the arbitrage
model document for the full table.

## Interpretation notes

The brief asked for "flutter wave for a clean finish". This build reads that as **Flutterwave**,
the payments company that holds a Bank of Uganda payment-systems-operator licence and settles
MTN MoMo and Airtel Money. If it meant **Flutter**, Google's UI toolkit, the roadmap covers a
Flutter mobile client as phase 2; the fare model and data files were written to be shared by
both.
