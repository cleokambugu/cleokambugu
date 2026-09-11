# What survived contact with an implementation

The transferable results from building [`tools/finance/`](../../tools/finance/)
against this curriculum — the things that stay true after the library version
moves, and the places where writing the code taught something the formula
sheet did not.

Every claim here is anchored to a file and pinned by a check in
`tools/finance/test_finlib.py` (74 checks, all passing).

---

## 1. Three routes to the same number is the best debugger in finance

A binomial tree with the step shrinking to zero *becomes* geometric Brownian
motion. So the same European option price must fall out of a tree, a closed
form, and a Monte Carlo simulation. When they disagree, one has a bug — and
you usually learn which from *how* they disagree.

```
Black-Scholes       10.4506
binomial (1000)     10.4486     ← O(1/steps) convergence, oscillating
Monte Carlo         10.4645 ± 0.0329   ← brackets BS inside its 95% CI
```

This triangle caught more mistakes during the build than any amount of
re-reading. `test_binomial_converges_to_black_scholes` also checks that *more
steps reduces the error* — a tree that agrees at 3000 steps but not at 25 is
suspicious in a different way than one that never agrees.

**Generalises to:** any quantity with an analytic and a numerical route. Pin
them against each other and you get a regression test that survives
refactoring.

## 2. A confident wrong error bar is worse than no error bar

The one genuine bug the test suite caught in my own code.

`monte_carlo_european` supports antithetic variates: draw `z`, use both `z`
and `−z`. The first implementation pooled all the payoffs and computed a
sample variance across them. That is **invalid** — the two halves of a pair are
negatively correlated *on purpose*, which is the entire mechanism. Treating
them as independent produces a standard error that does not describe the
estimator in use.

The fix is to make the **pair mean** the independent sampling unit, and to
report `draws` separately from `paths`
([`stochastic.py`](../../tools/finance/finlib/stochastic.py)). Only then does
the reported `stderr` actually fall when variance reduction works — which is
what `test_antithetic_variates_reduce_standard_error` now asserts.

**The lesson:** a variance-reduction technique changes the *estimator*, so it
changes how the error must be computed. Bolting it onto an unchanged variance
formula silently invalidates the confidence interval — and a simulation that
reports tight, wrong error bars is more dangerous than one that reports none,
because it invites trust.

## 3. Distinguish truncation error from a wrong formula

Numerical effective duration disagreed with the analytic modified duration by
2×10⁻⁶. Tempting to shrug and loosen the tolerance. Instead: central
differencing has O(Δy²) truncation error, so **halving the step should cut the
error by four**. It does — so the residual is truncation, not a wrong formula,
and the test now asserts the convergence ratio rather than just a loose bound
(`test_duration_and_convexity_match_numerical_repricing`).

**Generalises to:** any "close but not equal" numerical result. Don't widen
the tolerance until you can name the error term and show it behaves as that
term predicts. A tolerance chosen to make a test pass tests nothing.

## 4. No-arbitrage identities are free, model-independent test oracles

Put-call parity holds *whatever* model produced the prices — it is pure
replication, not a modelling assumption. So it is the first check to run on
any option pricer, including one you did not write.

The same trick appears throughout, and each one became a test:

| Identity | Why it is free |
|---|---|
| `C − P = Se^{−qT} − Ke^{−rT}` | replication |
| asset-or-nothing − K × cash-or-nothing = vanilla call | payoff decomposition |
| American call = European (no dividends) | never optimal to exercise early |
| Margrabe with `ρ=1`, equal vols = intrinsic | spread vol is exactly zero |
| bond at par when `y = c` | definition |
| zero-coupon Macaulay duration = maturity | definition |
| par swap rate on a flat curve = the flat rate | algebra |
| WACC invariant to leverage, no taxes | Modigliani-Miller I |
| DuPont product = ROE computed directly | algebra |

**The lesson:** before writing a numerical test with a magic constant, look
for an identity the answer must satisfy. Identity-based tests don't go stale
when you change the implementation, and they fail for comprehensible reasons.

## 5. Zero dependencies was a feature, not a constraint

The sandbox had no numpy, scipy, pandas or statsmodels. Rather than treat that
as a blocker, the whole engine went to pure stdlib: normal CDF from
`math.erf`, matrix inverse by Gauss-Jordan with partial pivoting
([`linalg.py`](../../tools/finance/finlib/linalg.py)), ACF/PACF by
Durbin-Levinson.

The result runs in any session, sandbox or CI runner with no provisioning
step — which matters far more for something meant to be handed to other people
and other agents than a marginal speed-up would. Covariance matrices in
mean-variance optimisation are small; an O(n³) elimination that is obvious to
audit beats a dependency.

**Generalises to:** for a shared toolkit, install friction is a real cost paid
by every user forever. Pay a small performance cost once instead.

## 6. Make the dangerous number impossible to miss

A DCF's terminal value routinely carries 70–90% of total value, so the
valuation is mostly a bet on a perpetuity assumption rather than on the
forecast anyone actually argued about.

So `dcf_enterprise_value` and `multistage_ddm` return `terminal_share`
alongside the value, and `fin.py dcf` prints a warning above 75%:

```
  value           1,598.58
  terminal_share  0.829864
  warning         83% of value sits in the terminal assumption;
                  the forecast is doing little of the work
```

Same instinct elsewhere: `portfolio` flags negative (short) weights; the ratio
helpers raise `ZeroDivisionError` **naming the ratio** instead of returning
`inf`; `growing_perpetuity_pv` refuses `g ≥ r` rather than returning a
negative number that looks like a price; `binomial_price` refuses a
risk-neutral probability outside `[0,1]` instead of returning an
arbitrage-laden value.

**The lesson:** surfacing where a number's weight sits is often worth more
than the number. A tool that silently returns a technically-correct answer
built on an unexamined assumption is a tool that will eventually be quoted in
a decision.

## 7. The model choice is the judgment; the formula is the easy part

The formulas are a semester of work to *derive* and an afternoon to
*implement*. What actually separates a working answer from a wrong one is
knowing which model is inapplicable:

- Closed forms assume **European** exercise → American needs a tree.
- Binomial trees **stop recombining** with discrete dividends → use a yield or
  handle dates explicitly (flagged on the 15.435x sheet, and a real trap).
- Analytic duration assumes **fixed** cash flows → callable bonds and MBS need
  effective duration, because the cash flows themselves move with rates.
- Mean-variance optimisation is brutally sensitive to expected returns →
  minimum-variance weights need none, which is why they survive estimation
  error.
- Arithmetic-average Asians have **no** closed form (a sum of lognormals isn't
  lognormal) → Monte Carlo, with the geometric case as a control.

This is the part worth writing down, and it is why the five
[`.claude/skills/`](../../.claude/skills/) files carry the "when NOT to use
this" guidance rather than just listing functions. A function list is
discoverable from the code; the judgment isn't.

## 8. The gambler's ruin is not a toy

It appears in 15.455x as a discrete-process exercise, and it is the most
directly transferable result in the curriculum. With a negative edge, ruin is
near-certain given enough rounds **regardless of starting capital** —
`gamblers_ruin_probability` shows how fast the probability collapses as the
edge turns against you.

That carries straight into position sizing and leverage: **survival is a
constraint, not a preference.** A strategy with positive expected value can
still ruin you if the path can reach zero, because there is no recovery from
an absorbing barrier. Any risk system that reasons only about expected return
is missing the boundary condition.

---

## What is deliberately not here

- **Credit risk and credit derivatives** — the Merton structural model, CDS,
  tranche correlation, prepayment. Mapped in
  [`curriculum.md`](curriculum.md), absent from `finlib`.
- **Short-rate trees and bonds with embedded options** — the effective
  duration/convexity hooks exist and take any pricing function, but no rate
  tree ships.
- **Barrier and lookback closed forms** — in/out parity is documented; the
  analytics are not implemented.
- **No-short-sales constrained optimisation** — needs a QP solver; the closed
  form is unconstrained and says so.

Named rather than left to be discovered, and the obvious next increment.
