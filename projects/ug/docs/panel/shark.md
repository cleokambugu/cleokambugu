# UG pre-seed critique

## Verdict

Not on this plan. I would write a small cheque (US$150–200k) on one condition: the raise funds **only the Virtual Stage on one corridor** for 90 days, with a driver price that is commercial, not a "cost split". Kill criteria at day 90: 500 paid seats, 60% of drivers accepting a second offer, no refund at cut-off above 20%. Everything else in `business-plan.md` (Rent, Explore, Hustle Mode, UG Plus, the data business) is a Series A conversation at best.

## What is genuinely new

`v1-concept.md` has one real idea: riders **escrow money before a car exists**, and the platform manufactures a funded trip inside a driver's declared comfort map. Swvl needed a fleet, BlaBlaCar needs the driver to post, inDrive haggles per trip. Pre-paid demand handed to a private driver is a legitimate inversion, and Empty Legs at 40% is a clean add-on. The Vouch mechanic digitising the stage-chairman check (`onboarding.md`, SafeBoda row) is good local observation. That is the company. The compare desk is not.

## Five things that kill this

1. **The driver has no reason to say yes.** `arbitrage-model.md` gives the driver `per_seat × (seats−1)`: cost recovery, zero profit. A Jinja run at the model's own constants costs ~UGX 70,000 in fuel and wear; the "UGX 84,000 waiting" offer in `v1-concept.md` nets him ~UGX 14,000 for three hours plus a dead return. BlaBlaCar works because the driver was going anyway; the Virtual Stage explicitly manufactures trips he was not taking.
2. **The compare screen is wrong by construction.** Fourteen of fifteen tariff rows are *modelled* or a 2020 Uber blog snippet (`uganda-fares.md`). Bolt and Yango surge dynamically. The plan makes this screen the marketing hook ("everyone screenshots a price comparison"); the first screenshot next to a live Bolt quote ends the trust story.
3. **The platforms will not cooperate.** Deep links carry no price; the user lands in Bolt and sees a different number. Uber's history with aggregators is litigation, not affiliate fees. `business-plan.md` §7 argues "a published model is UG's speech"; a Kampala court is not where a pre-seed company wants to test that.
4. **Processing eats half of revenue.** The §5 table: UGX 67m gross, UGX 31.5m to Flutterwave, because UG collects UGX 900m of GMV to earn a 10–12% take. That is a structural margin problem, not a negotiation.
5. **Cost-sharing vs commerce is a legal contradiction.** §8 says pooling "sits in a grey zone" as cost-sharing. The moment the driver earns above cost (which he must, see 1), it is PSV carriage requiring SGS inspection, third-party insurance and a licence (`onboarding.md`). The plan wants the price of one and the legality of the other.

## Unit economics I do not believe

- **0.6 pool seats per MAU per month** (6,000 seats, ~1,500 full cars, on three launch corridors). Replace with 0.1 in year one, and one corridor.
- **Average seat UGX 25,000.** The formula produces ~UGX 15,500 for Jinja; the matatu is UGX 20–30k. Either the seat is not cheaper than the matatu, or revenue per seat is UGX 1,500, not 2,500. Replace with a commercial price: driver floor (Bolt-equivalent hourly plus fuel) ÷ 4, UG 15% on top, and accept the seat is ~UGX 25–30k, competing on comfort and time, not price.
- **400 rentals/month × UGX 450,000** is 4% of MAU renting a car every month. Replace with 40.
- **150 Explore weekends × UGX 2.2m** from households earning UGX 1–5m/month. Replace with zero until Phase 3.
- **3% subscription conversion at UGX 38,000 blended.** Boujee costs more than the savings it promises. Replace with 0.3% or delete.
- **Referrals: 25% signed partners × UGX 500.** Replace with zero.
- **Processing 3.5% of UGX 900m.** Charge the fee to the rider explicitly and use Flutterwave split payouts; model processing as a cost of the seat price, not of UG's revenue.

## Recommendations for v2

1. One corridor: Kampala–Entebbe airport, hourly stages, where the matatu is weak and the UGX 80–120k special hire makes a UGX 30k pooled seat obviously cheaper *and* pays the driver UGX 100k+.
2. Reprice Pool as commercial carriage with a driver floor and a 15% take; delete the cost-split narrative from the deck.
3. Get the Ministry of Works/TLB written position and a per-seat insurer quote as a gating milestone before writing the backend in `roadmap.md` Phase 1.
4. Demote the compare desk to a weekly crowd-sampled index with dated provenance; no deep links, no 2020 tariffs in production.
5. Remove Rent, Explore, Hustle Mode, UG Plus and the Felt/Tazama/Cephable plug-ins from the product surface until 1,000 paid seats.
6. Rebuild the §5 table bottom-up from the first 90 days of Entebbe data, not from MAU multipliers.

## The kill question

At what per-seat price does the Friday Jinja car both beat the UGX 25,000 matatu and pay the driver more than he would earn on Bolt that evening, and does that price survive the cost-sharing legal position you are relying on?
