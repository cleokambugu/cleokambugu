# Legal stress-test: UG v1

*Basis: I read the six documents named. Where I say "the docs claim", that is their content; where I say "general knowledge", that is my own understanding of Ugandan practice, unverified against current instruments. I cite no section numbers.*

## Licensing exposure

**General knowledge:** carrying passengers for hire or reward in Uganda requires a PSV-licensed vehicle and an appropriately licensed driver under the Traffic and Road Safety Act regime administered by the Transport Licensing Board. Genuine cost-sharing (the driver was going anyway, passengers split fuel) is the only arguable exemption, and it is untested here.

**The docs undercut their own defence.** `business-plan.md` §8 calls private-driver pooling a "grey zone" to clear with MoWT "before launch". But `v1-concept.md` describes UG *manufacturing* trips, setting the seat price, collecting the fare, topping cars up from an "empty-leg pool", and offering a driver "UGX 84,000 waiting for a Jinja run". The driver never had a trip; UG dispatched one. That is a for-hire service with UG as the operator in substance, and the "10% of the rider share" makes UG a commission-taking intermediary. Empty Legs (return seats at 40%) sells PSV seats on rental cars. "Airport any night" runs are special-hire work, itself a licensed category. Expect KCCA interest too: anything branded a "Stage" inside the city will be read as one.

**Rental brokerage:** brokering for licensed yards (§8) is the right shape. But the Handshake's "I have a car to rent out" chip is peer-to-peer rental by private owners, contradicting §8. Private motor policies generally exclude hire; chauffeured owner rentals are PSV again.

## Money and data

**Float.** The docs say twice that UG "must not hold customer float", then the revenue model books "deposit float", Hustle Mode holds "money in the UG wallet", and the checkout sells "wallet top-up". General knowledge: stored value and holding customer funds are Bank of Uganda-licensed activities under the National Payment Systems framework; Flutterwave's licence covers Flutterwave, not a merchant sitting on it. Escrow to departure *is* holding funds; `subaccounts` split at charge time does not solve a delayed payout. Refunds at cut-off need a written policy, timelines, and a plan for unclaimed MoMo refunds.

**KYC.** Driver payouts need identity; the docs' URA e-tax plate lookup "where permitted" is probably not permitted.

**Data (DPPA 2019, general knowledge).** Register with the Personal Data Protection Office; give a privacy notice; collect for a stated purpose. Comfort Maps are movement profiles; Circles disclose employer and *church*, which is religious data and sensitive. The plug-in rules (off by default, links only) are sound, but a trip carries other riders' data, who did not consent to Felt or Tazama. Cross-border transfer applies. Cephable automations that move money need explicit payment authorisation. The "anonymised fare index" must be genuinely anonymised before sale.

## Vouch before verification: allowed or reckless

The docs contradict themselves: the mechanisms table says two vouches make a driver "bookable inside a circle" before the document check; the narrative says offers can only be *accepted* after verification. Pick the second. A vouch cannot substitute for a permit, registration, insurance or the vehicle's fitness. If an unverified driver crashes with paid passengers, the insurer voids cover and UG, having collected the fare and kept 10%, is the deepest pocket. As a *discoverability* signal, Vouch is fine and clever (SafeBoda's chairman check, digitised). As a gate for paid carriage it is reckless.

## Consumer protection on the compare screen

General knowledge: Uganda lacks a mature standalone consumer-protection statute (verify current status); misrepresentation, the Contracts Act and electronic-transactions rules still bite. The docs admit the engine uses a 2020 Uber tariff and modelled values. Showing that as "Uber's price" is misleading. Label every card "UG estimate, sampled [date]", show ranges, flag surge. Names in plain text as nominative reference are defensible; competitors' stylised marks and logos are trademark use without licence. Disclose that some links pay referrals if ranking claims to be by price. Crowd-sourced screenshots contain third-party personal data.

## What must be true before the first shilling moves

1. Written MoWT/TLB position, or launch only with PSV-licensed vehicles and drivers.
2. Payment structure with no UG-held funds: split-at-charge or a licensed escrow partner; wallet and "deposit float" removed.
3. Incorporated entity, trading licence, URA registration, VAT treatment of commission.
4. Passenger liability cover bound per seat.
5. Document verification enforced server-side before acceptance.
6. PDPO registration, privacy notice, consent per plug-in, retention policy.
7. Terms: UG as intermediary, cancellation and refund rules, dispute process.
8. Compare cards relabelled as estimates; no logos.
9. Server-side verification and webhooks (already listed in `payments-flutterwave.md`).

## Recommendations for v2 (ranked)

1. Launch Pool with licensed special-hire/tour operators only; keep the Comfort Map.
2. Delete the wallet; escrow via a licensed partner or not at all.
3. Vouch gates visibility, never payment.
4. Drop "church" from Circles or treat it as sensitive data with explicit consent.
5. Broker yards only; defer peer-to-peer owner rentals until insurance exists.
6. Rebuild the compare screen around dated estimates and plain-text names.
