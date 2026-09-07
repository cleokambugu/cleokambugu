# Roadmap

## Phase 0 — this prototype (done)

- Single-file site with Ride (the arbitrage desk), Pool, Rent, Explore, Hustle
  Mode, UG Plus, and a Flutterwave checkout with a sandbox fallback.
- Published fare model with provenance on every card.
- Interactive 3D particle map of Uganda as the hero.

## v1 — the Virtual Stage (done, this prototype)

- Two doors, the Handshake, stages with fill bars and cut-offs, Comfort Map and funded offers,
  empty legs, Pulse, the Tazama dock, voice commands, Felt export, Me, tab bar, manifest.
- The panel's quick wins: driver wage in the formula, verified-only acceptance, honest
  provenance and sandbox, fixed pickup points, the airport guarantee, escaping and referrer
  hygiene.

## v2 — the backend and the licence (what the panel says must exist before a shilling moves)

Ranked by how many seats asked for it; details in `stress-test.md`, contract in `../server/`.

1. Ledger and intent state machine; server-generated `tx_ref`; webhook-first fulfilment;
   T+1 payout hold; departure confirmation.
2. Regulatory gate: MoWT/TLB written position, per-seat insurance, PDPO registration, entity
   and URA; the float question settled with Bank of Uganda and Flutterwave.
3. Two launch corridors with contracted anchor drivers: nightly Entebbe, Saturday-morning Jinja.
4. Mobile diet: static map on phones, fonts cut, intro off, Three.js only on desktop with hover.
5. Four-tab shell with a driver switch; Hustle, plans and plug-ins behind Me.
6. Documents at the first funded offer; the Handshake becomes phone plus OTP.
7. Weekly crowd-sampled fare index with dates; plain-text competitor names in production.
8. Chairman vouch accounts with a cut per rider signed; circles with a verified anchor.
9. Charge at seating for a rider's first trip; escrow from the second.
10. Sensitive-data handling for circles; per-plug-in consent from every rider on a trip.

## Phase 1 — trust before supply (8–10 weeks)

- Backend: accounts (phone OTP), trips, seats, bookings, wallet ledger, Flutterwave verify and
  webhooks, split payouts.
- Verification: plates (URA e-tax lookup where permitted), driving permit photo, employer or
  circle attestations.
- Crowd sampling of live fares for the compare engine; publish the weekly index.
- Legal: Ministry of Works and Transport position on cost-sharing pools; partner terms with
  two licensed rental yards; an insurer for per-seat cover.
- Launch routes: Kampala–Jinja (Fri/Sun), Kampala–Entebbe airport (hourly), Kampala–Mbarara
  (Sat/Sun).

## Phase 2 — the phone (parallel, 10–12 weeks)

- Flutter mobile client (Android first; iOS second) sharing the fare model and data files.
  Deep links into Uber, Bolt, SafeBoda, Faras, Yango, Tinka with pick-up and drop-off.
- Hustle Mode with calendar import and the day-chain quote.
- USSD fallback for booking a seat without data.

## Phase 3 — tourism (after the first 1,000 pooled trips)

- Explore bookings with lodges and activity operators; UWA permit purchase through an
  authorised agent.
- Group weekends as a product: a pool and a lodge on one deposit.
- Corporate and family accounts; the Executive plan's statements.

## Phase 4 — the index as a business

- Sell the anonymised fare index to fleets, insurers, and the regulator.
- Open the compare engine to third parties by API.

## Regulatory and operating notes (snippet-level, to be verified with counsel)

- Boda operators need a Class M permit and an annual PSV licence from the Transport Licensing
  Board; KCCA runs boda-free zones downtown.
- Kampala's leadership has said all bodas should operate under digital platforms; the shape of
  the resulting regulation is what UG must track.
- Ride-hailing companies are licensed; UG as a comparison and pooling platform should get a
  written view on whether it needs the same licence.
- Flutterwave holds a Bank of Uganda PSO licence; UG must not hold customer float.
- UWA tariffs run in multi-year books (the last summary seen was valid to 30 June 2026); confirm
  the current book before charging anyone for a permit.
