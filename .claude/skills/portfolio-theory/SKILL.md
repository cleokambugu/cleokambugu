---
name: portfolio-theory
description: "Build and assess portfolios. Use for mean-variance optimisation, the efficient frontier, minimum-variance and tangency/max-Sharpe portfolios, diversification, covariance and correlation matrices, two-fund separation, the Capital Asset Pricing Model, beta, the security market line, Arbitrage Pricing Theory and multi-factor models, the Efficient Market Hypothesis, and performance measurement (Sharpe, Treynor, Jensen's alpha, information ratio, tracking error). Triggers on: 'asset allocation', 'optimal weights', 'efficient frontier', 'diversify', 'CAPM', 'beta', 'expected return', 'risk-adjusted return', 'Sharpe ratio', 'alpha', 'factor model', 'how should I weight these'. Do NOT use for option pricing (use derivatives-pricing) or single-company valuation (use finance-valuation)."
---

# Portfolio theory — risk, return, and what diversification does

The core result: **only risk you cannot diversify away earns a return.** Split
an asset's risk into a systematic part (moves with everything else) and an
idiosyncratic part (its own). The second is free to remove by holding more
names, so the market pays nothing for bearing it. Everything below is that
sentence made precise.

Curriculum source: MITx 15.415.2x (portfolio theory and CAPM), 15.415.1x
(risk, APT, EMH), and the optimisation half of 15.455x. See
`notes/mitx-finance/`.

## Use the engine

```bash
python tools/finance/fin.py portfolio \
    --returns 0.08,0.12,0.15 \
    --cov "0.04,0.01,0.02;0.01,0.09,0.015;0.02,0.015,0.16" \
    --rf 0.03 --target 0.13

python tools/finance/fin.py capm --rf 0.03 --beta 1.2 --premium 0.05 --realised 0.11
```

```python
import sys; sys.path.insert(0, "tools/finance")
from finlib import portfolio as pf, linalg

cov = linalg.cov_from_returns([asset_a_returns, asset_b_returns])  # from history
pf.global_min_variance_weights(cov)          # needs no expected returns at all
pf.tangency_weights(mu, cov, rf)             # max Sharpe
pf.frontier_weights(mu, cov, target_return)  # min variance at a target
pf.efficient_frontier(mu, cov, points=25)
```

## What to reach for

| Question | Call |
|---|---|
| Lowest-risk mix | `global_min_variance_weights` |
| Best risk-adjusted mix | `tangency_weights` (max Sharpe) |
| Hit a return target | `frontier_weights` |
| Trace the trade-off | `efficient_frontier` |
| Covariance from history | `linalg.cov_from_returns` |
| Required return | `capm_expected_return` / `apt_expected_return` |
| Did it actually do well? | `sharpe_ratio`, `treynor_ratio`, `jensen_alpha`, `information_ratio` |

## The judgment that matters

**Expected returns are the weak link, not the optimiser.** Mean-variance
optimisation is exquisitely sensitive to `mu` — small estimation errors
produce wildly concentrated, confidently wrong weights. This is why
`global_min_variance_weights` is worth knowing: it uses **only** the
covariance matrix, and covariance is estimated far more reliably than means.
Garbage in, confidently optimised garbage out.

**These weights can go short.** The closed form solves the *unconstrained*
problem, so negative weights are real short positions, not a bug. Adding a
no-short-sales constraint turns it into a quadratic program with inequality
constraints and no closed form. `fin.py portfolio` flags negative weights;
read them before acting.

**Sharpe or Treynor depends on the portfolio's role.** Sharpe divides by total
risk — right when this *is* the whole portfolio. Treynor divides by beta —
right when it is one sleeve of something already diversified, so its
idiosyncratic risk is someone else's problem. Using the wrong one flatters or
punishes a manager for something they don't control.

**Alpha is only alpha relative to a model.** `jensen_alpha` measures return
above the CAPM line for that beta. Under a multi-factor model, much of what
looks like alpha turns out to be a factor loading in disguise — `apt_expected_return`
takes as many factors as you have. APT deliberately does not say *which*
factors belong; that is empirical, not theoretical.

**CAPM is the one-factor special case of APT** — the test suite pins the
identity. They rest on different arguments, though: CAPM on mean-variance
preferences and market clearing, APT on no-arbitrage across a factor
structure.

**EMH is a claim about how hard it is to beat prices, not that prices are
right.** Its practical use here is a prior: treat a strategy that appears to
generate large risk-adjusted returns as most likely a modelling error, a
missing risk factor, or a look-ahead bug — until it survives honest
out-of-sample testing.

**A degenerate frontier means your inputs are degenerate.** If all expected
returns are equal there is no risk/return trade-off; `frontier_constants`
raises rather than dividing by ~0. Perfectly correlated assets make the
covariance matrix singular and `linalg.inverse` says so by name.

## Scope

Allocation mechanics. Not investment advice, and none of these functions knows
any real market or security.
