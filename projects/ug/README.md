# UG — Ride. Pool. Rent. Deliver.

A Ugandan mobility and tourism marketplace for people who have places to be and a budget to
respect. **Ride. Pool. Rent. Deliver.** is the catchphrase and the order of the product: UG puts every ride on the
Kampala market on one screen (the **arbitrage desk**), pools road trips so a Prado costs a
quarter (**Pool**), rents the car when you need to arrive (**Rent**), and moves the parcel, in the boot of a
stage car if it is going upcountry (**Deliver**). **Explore** prices the
whole park weekend in one number and is where all three verbs get used at once. Payment is mobile
money through Flutterwave.

Status: **v1.2, a working product in sandbox**. The site is a single-file installable web app
and the server behind it is real: accounts by one-time code, the Virtual Stage with intents and
funded offers, a double-entry ledger, bookings on the trip rail, Pulse, Flutterwave verification
and webhooks, tests, a Docker image and deployment workflows. It runs in sandbox until
Flutterwave keys are set. Nothing here is a live fare, a licensed service, or a contract with an
operator; see `docs/deploy.md` and the panel's list before real money moves.

| Path | What it is |
| --- | --- |
| [`site/index.html`](site/index.html) | **v1.** The app shell and the Virtual Stage: two doors, the sixty-second Handshake, paid intents that fill a stage, the driver's Comfort Map and funded-offer feed, empty legs, Pulse, the Tazama dock, voice commands, Me, a bottom tab bar. Single file, no build step. |
| [`site/v0.html`](site/v0.html) | **v0**, frozen (also git tag `ug-v0`). |
| [`site/manifest.webmanifest`](site/manifest.webmanifest) | Web app manifest so the site installs as the app. |
| [`docs/versions.md`](docs/versions.md) | What each version is and where it lives. |
| [`docs/atlas.md`](docs/atlas.md) | The tie-together: one table, one truth about state, one desk, one rail, one formula, one map, one wallet, one crest, one link. |
| [`docs/stay-on-ug.md`](docs/stay-on-ug.md) | Booking with partners without leaving UG: the trip rail now, and the business and API channels each operator offers (researched by search). |
| [`docs/v1-concept.md`](docs/v1-concept.md) | The Virtual Stage: the logistics trick, the four mechanisms, the Handshake. |
| [`docs/stress-test.md`](docs/stress-test.md) | The panel of sharks and maestros: verdicts, what v1 changed, what v2 must do. Full critiques in [`docs/panel/`](docs/panel/). |
| [`server/`](server/) | **The backend.** Node 22, no dependencies, SQLite: `src/` (api, stages, ledger, bookings, pulse, otp, flutterwave), `test/`, a Dockerfile, `.env.example`, `scripts/` (data export, icons). `README.md` there is the system shape; `openapi.yaml` the contract. |
| [`docs/deploy.md`](docs/deploy.md) | Run it locally in two minutes; three ways to put it on the internet; what live and sandbox mean. |
| [`site/sw.js`](site/sw.js), [`site/icons/`](site/icons/), [`site/config.js`](site/config.js) | Service worker for the offline shell, PNG icons from the Crest, the API base override. |
| [`data/`](data/) | The fare model, routes, fleet, and destinations as JSON, with provenance tags. Exported from the site's data block. `uganda-geometry.json` is the border and lakes from Natural Earth 10m, simplified. |
| [`brand/`](brand/) | The Crest mark, wordmark, and app icon as SVG. |
| [`docs/business-plan.md`](docs/business-plan.md) | Market, customer, product, revenue model, unit economics, go-to-market, risks. |
| [`docs/arbitrage-model.md`](docs/arbitrage-model.md) | How the compare engine computes and ranks quotes, and what each number's provenance is. |
| [`docs/brand.md`](docs/brand.md) | Identity: name, voice, palette, type, motion, the catchphrase and the verbs. |
| [`docs/payments-flutterwave.md`](docs/payments-flutterwave.md) | Checkout integration as built, what a production deployment must add. |
| [`docs/integrations.md`](docs/integrations.md) | The plug-in registry: Felt (maps), Infrared City (workflows), Tazama (entertainment), Cephable (automation and hands-free), and what phase 1 must wire. |
| [`docs/roadmap.md`](docs/roadmap.md) | Phases from this prototype to a licensed operation, plus regulatory notes. |
| [`../../notes/mobility-market/`](../../notes/mobility-market/) | Study notes on Sixt, Pool, SafariShare (benchmarked), Tinka, competitor onboarding, the Antigravity landing page, and Ugandan fares, with first-hand versus secondhand provenance marked. |

## Run it

```
cd projects/ug/server
npm run export-data && npm run dev     # sandbox server + site at http://localhost:8787
npm test                               # ledger, stage and API tests
```

The site alone also works from any static server or the Artifact link; without an API it runs
its in-browser sandbox.

The page loads Three.js r128 from cdnjs and three Google Fonts. Without network access the 3D map
hides itself and the type falls back to the system stack; everything else works offline.

## What is real and what is modelled

- **Real, read first-hand:** the Flutterwave v3 inline checkout contract (from
  `Flutterwave/React-v3` on GitHub), the Antigravity 3D landing-page technique (from
  `Emmancipated/antigravity-landingpage-clone`), and Uganda's border and lakes (Natural Earth
  10m from `nvkelso/natural-earth-vector`). All were cloned and read.
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
