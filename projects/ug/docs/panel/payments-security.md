# Payments and security critique: UG v0 and v1

## Escrow and ledger design

(Line numbers refer to `projects/ug/site/v0.html`.)

The docs contradict each other: `payments-flutterwave.md` splits to `subaccounts` at charge time "so UG never holds float", while `v1-concept.md` holds seats until departure and refunds at cut-off. Money already split to a driver cannot be refunded to a rider. Pick one: collect into Flutterwave's balance (the float sits under its PSO licence), release by transfer after departure, refund from that balance at cut-off. Confirm with Bank of Uganda whether "collected and held pending service" counts as e-money issuance under the NPS Act 2020; if so, a licensed partner holds the trust account, not UG.

The backend is a double-entry journal: Flutterwave clearing, per-intent escrow, driver payable, UG revenue, refund payable, wallet liability. Every posting balances; balances are derived, never a stored number that gets `+50000` (line 1158 does exactly that to a DOM string). Intents are a state machine (queued, held, manufactured, accepted, departed, settled/refunded); each transition is a journal entry.

`tx_ref` is server-generated, bound to `intent_id` plus attempt, unique-indexed; a replayed webhook is a no-op. Fulfil only on `charge.completed` after `GET /transactions/{id}/verify`, matching amount, currency and `tx_ref` to the intent, never on the inline `callback`. MoMo approvals arrive after the sheet closes; the doc says so, the code ignores it. Refunds go only to the source MSISDN or card.

## Fraud scenarios

1. **Self-filled stage.** Accomplice SIMs buy seats, the stage "departs", driver collects. Counter: payout only after each rider's device confirms departure (geofence or code shown to driver), T+1 hold, velocity limits per MSISDN/device, minimum account age.
2. **Fill-bar price gaming.** Prices fall as cars fill; sybil intents push the price down, then cancel. Counter: price locked at payment, rebate after departure, cancellation fee once the stage passes a threshold.
3. **Manufactured Empty Legs.** Book an outbound rental with driver, sell the 40% return to friends, cancel the outbound. Counter: legs on sale only after the outbound's non-refundable window; cancelling voids legs and refunds riders.
4. **Vouch collusion.** Two sybil members vouch a driver in; he takes prepaid seats and vanishes. Counter: vouchers must be document-verified with ride history, vouches carry a rating and payout stake, unverified drivers get a value cap.
5. **Stolen-card rental deposit.** Card deposit, car collected, chargeback. Counter: MoMo-only above a threshold, ID plus selfie plus in-app yard handover, holdback until return.
6. **Phantom yard.** Lists a car it does not own, collects deposits. Counter: plate/logbook checks, deposit escrowed until renter confirms handover, payout delay.
7. **SIM swap.** OTP and MoMo share one MSISDN. Counter: device binding, 48-hour payout hold after any number change.

## Client-side findings in v0.html

- **Fail-open payments.** The `catch` at 1207 treats *any* error, including the 4-second script timeout (1183) and `FlutterwaveCheckout` throwing, as "Approved (simulated)" and calls `pay.onDone()`. Behind a slow CDN every seat and wallet top-up succeeds for free.
- The `callback` (1197) fulfils without checking `d.status === 'successful'`.
- **Key check** (1201) accepts `FLWPUBK_TEST` keys, so production can silently run in test mode under a footer reading "Bank of Uganda licensed PSO". No secret key in the client, which is correct.
- `tx_ref` (1169) is `Date.now().toString(36)`: predictable, collides across tabs, unlinked to any order, read back from DOM text. Amount is client-computed. Phone pre-filled with `0772 000 000` (692), so a real charge prompts a stranger.
- **Plug-in keys** sit in plaintext `localStorage` `ug:plug:<id>` (1267), readable by any XSS or shared phone. Any `http://` endpoint passes, including the default `http://127.0.0.1:5178` (1236). The key is never sent anywhere, so the "only to APIs" promise in `integrations.md` has no code behind it.
- **XSS.** The endpoint is interpolated raw into `href="…"` (1252, 1270) and the "Connected ·" text (1250) via `innerHTML`; `https://<img src=x onerror=…>` passes the regex. Self-XSS today, stored XSS once settings sync to accounts. Same for `trips` from `localStorage` (1010) rendered unescaped at 1019–1026; `badges:['Phone verified']` is hard-coded (1049) with no verification.
- All `target="_blank"` links carry `rel="noopener"` (zero misses); none carry `noreferrer`, so third-party endpoints receive the Referer plus the route in the query string.
- No CSP, no SRI on three.js (715) or the injected `v3.js` (1182). A compromised CDN owns the checkout.
- Escape closes the payment modal mid-charge (1176).

## Data protection

The Data Protection and Privacy Act 2019 applies: PDPO registration, a DPO, breach notification. Circles (church, employer) reveal religious affiliation, a special category; permit photos, plates, location and trip patterns are the rest. Minimise what reaches Flutterwave (`meta.label` carries route text), sign a DPA, require per-share consent before any plug-in receives trip context, https-only endpoints, a retention schedule, and pseudonymisation so deletion requests do not break the immutable ledger.

## Recommendations for v2

1. Delete the runtime sandbox fallback; sandbox is a build flag, production refuses to open checkout without a live key.
2. Build the ledger and intent state machine; fulfil only from verified webhooks.
3. Server-generated idempotent `tx_ref`; recompute amounts server-side.
4. Settle the float question with BoU and Flutterwave before holding one prepaid seat.
5. Payout controls: rider departure confirmation, T+1 hold, number-change hold.
6. Replace `innerHTML` with `textContent` or escaping; add CSP and SRI; move plug-in keys server-side behind a host allowlist.
7. KYC ladder tied to value caps: vouch, document check, payout limits.
8. DPPA pack: PDPO registration, Flutterwave DPA, per-plug-in consent, retention policy.
