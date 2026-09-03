# Quality: what UG may say about whom

The Quality section of the app points at this file, so this file has to be the real thing: the
meters, the weights, the thresholds, the seeded rows, and — most importantly — the rule about
whose name a number may be printed beside.

## The rule

**A score next to a company's registered name is a statement of fact about that company.**

UG has not brokered enough trips to make one. So it does not make one. That is the whole
governing rule, and everything below follows from it:

| | Published today | Published when |
|---|---|---|
| **The offer** — what an operator has put on the record | Yes, with the page it was read from | now |
| **The delivery** — how well they keep it | No | after 200 UG-brokered trips with that operator |
| **The arithmetic** | Yes, on four invented operators | now |

An earlier version of this build got this wrong, and it is worth recording why, because the
mistake is an easy one to make and it is not a small one.

That version printed a hand-typed table of reliability percentages beside nineteen real
operators — *"Bolt · 80 · Steady, reliable, with gaps it has not closed"*, *"Yango · fixed what
broke: 44"* — on a public page, next to drawn versions of their marks, under a headline claiming
the ranking was impartial. The figures were invented. The disclosure was four levels down inside
a collapsed panel. Two independent reviews landed on it as the single thing most likely to end
the company: in Uganda that is injurious falsehood with **no justification defence available**,
because UG would be conceding the statements were untrue. It also poisons every partner
conversation the business needs, and it hands a competitor a press release.

The rows were deleted. What replaced them is better product anyway, because "here is what they
promised, in writing, and here is where we read it" is a genuinely useful thing that nobody else
publishes, and it is true.

## The offer

Eighteen promises an operator can put on the record. Each is tied to the meter that would judge
it — a promise with no meter cannot be declared, and `qaValidate()` fails the build rather than
warning about it.

| Promise | Meter | |
|---|---|---|
| A published price · No surprise charges · Quoted before you board | money | a fare anyone can check, and the number quoted is the number charged |
| A pickup window | time | a time it will be there by, not a guess |
| Accepts and comes · Free cancellation · Runs after dark | shows | an accepted trip is a trip that happens |
| A helmet · Belts that work · Passenger cover · A receipt · Takes luggage · Step-free boarding · Serves you in your language | care | |
| A line a person answers · An answer within a day | fix | |
| The driver paid weekly, in full · The rate published to the driver | pay | |

Where an operator publishes nothing, the board says **none published**, and says in the same
breath that this is a fact about the paperwork rather than about the service. A stage taxi has no
press office. Many of the best drivers in Kampala have never written a promise down. Marking them
down for that would be ranking companies by whether they have a marketing department, which is
exactly what this system exists not to do.

Sources are in `QA_OFFER_SRC`. Three operators — the street boda, the special hire, the matatu —
have no entry, deliberately.

## The six meters

Each is fed by evidence UG can hold, not by opinion.

| Meter | Weight | Evidence |
|---|---|---|
| Kept the price | 1.30 | the quote against what was actually charged |
| Kept the time | 1.15 | the promised window against the trip rail's own timestamps |
| Showed up | 1.25 | accepted against completed |
| Treated you right | 1.20 | reported conduct, kit and the state of the vehicle |
| Fixed what broke | 0.90 | complaints resolved, and how quickly |
| Paid the driver | 1.00 | the supply side's own report |

**Weights are fixed.** An earlier version summed the weights of the promises resting on a meter,
which meant a supplier could triple the weight of its best meter by publishing a handful of
promises that cost it nothing. A promise decides *whether* a meter is scored. Never how much it
counts.

**Care is scored for everybody**, declared or not. Declining to promise a helmet is not a defence
for riding without one.

## The arithmetic

```
score = Σ(wₘ · pulledₘ) / Σ wₘ        over meters the supplier's promises rest on, plus care
pulledₘ = (n·rawₘ + K·priorₘ) / (n + K)          K = 25 trips
w(report) = 0.5 ^ (max(0, age_days) / 90)        half-life 90 days, never above 1
```

`priorₘ` is a fixed market baseline — money 86, time 70, shows 85, care 80, fix 55, pay 84 —
published here and **not** derived from the evidence it is correcting. A previous version took the
median of the same seeded table within a supplier's own category; three categories had a single
member, so shrinkage did nothing for them, and a helicopter charter with twelve trips ranked first
on a page claiming that could not happen.

`max(0, age)` matters more than it looks: without it a report dated in the future scored
`0.5^negative` and carried more than full weight. One forged timestamp was worth two thousand
honest reports.

### Bands

Keeps its word 84+ · Steady 70+ · Watch 55+ · Suspended below.

Two things move the band without touching the number, because the measurement should stay
readable and the consequence should still apply:

- **A safety breach** (care below 72) holds the band at Watch however good the rest is.
- **Fewer than six published promises** caps the band below the top. This closes the obvious gap:
  otherwise the safest way to score well is to stop making claims. It only ever applies to
  suppliers who *have* a delivery score, which is why it cannot be used against an operator with
  no press office.

## What does not count

Brand. Age. Fleet size. Funding. Advertising. Money paid to UG, of which there is none to pay.
Whether UG competes with them. Whether they have a website. There is no input for any of these and
no way to buy a position, because there is nothing to sell.

## UG's own services

Scored by the same meters and marked as UG's own on every row. No independent auditor has looked
at them. That is stated on the card rather than implied, and it is the reason the arithmetic,
weights, thresholds and seeded rows are all published here: so that somebody can.

## What is real in this build

- **Real:** the offer record and its citations; the arithmetic; the demonstration; the publication
  floor; the personal hide; the correction path; the fix ledger.
- **Simulated:** the four demonstration operators — Kanyanya Express, Rwenzori Riders, Nile
  Coaches, Kigo Cars — who do not exist. Their figures are chosen to show the meters working.
- **Not built yet:** the server side. Reports, hides and fixes live in `localStorage` today, which
  means "stop the line" stops nothing beyond your own board and a fix reaches nobody. Before this
  system carries any weight it needs identity, deduplication, rate limits, an audit log, an
  appeals queue and a named reviewer. That is a team, not a function, and the section does not
  claim otherwise.

## The practices

Six working practices sit under the board, each with a mechanism attached rather than a poster:
stop the line, go to the stage, little by little, make the wrong thing impossible, ask why five
times, look back even when it went well.

Their lineage is the Toyota Production System and the quality tradition around it — *andon*,
*genchi genbutsu*, *kaizen*, *poka-yoke*, the five whys, *hansei*. That is credited here, in the
methods document, and deliberately nowhere in the interface. Borrowing a practice and then
dressing a Ugandan product in another culture's vocabulary would be the wrong way round. In the
product each practice is named in whatever language the reader chose, and where that language
already carries a saying for the idea, the saying is what appears: *haba na haba hujaza kibaba* in
Swahili, *akatono katono kajjuza ensuwa* in Luganda. The thought arrives in a language that has
been thinking it.

## Anti-gaming, and what is still open

Closed: fixed weights; the exposure ceiling; the clamped decay; a prior from outside the evidence;
the safety hold; no third-party scores at all until UG has its own trips.

**Still open, and a reader should know it:** nothing yet binds a report to a paid, completed trip
on a device that was at the pickup. Until that exists, the reports are honest by convention rather
than by construction. It is the first thing the server has to enforce.
