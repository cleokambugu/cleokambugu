# UG business plan

Working draft, September 2026. Figures marked *(snippet)* were read from search results and
third-party pages, not from the operator or the statistics bureau; treat them as direction, not
fact. Figures marked *(modelled)* are assumptions to be tested.

## 1. The one-line

UG is the app a Kampala professional opens before any trip: it shows every ride option on the
market priced side by side, and it sells the two things nobody else bundles well, a shared seat
on the road trip and a rental priced per head.

## 2. Who it is for

**The aspirational middle.** Household income roughly UGX 1–5 million a month, which is the
range Ugandan researchers use to define the middle class *(snippet: KAS paper; EPRC puts about
8.3 million Ugandans, 22%, in the middle class on 2016/17 data)*. Kampala's median household
income is around UGX 667,000 *(snippet)*, so the top quarter of urban earners is the market.

What they have in common:

- **Multiple lives at once.** A salaried job, a side hustle (cakes, imports, land, a boda they
  own), a family run, a church or alumni circle, and a social calendar that demands a visible
  car at a kwanjula or an introduction.
- **A budget that must stretch to look bigger than it is.** The Prado at the function matters;
  paying for it alone does not. Splitting is the norm, and it is currently done over WhatsApp
  and cash.
- **App fatigue.** Uber, Bolt, SafeBoda, Faras, Yango, Tinka, and inDrive all on one phone.
  Everyone already price-checks across two or three apps before booking. UG does it in one tap.
- **Domestic tourism is affordable to them and under-served.** East African citizens pay
  UGX 300,000 for a gorilla permit against US$800 for foreign visitors *(snippet: UWA tariff to
  June 2026)*. Park entry for citizens is UGX 20,000–25,000. The barrier is transport and
  planning, not fees.

## 3. The product: Ride. Pool. Rent.

Sixt's product architecture is the template: one app, a few verbs, one account. UG's
catchphrase is the product in order of use: Ride (daily), Pool (weekly), Rent (the occasion).
Explore is the weekend planner that uses all three.

| Verb | What it does | UG's edge |
| --- | --- | --- |
| **Ride** (the arbitrage desk) | Quotes Uber, Bolt, SafeBoda, Faras, Yango, Tinka, the street boda, the matatu, a special hire, the bus, and UG's own pool and rental for the same trip; ranks by price; deep-links to the winner. | Competitors are the inventory. UG earns the click and the trust, never a mark-up. |
| **Pool** | Verified drivers post intercity and airport trips; riders take seats at the true road cost divided by seats plus 10%. Circles (employer, alumni, church, school run) keep it among people who half-know each other. | Pool-style trust (phone verification, trip chat, two-way ratings) with a transparent cost formula instead of a haggled fare. |
| **Rent** | Self-drive or chauffeured, priced per day and per head. Deposit of 20% by MoMo. | The per-head price is the product. A Prado at UGX 300,000/day is UGX 75,000 each for four. |
| **Explore** | Pick a destination; get park entry, permits, vehicle fee, lodge, food and transport totalled for the party, by residency category, with pooled transport as the default. | The only planner that computes EAC-citizen prices, which is what the target market pays. |

A fifth surface, **Hustle Mode**, chains the day's legs (school run, office, client lunch,
delivery, home) and quotes each on the cheapest sensible mode with money held in the UG wallet.
It is the feature that makes the app daily rather than occasional.

## 4. Revenue model

| Stream | Mechanics | Assumption |
| --- | --- | --- |
| Pool commission | 10% of the rider share on every seat. | Average seat UGX 25,000 → UGX 2,500 per seat. *(modelled)* |
| Rental listing and booking fee | 12% of the booking from the yard, plus the deposit float. | Average 3-day booking UGX 450,000 → UGX 54,000. *(modelled)* |
| Referral on Ride | Affiliate and partner deep links; where a partner will not pay, the click is still the reason users return. | UGX 300–800 per referred booking, only with partners that sign. *(modelled)* |
| Explore deposits | 15% deposit collected by UG, 5% retained as planning fee on lodges and activities booked through UG. | Average weekend for four UGX 2.2 million → UGX 110,000. *(modelled)* |
| UG Plus subscriptions | Boujee UGX 29,000/month; Executive UGX 79,000/month. | 3% of MAU convert. *(modelled)* |
| Data and B2B | Anonymised fare index sold to fleets, insurers, and the regulator; corporate travel accounts. | Year 2 onward. |

Payments run through Flutterwave. Its Uganda mobile money collection fee should be taken from
its live pricing page (flutterwave.com/ug/pricing) before modelling margins; the page was not
reachable from this session. Budget 3–4% of collected value *(modelled)*.

## 5. Unit economics at 10,000 monthly active users (modelled)

| Line | Per month |
| --- | --- |
| Pool seats: 10,000 MAU × 0.6 seats × UGX 2,500 | UGX 15.0 m |
| Rentals: 400 bookings × UGX 54,000 | UGX 21.6 m |
| Explore: 150 weekends × UGX 110,000 | UGX 16.5 m |
| Subscriptions: 300 × blended UGX 38,000 | UGX 11.4 m |
| Referrals: 20,000 clicks × 25% signed partners × UGX 500 | UGX 2.5 m |
| **Gross revenue** | **UGX 67.0 m** |
| Payment processing (3.5% of ~UGX 900 m collected) | (UGX 31.5 m) |
| Support, verification, insurance float | (UGX 8.0 m) |
| **Contribution before payroll and marketing** | **UGX 27.5 m** |

The processing line dominates because UG collects the whole seat or rental price and pays out
the driver's or yard's share. Two levers: negotiate a lower collection rate at volume, or
collect only UG's fee and let the driver collect the rest in MoMo directly (cheaper, but
weaker on trust and disputes). The prototype models full collection.

## 6. Go-to-market

1. **Circles first.** Launch with five employers, two universities' alumni groups, and two
   large churches. Every pool trip needs a full car; circles are where the trust already is.
2. **The Friday Jinja run and the Sunday airport run.** Two routes with obvious repeat demand.
   Own them before generalising.
3. **The compare screen as marketing.** It is shareable, honest, and useful on day one with
   zero supply. Everyone screenshots a price comparison.
4. **Kwanjula season.** Rental per-head pricing pitched at introduction ceremonies and
   weddings, where the vehicle is a status item and the cost is always shared.
5. **Domestic tourism partners.** Uganda Wildlife Authority tariffs for citizens are the
   story; lodges get groups arriving on known dates.

## 7. Why competitors will tolerate being listed

A pre-filled deep link is a booking with no acquisition cost. Faras runs on a 10% commission
and SafeBoda on about 15% *(snippet)*; both need volume more than they need exclusivity. The
ride-hailing apps do not sell intercity seats or per-head rentals, so UG does not eat their
core. The risk is the opposite: an app declining to be compared. The answer is to publish the
method and let a user compare anyway; a quote from a published model is UG's speech, not the
partner's data.

## 8. Risks and honest unknowns

- **Tariff data.** No operator publishes a current tariff. The engine uses a 2020 Uber tariff
  and modelled values for the rest. Live accuracy needs partner APIs or a sampling programme
  (drivers and riders submitting screenshots for wallet credit).
- **Regulation.** Ride-hailing and boda operation are licensed through the Transport Licensing
  Board; boda riders need a Class M permit and a PSV licence *(snippet)*. Pooling by private
  drivers for cost-sharing sits in a grey zone that must be cleared with the Ministry of Works
  and Transport before launch. Rentals are a licensed business; UG should broker for licensed
  yards rather than own cars.
- **Payments.** Flutterwave holds a Bank of Uganda PSO licence *(snippet)*; UG itself must not
  hold customer float without the right licence. Collect and pay out, do not bank.
- **Safety liability.** Pool trips between private individuals need insurance. Model an
  optional per-seat cover with a local insurer before scaling.
- **Google Antigravity ambiguity.** The brief's "interactive 3D images like Google Antigravity"
  refers to a landing page style (floating, pointer-reactive particles) rather than a data
  standard. The site reproduces the technique; nothing about Google is used.
