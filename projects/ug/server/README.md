# UG backend contract (v2 target)

There is no backend in v1; everything runs in the browser with timers standing in for other
people. This directory holds the contract the v2 backend must satisfy, written from the
Virtual Stage design and the panel's ledger, fraud and regulatory findings. `openapi.yaml` is
the API; this file is the shape of the system.

## Services

| Service | Owns | Notes |
| --- | --- | --- |
| **Identity** | phone OTP, device binding, roles, KYC ladder (vouched → documents → payout limit), chairman and circle anchors | Number change triggers a 48-hour payout hold. |
| **Stages** | corridors, windows, cut-offs, pickup points, intents, fill state, manufacture, offers, acceptance, departure confirmation | State machine per intent: `queued → held → manufactured → accepted → departed → settled | refunded`. |
| **Comfort Maps** | base, radius, corridors, days, hours, vehicle, hard no's, driver type (going anyway / for hire), minimum payout | The only thing a driver maintains. |
| **Ledger** | double-entry journal: processor clearing, per-intent escrow, driver payable, UG revenue, refund payable | Balances are derived, never stored and incremented. `tx_ref` is server-generated, idempotent, unique. |
| **Payments** | Flutterwave charge, verify, webhook (`charge.completed`), transfer (payout), refund | Fulfil only after verify; never on the inline callback. Money is held in the processor's balance under its licence until the float question is settled with Bank of Uganda. |
| **Pulse** | demand (paid seats) and supply (comfort maps, drivers near) per town and corridor, per hour; hotspot ranking for drivers and riders; GeoJSON layer for Felt | The AI that points people somewhere without a search. Starts as rules; learns from fills. |
| **Fares** | the published fare model, weekly crowd-sampled index with dates, provenance per figure | Replaces the 2020 tariffs before any marketing of the compare desk. |
| **Plug-ins** | per-user connections and consent per plug-in; server-side keys behind a host allowlist; outbound calls to Felt, Infrared City, Tazama, Cephable, Clarifom | Nothing leaves without the user's switch. Trip context shared with a third party requires consent from every rider on the trip. |
| **Feedback** | spoken and typed feedback (Clarifom), tags, tickets, driver and rider ratings | Ratings feed offer ordering. |

## Non-negotiables from the panel

1. Acceptance of a funded trip requires cleared documents, enforced server-side.
2. Payout after departure confirmation by riders' devices, with a T+1 hold.
3. Refunds go only to the source MSISDN or card; airport-night stages carry the special-hire guarantee.
4. Price locked at payment; the rebate as the car fills is paid after departure.
5. Empty legs go on sale only after the outbound's non-refundable window; cancelling the outbound voids the legs.
6. CSP and SRI on the client; no `innerHTML` with user data; plug-in keys never on the device.
7. PDPO registration, privacy notice, per-plug-in consent, retention schedule; church membership treated as sensitive.

## Stack suggestion

Postgres (ledger and state machines want transactions), a small Node or Go API, a queue for
webhooks and payouts, Flutterwave for collection and transfers, a rules engine for Pulse that
can be replaced by a model once there are fills to learn from. The Flutter mobile client and
the web app share this API and the data files in `../data/`.
