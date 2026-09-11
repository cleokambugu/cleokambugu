# MITx Finance MicroMasters — curriculum map

MIT Sloan's graduate finance sequence, delivered online. Six courses; the
first five are taught, the sixth is a proctored comprehensive exam. Content is
shared with MIT's residential Master of Finance.

> **Provenance.** Course codes, titles, prerequisites, ordering and instructors
> are *(secondhand)* — assembled from search snippets, because every
> MIT-operated host is blocked from this sandbox (see
> [`README.md`](README.md) for the list and the evidence). The detailed topic
> maps for **15.435x** and **15.455x** are first-hand reading of two learner
> coursework repos, cited inline. Nothing below was read from an MIT-authored
> syllabus.

---

## The six courses *(secondhand)*

| # | Code | Course | Role |
|---|---|---|---|
| 1 | **15.415.1x** | Foundations of Modern Finance I | Entry point |
| 2 | **15.415.2x** | Foundations of Modern Finance II | Continues I directly |
| 3 | **15.516x** | Financial Accounting | Entry point |
| 4 | **15.455x** | Mathematical Methods for Quantitative Finance | Entry point |
| 5 | **15.435x** | Derivatives Markets: Advanced Modeling and Strategies | Advanced |
| 6 | **CFx** | Comprehensive Final Exam in Finance | Proctored capstone |

The screenshot that prompted these notes shows the first five; CFx sits below
the fold.

**Ordering.** Three courses are *entry points* with no dependency on the
others: 15.415.1x, 15.516x, 15.455x. Start with any. The hard constraint is
that **15.415.1x must precede 15.415.2x** — they are one course split in two,
and the second begins exactly where the first ends. Learners are explicitly
discouraged from taking them concurrently or in reverse. 15.435x sits on top,
suggesting 15.415.1x/.2x plus calculus, with 15.455x and basic programming
recommended.

**Format.** Self-paced and on demand; all content unlocks at enrolment.
15.415.1x runs a Week 0 introduction plus 10 lectures, 10 problem sets and 10
recitations. 15.415.2x is listed at ~16 hours of lecture video over 12 weeks
with a proctored final. 15.435x runs 12 weeks.

**Prerequisites** *(secondhand)*: calculus and linear algebra required
throughout; probability and statistics suggested. 15.435x also recommends
basic programming. 15.455x teaches applied computation in **R**; the
implementation in this repo is Python, which is a deliberate departure, not a
claim about the course.

**Instructors** *(secondhand)*: Leonid Kogan, Jiang Wang and Egor Matveyev
(15.415.1x/.2x); Deborah Lucas (15.435x). 15.435x is organised around chapters
of Hull, *Options, Futures and Other Derivatives*.

---

## 1. 15.415.1x — Foundations of Modern Finance I *(secondhand)*

A unified framework for valuation, investment and corporate decisions. Four
stated topics:

1. The financial problems firms and households actually face, and the
   principles of modern finance for tackling them.
2. **Valuation of fixed income securities and common stocks.**
3. **Risk analysis, the Arbitrage Pricing Theory (APT), and the Efficient
   Market Hypothesis (EMH).**
4. **Introduction to corporate finance and capital budgeting.**

→ Implemented in [`finlib/tvm.py`](../../tools/finance/finlib/tvm.py),
[`fixed_income.py`](../../tools/finance/finlib/fixed_income.py),
[`equity.py`](../../tools/finance/finlib/equity.py).
Skill: [`finance-valuation`](../../.claude/skills/finance-valuation/SKILL.md).

## 2. 15.415.2x — Foundations of Modern Finance II *(secondhand)*

Picks up where I stops. Topic list:

- **Forwards and Futures**
- **Options**
- **Portfolio Theory**
- **Capital Asset Pricing Model (CAPM)**
- **Capital Budgeting and Real Options**
- **Financing / Capital Structure**
- **Interaction between Investing and Financing**
- **Payout and Risk Management**

→ [`portfolio.py`](../../tools/finance/finlib/portfolio.py),
[`derivatives.py`](../../tools/finance/finlib/derivatives.py),
capital structure in [`equity.py`](../../tools/finance/finlib/equity.py).
Skills: [`portfolio-theory`](../../.claude/skills/portfolio-theory/SKILL.md),
[`derivatives-pricing`](../../.claude/skills/derivatives-pricing/SKILL.md).

## 3. 15.516x — Financial Accounting *(secondhand)*

Snippet-level only; this is the thinnest topic map here, and the honest label
is that it is an outline rather than a syllabus. Topics surfaced: the
accounting equation and balance-sheet entries, **accrual accounting**, revenue
recognition and allowances, inventory valuation, depreciation, long-term debt
and leases, income taxes, shareholders' equity and earnings per share, and
introductory financial statement analysis.

→ [`accounting.py`](../../tools/finance/finlib/accounting.py).
Skill: [`financial-accounting`](../../.claude/skills/financial-accounting/SKILL.md).

## 4. 15.455x — Mathematical Methods for Quantitative Finance

The mathematical foundations for financial engineering: linear algebra,
optimisation, probability, stochastic processes, statistics, and applied
computation in R.

**First-hand** — the topic list below is the `README.md` of
[`m-chinmayee/MITx_15.455x_...`](https://github.com/m-chinmayee/MITx_15.455x_Mathematical_Methods_for_Quantitative_Finance)
at commit `09d0a01`, a learner's coursework repo cloned and read directly:

> 1. Probability
> 2. Discrete-time Stochastic Processes
> 3. Time Series
> 4. Continuous-time Stochastic Processes
> 5. Ito Calculus
> 6. Continuous-time Finance
> 7. Optimization
> 8. Optimal Decision Making and Optimal Strategies

The committed code in that repo shows what the exercises look like in
practice, which is the more useful signal:

| File | Exercise |
|---|---|
| `week3_module2_time_series.py` | Generate random-walk, AR(2), MA(2) and ARMA(2,2) data; identify order from **ACF and PACF** |
| `week3_recitation_monte_carlo.py` | Monte Carlo price paths via a binomial model, motivating the lognormal/GBM limit |
| `week3_module4_gamblers_ruin.py` | **Gambler's ruin** with absorbing boundaries, over many instances, to get the distribution of ruin times |
| `week4_continuous_time_models.py` | Brownian motion as the continuous limit of the normal random walk |

Course-page topics add *(secondhand)*: continuous-time limits of discrete
processes, properties of Brownian motion, **Ito's lemma**, the
**Black-Scholes-Merton equation**, dynamic hedging and risk management;
covariance/correlation matrices for asset pricing; and optimisation —
Lagrange multipliers, inequality constraints, quadratic programming, Markov
decision processes, dynamic programming — applied to portfolio construction
and algorithmic trading.

→ [`stochastic.py`](../../tools/finance/finlib/stochastic.py),
[`linalg.py`](../../tools/finance/finlib/linalg.py).
Skill: [`quant-methods`](../../.claude/skills/quant-methods/SKILL.md).

## 5. 15.435x — Derivatives Markets: Advanced Modeling and Strategies

Stated aims *(secondhand)*: a sophisticated understanding of derivative
modelling, valuation and hedging; familiarity with the major markets,
instruments and strategies; and insight into current market developments.

**First-hand** — the following is the structure of the final-exam cheat sheet
in [`ol-gerd/MIT15.435x`](https://github.com/ol-gerd/MIT15.435x) at commit
`40c9508`, cloned and read directly. It is a learner's summary, not MIT's, and
it is the sharpest available picture of the course's actual scope:

| Section | Covers |
|---|---|
| **Forward Contracts** | Cost of carry across stocks, dividend payers, coupon bonds, FX and commodities; value of an existing forward; hedge ratios |
| **Futures and Swaps** | Margin mechanics; fixed-float swap valuation and the **par swap rate**; Eurodollar futures; currency and commodity swaps; total-return swaps |
| **Duration and Convexity** | Macaulay, modified and dollar duration; convexity; the second-order price approximation; portfolio aggregation; hedging with forwards; **numerical duration/convexity by central differencing** |
| **Option Strategies** | Put-call parity; protective put, covered call, bull/bear spreads, butterfly, straddle, strangle; no early exercise for an American call on a non-dividend stock |
| **Pricing Options** | **Replicating portfolio** and **risk-neutral** one-step valuation; calibrated CRR trees (`u = e^{σ√h}`, `d = 1/u`); the futures case `q* = (1−d)/(u−d)`; Black-Scholes with dividends; Black's formula for futures options; *"careful — with discrete dividends the tree does not recombine"* |
| **Greeks** | Delta, gamma; mid-point numerical gamma |
| **Delta-Gamma Hedging** | The two-equation system: `N* = −Γ/Γ*`, then shares for residual delta |
| **Volatility** | Smile/skew — Black-Scholes underprices at low `K/S`, overprices at high; CEV, Heston, jump diffusion |
| **Exotics** | Binary (cash- and asset-or-nothing, and their decomposition into a vanilla); Asian; barrier with in/out parity; lookback; **exchange (Margrabe)**; compound; gap |
| **Monte Carlo hints** | The GBM stepping formula; generating correlated Gaussians via `ε₂ = ρε₁ + √(1−ρ²)ε` |
| **Bonds and Rate Options** | Black's model for bond options; short-rate binomial trees; bonds with embedded options (callable = vanilla − call); caps as strips of caplets |
| **Credit Risk** | Credit spreads and option-adjusted spread; expected vs promised cash flows; **structural approach** — equity as a call on firm assets, debt as risk-free bond minus a put, loan guarantees as puts; the **Merton model** |
| **Credit Derivatives** | CDS mechanics; securitisation and tranche correlation (equity tranche long correlation, senior short); PSA prepayment; pass-through vs sequential-pay; IO/PO duration behaviour |

→ [`derivatives.py`](../../tools/finance/finlib/derivatives.py) and
[`fixed_income.py`](../../tools/finance/finlib/fixed_income.py).
Skill: [`derivatives-pricing`](../../.claude/skills/derivatives-pricing/SKILL.md).

**Implemented:** forwards and cost of carry, par swap rates, the full
duration/convexity toolkit including numerical variants, put-call parity,
replication and risk-neutral valuation, calibrated CRR trees with American
exercise, Black-Scholes and Black-76, the Greeks, delta-gamma hedging, and the
closed-form exotics (binary, gap, Margrabe), with Asian by Monte Carlo.

**Not implemented:** credit risk and credit derivatives (Merton structural
model, CDS, tranching, prepayment), short-rate trees and bonds with embedded
options, and barrier/lookback closed forms. These are mapped above but absent
from `finlib` — a deliberate boundary, and the obvious next increment. Stated
here rather than left for someone to discover.

## 6. CFx — Comprehensive Final Exam in Finance *(secondhand)*

A proctored exam across the five courses, required for the credential.

---

## What this maps onto

| Course | Module | Skill |
|---|---|---|
| 15.415.1x | `tvm`, `fixed_income`, `equity` | `finance-valuation` |
| 15.415.2x | `portfolio`, `derivatives`, `equity` | `portfolio-theory`, `derivatives-pricing` |
| 15.516x | `accounting` | `financial-accounting` |
| 15.455x | `stochastic`, `linalg` | `quant-methods` |
| 15.435x | `derivatives`, `fixed_income` | `derivatives-pricing` |

74 verification checks, all passing:
`python tools/finance/test_finlib.py`.
