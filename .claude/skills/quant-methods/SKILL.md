---
name: quant-methods
description: "The mathematical machinery under quantitative finance. Use for stochastic processes, random walks, Brownian motion, geometric Brownian motion, Ito's lemma and Ito calculus, the Black-Scholes-Merton PDE, Ornstein-Uhlenbeck and mean reversion, Euler-Maruyama SDE simulation, Monte Carlo methods, variance reduction and antithetic variates, confidence intervals on simulations, correlated random draws, the gambler's ruin, time series analysis (ARMA, AR, MA, random walk), ACF and PACF, stationarity and Box-Jenkins order identification, plus linear algebra and constrained optimisation (Lagrange multipliers, covariance matrices) for finance. Triggers on: 'simulate', 'Monte Carlo', 'stochastic process', 'Brownian motion', 'GBM', 'Ito', 'SDE', 'mean reversion', 'time series', 'ARMA', 'autocorrelation', 'random walk', 'confidence interval on a simulation', 'ruin probability'."
---

# Quantitative methods — processes, simulation, and time series

The bridge between discrete intuition and continuous models. A binomial tree
with the step shrinking to zero *becomes* geometric Brownian motion, which is
why the same option price falls out of a tree, a closed form, and a
simulation. When those three disagree, one of them has a bug — that triangle
is the most useful debugging tool in quantitative finance, and
`tools/finance/test_finlib.py` pins all three against each other.

Curriculum source: MITx 15.455x *Mathematical Methods for Quantitative
Finance*. Coursework from this course was cloned and read first-hand; see
`notes/mitx-finance/`.

## Use the engine

```python
import sys; sys.path.insert(0, "tools/finance")
from finlib import stochastic as st

st.gbm_paths(100, mu=0.05, sigma=0.2, T=1.0, steps=252, paths=1000, seed=42)
st.ornstein_uhlenbeck_paths(0.05, kappa=2.0, theta=0.03, sigma=0.01, T=5, steps=500)
st.euler_maruyama(x0, drift=lambda x, t: ..., diffusion=lambda x, t: ..., T=1, steps=1000)

mc = st.monte_carlo_european(100, 100, 0.05, 0.2, 1.0, paths=200_000, seed=1)
mc["price"], mc["stderr"], mc["ci_low"], mc["ci_high"]

st.simulate_arma(2000, ar=[0.7], ma=[0.3], seed=1)
st.acf(series, nlags=20)
st.pacf(series, nlags=20)
st.gamblers_ruin_probability(start=5, target=10, p_win=0.45)
```

## Rules that keep simulations honest

**Never report a simulated number without its error bar.** `stderr` and a 95%
interval come back from every estimator here. A Monte Carlo price with no
uncertainty attached is not a price, it is a number that happens to be near
one. Error falls as `1/√draws` — 4× the work halves it, which is also why
brute force gets expensive fast and variance reduction is worth the thought.

**With antithetic variates the pair mean is the sampling unit.** The two
halves of a `(z, −z)` pair are negatively correlated *on purpose* — that is
the mechanism. Computing the variance across the pooled payoffs as if they
were independent produces an invalid standard error. `monte_carlo_european`
reports `draws` (independent units) separately from `paths` (payoff
evaluations) for exactly this reason.

**The Ito correction is not optional.** `d(log S) = (μ − σ²/2)dt + σdW`, not
`μ dt`. Dropping the `−σ²/2` is the classic first mistake in simulating
prices, and it biases every path upward. `gbm_paths` steps the log exactly, so
it carries **no** discretisation bias in the terminal distribution however
large the step — for a payoff that depends only on `S_T`, draw it in one step
and don't waste work on a fine grid.

**Euler-Maruyama does carry discretisation error**, of order `√dt`. Use it
only when there is no exact solution, and shrink the step until the answer
stops moving.

**Seed everything.** Every sampler takes `seed` and uses its own
`random.Random`, so results reproduce and nothing disturbs global RNG state.
An unreproducible simulation cannot be debugged.

**Check a simulation against something you know.** The gambler's ruin has a
closed form (`gamblers_ruin_probability`); GBM has a known mean; Monte Carlo
has Black-Scholes. The test suite checks each against its analytic
counterpart — do the same before trusting a new simulator.

## Time series

`acf` and `pacf` (Durbin-Levinson) are the Box-Jenkins pair for identifying
order:

| Process | ACF | PACF |
|---|---|---|
| AR(p) | decays geometrically | **cuts off** after lag p |
| MA(q) | **cuts off** after lag q | decays |
| ARMA(p,q) | decays | decays |
| Random walk | ~1 and barely decaying | ~1 at lag 1 |

An ACF that stays near 1 means the series is non-stationary — difference it
before fitting anything. Fitting ARMA to a random walk in levels produces
confident, meaningless parameters. Rough significance band for "is this lag
real": `±3/√n`.

## The transferable lesson

The gambler's ruin is not a toy. With a negative edge, ruin is near-certain
given enough rounds *regardless of starting capital* — and the closed form
shows how fast the probability collapses as the edge turns against you. That
result carries directly into position sizing and leverage: survival is a
constraint, not a preference, and a strategy with positive expected value can
still ruin you if the path can hit zero first.

## Scope

Mathematical and simulation machinery. Not investment advice.
