# Stay on UG: booking with partners without leaving

The arbitrage desk only works as a product if the customer never leaves. In v0 every partner
quote opened the partner's app in a new tab; that is a comparison site, not a product. From
v1.1 the primary action on every quote is **Book on UG**, and a **trip rail** in the nav shows
the booking through to done. The partner link remains as a quiet secondary for anyone who
wants it.

## How it works in the prototype

1. The customer confirms the quote and pays on UG (sandbox).
2. UG's concierge places the booking with the partner. In the prototype this is simulated with
   timers: placed, driver and plate assigned, arriving, on trip, done.
3. The rail shows each state with a time, a call button once a driver is assigned, an ETA to
   share, a cancel while nothing has been placed, and "say what happened" at the end.
4. Parcels run on the same rail: placed, courier assigned, picked up, on the way, delivered
   (signed for if requested).

## How it must work in production

A research agent surveyed the partners' business and programmatic channels on
2 September 2026, by search snippets only (the pages themselves are blocked from the session).
Everything below is *(snippet)* and must be verified before a contract is signed.

| Operator | Guest or business booking channel | Programmatic access | Delivery product | Confidence |
| --- | --- | --- | --- | --- |
| **Uber** | Uber Central (Uber for Business): a coordinator enters the rider's phone and pickup/drop-off; the rider gets an SMS with a tracking link and needs no app or account; book now or up to 30 days ahead. | **Guest Trips API** in the U4B API suite, positioned as the way to embed Central in your own software. Separately **Uber Direct** (courier quotes, deliveries, tracking, proof of delivery, webhooks). | Uber Direct, Uber Eats | High for the products; Uganda availability of Central and Direct unconfirmed |
| **Bolt** | Ride Booker in Bolt for Business: designated agents book for guests, now or scheduled; the passenger gets an SMS with driver and ETA; monthly reporting. | No public ride API found. Merchant-side delivery APIs exist (Bolt Food/Market; a "Bolt Business Delivery" doc). | Bolt Food; business delivery | Medium (Ride Booker) / Low (API) |
| **SafeBoda** | SB Business: sub-accounts per branch, a central wallet, trip approvals before dispatch, live tracking, reporting; "send package" settled from the business wallet. | Nothing found. | SafeBoda Send | Medium (channel) / Low (API) |
| **Faras** | "Corporate travel" for teams and clients. | Nothing found. | Package and food delivery | Low |
| **Yango** | Partner programme with an embeddable ride-request widget. | Partner API (key by email, `YaTaxi-Api-Key`, client id); partner-gated. | Not surfaced for Uganda | Medium |
| **Tinka** | Nothing on business accounts; consumer app with taxi, boda, parcel delivery, MoMo. | Nothing found. | In-app parcel delivery | Low |
| **inDrive** | Consumer "book for someone else" only. | No public API. | Express delivery | Low |
| **8 to 8** (Jinja) | Nothing found online. | Nothing found. | The product itself, per the founder's brief. | Not verified |
| **SafariShare** (precedent) | Rolling out a nationwide network of registered agents who book buses on behalf of customers and earn mobile-money commissions; partnership with the Uganda Bus Operators Association. | Nothing public. | Parcels on bus routes planned. | Medium |

## Five design rules that follow

1. **The rider's phone number is the identity.** Uber Central and Bolt Ride Booker both key a
   trip to a phone and push an SMS with the driver, ETA and a tracking link. The customer never
   needs the partner's app; UG's rail is where they watch it.
2. **Dashboard first, API second.** Only Uber surfaced a real guest-trip API. Budget a
   concierge console per partner, staffed, with Uber as the one clean programmatic path and
   Yango by partner agreement.
3. **Separate the ride rail from the delivery rail.** Delivery APIs (Uber Direct, Bolt's
   merchant delivery API) are more open than ride APIs. Parcels can be API-native sooner.
4. **Pre-pay through a central business wallet with approvals.** SafeBoda's business wallet with
   trip approvals and sub-accounts is the local model: the concierge holds the business
   account, the customer never pays the partner directly, reconciliation is monthly. This must
   be squared with the panel's float finding: the business wallet is the partner's, not UG's.
5. **Position UG as an agent, not a reseller.** SafariShare's registered-agent network booking
   on commission shows operators and regulators already accept booking on behalf of riders.
   The stage chairman as a UG agent fits the same frame.

## What the code does and does not do

The rail is a state machine in the browser with timers standing in for a partner's console
and webhooks. Production replaces the timers with the partner channel (API, console or
staffed line) and the backend's intent state machine (`../server/openapi.yaml`, `/offers`,
`/stages/{id}/depart`, and a new `/bookings` resource to add for partner trips).
