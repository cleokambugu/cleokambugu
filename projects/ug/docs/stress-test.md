# The panel: sharks and maestros on UG

Six critics, each briefed as a persona and given the v0 site, the docs and the v1 concept, wrote
independent critiques on 2 September 2026. The full texts are in
[`panel/`](panel/). This document is the synthesis: where they agree, where they disagree, what
v1 changed because of them, and what is deferred to v2 with a reason.

The panel:

| Seat | Persona | Verdict in one line |
| --- | --- | --- |
| Shark | Africa-mobility investor | "Not on this plan." A small cheque for one corridor for 90 days; the Virtual Stage is the company, the compare desk is not. |
| Ops maestro | Ran pooling and carpool operations in East Africa | The stage works only intercity and airport, with a driver wage in the formula and fixed pickup points; most buckets will not fill at 10,000 MAU. |
| Lawyer | Ugandan transport, payments and data | UG as designed is the operator of a for-hire service; the wallet and escrow are stored value; Vouch must never gate payment. |
| UX maestro | Consumer apps for mobile-money markets | A megabyte before a price; the product is a screen and a half down on a phone; four tabs, phone plus OTP, documents at the first funded offer. |
| Payments and security | Escrow ledgers and marketplace fraud | The v0 checkout fails open; the ledger must be double-entry and webhook-first; seven fraud scenarios. |
| The street | A boda stage chairman and a Ntinda mother | "A cost-share and a wage are not the same thing." "Nobody pre-pays a stranger." Kill "dignity" and "Boujee"; make the chairman a vouch account. |

## Where all six agree

1. **The driver must earn.** Every critic found the v0 cost-split (driver recovers fuel and wear,
   nothing more) incompatible with a stage that manufactures trips. **Changed in v1:** one
   formula everywhere; a driver wage of UGX 300 per km is inside the seat price; the driver is
   never counted as a seat; offers show fuel-and-wear and wage separately, in shillings.
2. **Vouch gates visibility, never payment.** **Changed in v1:** two vouches make a driver
   visible inside a circle; only the document check lets them accept a funded trip.
3. **Provenance has to be readable, not a tooltip.** **Changed in v1:** every quote says
   "estimate from a published rate" or "UG estimate, unverified" in words on the card;
   "Best price" became "Likely cheapest" on modelled figures.
4. **The sandbox must not look like money.** **Changed in v1:** the checkout no longer treats a
   script failure as a successful payment; sandbox runs only when no key is configured; the
   footer no longer claims a licence; the wallet says "sandbox balance"; a prototype banner
   sits under the hero; phone and email are no longer pre-filled with a stranger's number.
5. **The compare desk is not a business, and it can mislead.** Kept in v1 as the shareable,
   honest utility it is; the shark, lawyer and mother all want dated, crowd-sampled figures
   before it is marketed. **Deferred to v2:** the weekly sampled index, plain-text names
   instead of stylised marks in production.
6. **Too much surface.** Hustle Mode, UG Plus, plug-ins and partners are pitch material in the
   customer path. **Changed in v1:** the phone gets a five-tab bar (Stage, Ride, Rent, Explore,
   Me) and the nav drops Partners. **Deferred to v2:** moving Hustle, plans and plug-ins behind
   Me.

## Where they disagree, and the call made

- **Escrow.** The ops maestro wants refunds to a wallet to avoid paying MoMo fees twice; the
  lawyer wants no wallet at all because stored value is a licensed activity; the payments
  maestro wants funds held in Flutterwave's balance under its licence and released by transfer.
  **Call:** the payments design (collect into the processor's balance, release after departure,
  refund from that balance) is the v2 architecture; the wallet stays in the prototype labelled
  as sandbox and is removed from the business plan's revenue lines.
- **The positioning line.** The street panel says "Look the part. Pay the smart price." and
  "Boujee" insult the customer; the founder chose the positioning deliberately for a market
  that is "trying to look bourgeois while making ends meet". **Call:** the founder's line stays;
  the copy the panel flagged as sneering ("dignity", "awkward cash", "kwanjula grade", the
  "lounge-style waiting room") was cut. Plan names are the founder's decision and are listed
  under v2 questions.
- **In-town pooling.** Ops says drop the radius; the concept keeps Ntinda–CBD as the daily
  habit. **Call:** kept in the prototype as a fixed-pickup daily stage; the launch plan in
  `roadmap.md` opens intercity and airport first.
- **Church as a circle.** The lawyer flags religious affiliation as sensitive data; the chairman
  and mother say circles are the only reason to trust a stranger. **Call:** circles stay;
  v2 must treat church membership as sensitive with explicit consent, and add the stage
  chairman as a first-class vouch account.

## What v1 changed because of the panel

| Change | Who asked |
| --- | --- |
| Driver wage in the formula; one `poolSeatCost`; fee shown in shillings | Shark, ops, chairman |
| Minimum fill (3 intercity, 2 airport); ceiling price; fixed pickup points; airport guarantee | Ops, mother |
| Accept requires documents; vouches only unlock circle visibility | Lawyer, ops, payments |
| Checkout no longer fails open; status checked; no licence claim; no pre-filled identities | Payments, UX |
| Provenance in words on every card; "Likely cheapest" | UX, shark, mother |
| Prototype banner; sandbox wallet label | UX |
| Escaping of user-entered strings in the DOM; `noreferrer` on outbound links; stricter endpoint check | Payments |
| Render loop pauses when the map is off-screen | UX |
| Copy cuts | Street |

## Deferred to v2, with the reason

See `roadmap.md`. The short list, ranked by how many seats asked for it:

1. Backend: double-entry ledger, intent state machine, server-generated `tx_ref`, webhook-first
   fulfilment, T+1 payout hold, departure confirmation. *(No backend exists; nothing else is
   real until this is.)*
2. Regulatory gate: MoWT/TLB written position, per-seat insurance quote, PDPO registration,
   entity and URA. *(Lawyer's checklist; the shark's condition.)*
3. One or two launch corridors with contracted anchor drivers: nightly Entebbe, Friday Jinja.
   *(Shark and ops both; the mother says Friday 17:30 to Jinja is wrong and it should be
   Saturday morning.)*
4. Mobile diet: static map on phones, fonts cut, intro delays off, Three.js only on desktop
   with hover. *(UX.)*
5. Four-tab shell with a driver switch; Hustle, plans and plug-ins behind Me. *(UX, street.)*
6. Documents at the first funded offer, not in the Handshake; phone plus OTP only. *(UX.)*
7. Crowd-sampled weekly fare index with dates; plain-text competitor names in production. *(Shark,
   lawyer, mother.)*
8. Chairman vouch accounts with a cut per rider signed. *(Chairman.)*
9. Charge at seating for the first trip; escrow from the second. *(UX, mother.)*
10. Sensitive-data handling for circles; per-plug-in consent; retention policy. *(Lawyer,
    payments.)*

## Questions only the founder can answer

- The kill question from the shark: at what per-seat price does the Jinja car beat the
  UGX 25,000 matatu and pay the driver more than Bolt would that evening, and does that price
  survive the cost-sharing legal position? (v1's formula gives about UGX 26,000 a seat with four
  riders and a UGX 24,000 wage on top of road cost; the answer is "comfort and time, not price".)
- Do "Boujee" and "Look the part" stay? The street says they sting; the brief says they are the
  market.
- Peer-to-peer car owners (the "I have a car" door) or licensed yards only?
- Will UG hold money at all, or only ever instruct a licensed processor to hold and release it?
