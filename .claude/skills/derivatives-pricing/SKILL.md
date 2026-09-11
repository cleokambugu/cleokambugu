---
name: derivatives-pricing
description: "Price and hedge derivatives. Use for forwards, futures, cost of carry, put-call parity, binomial trees, replicating portfolios, risk-neutral valuation, Black-Scholes, Black-76 futures options, FX options, American early exercise, the Greeks (delta, gamma, vega, theta, rho), implied volatility, delta and delta-gamma hedging, volatility smiles, and exotics (binary/digital, gap, exchange/Margrabe, Asian, barrier, lookback). Triggers on: 'option price', 'call', 'put', 'strike', 'Black-Scholes', 'binomial tree', 'Greeks', 'delta hedge', 'implied vol', 'forward price', 'futures', 'swap rate', 'payoff diagram', 'straddle', 'spread', 'how do I hedge this'. Do NOT use for portfolio allocation (use portfolio-theory) or company valuation (use finance-valuation)."
---

# Derivatives — pricing, Greeks, and hedging

One argument underneath all of it: **if a portfolio of traded assets
reproduces a payoff in every future state, it must cost what the payoff costs,
or there is an arbitrage.** Replication gives the price; the risk-neutral
probability is that same argument rewritten as an expectation. Neither claims
the world is risk-neutral — it is a change of measure, not a belief.

Curriculum source: MITx 15.435x *Derivatives Markets: Advanced Modeling and
Strategies* and the derivatives half of 15.415.2x. The 15.435x formula sheet
was cloned and read first-hand; see `notes/mitx-finance/`.

## Use the engine

```bash
# price by all three routes at once — they should agree
python tools/finance/fin.py option --spot 100 --strike 100 --rate 0.05 \
    --vol 0.2 --years 1 --compare --greeks

python tools/finance/fin.py greeks     --spot 100 --strike 100 --rate 0.05 --vol 0.2 --years 1
python tools/finance/fin.py impliedvol --price 10.45 --spot 100 --strike 100 --rate 0.05 --years 1 --vol 0.2
python tools/finance/fin.py hedge      --spot 100 --strike 100 --rate 0.05 --vol 0.2 --years 1 \
    --hedge-strike 110 --hedge-years 0.5
python tools/finance/fin.py option --spot 100 --strike 100 --rate 0.05 --vol 0.2 \
    --years 1 --model binomial --american --kind put
```

```python
import sys; sys.path.insert(0, "tools/finance")
from finlib import derivatives as d

d.black_scholes(100, 100, 0.05, 0.20, 1.0, "call")      # 10.4506
d.binomial_price(100, 100, 0.05, 0.20, 1.0, steps=500, kind="put", american=True)
d.greeks(100, 100, 0.05, 0.20, 1.0, "call")
d.delta_gamma_hedge(pos_delta, pos_gamma, hedge_delta, hedge_gamma)
```

## Choosing a model

| Situation | Model |
|---|---|
| European, lognormal | `black_scholes` — closed form, instant |
| Option on a future | `black_76` (equivalently `q = r`) |
| FX option | `black_scholes` with `q = r_foreign` |
| **American / early exercise** | `binomial_price(american=True)` — closed forms assume European |
| Discrete known dividends | `binomial_price`, or `forward_price_with_income` |
| Path-dependent (Asian, lookback) | Monte Carlo — `stochastic.monte_carlo_asian` |
| Binary, gap, exchange | closed forms in this module |
| Barrier | in/out parity: `c = c_in + c_out`, then price the easier leg |

## Rules that catch real errors

**Check parity before anything else.** `C - P = S e^{-qT} - K e^{-rT}` holds
whatever model produced the prices — it is pure no-arbitrage. If your call and
put disagree with parity, the bug is upstream of the model.
`put_call_parity` solves for whichever leg you omit.

**An American call on a non-dividend stock is never exercised early**, so it
equals the European. If your tree says otherwise, the tree is wrong — the test
suite pins this. American *puts* genuinely do carry an early-exercise premium.

**The binomial tree does not recombine with discrete dividends.** Use a yield,
or handle the dividend dates explicitly. Silently recombining is a real and
common error.

**Greeks units bite.** `vega` is per 1.00 of vol (divide by 100 for a vol
point); `theta` is per year (divide by 365 for a day); `rho` is per 1.00 of
rate. `fin.py greeks` prints the per-day and per-point conversions.

**Delta hedging is not gamma hedging.** Stock has zero gamma, so a
delta-neutral book still loses on a large move. To neutralise both you need a
second option: `N* = -Γ/Γ*`, then shares clean up the residual delta
(`delta_gamma_hedge`). A delta hedge is only instantaneous — it needs
rebalancing, and the rebalancing cost is the option premium in disguise.

**Implied volatility is a quote convention, not a forecast.** It is the number
that makes Black-Scholes reproduce a price. That the smile exists at all is
evidence the lognormal assumption is wrong: real returns have fat tails and
jumps. Low strike/spot → Black-Scholes *under*prices; high → it *over*prices.

**Monte Carlo without a standard error is not a price.** Every simulator here
returns `stderr` and a 95% interval. Error falls as `1/√draws`, so 4× the work
halves it. Use antithetic variates for monotone payoffs — and note the pair
mean, not the individual payoff, is the independent sampling unit.

## Sanity checks worth running

Cheap, and they catch most mistakes:

- Put-call parity holds.
- Tree → closed form as `steps` grows (3000 steps lands within 0.005).
- Monte Carlo brackets the closed form inside its own CI.
- `asset-or-nothing − K × cash-or-nothing == vanilla call`.
- Exchange option with `ρ = 1` and equal vols collapses to intrinsic value.
- Asian < otherwise-identical European (averaging kills variance).

All six are in `tools/finance/test_finlib.py`.

## Scope

Pricing and risk mechanics only. Nothing here is investment advice, no
function knows any real market, and none of this is a trading
recommendation — consistent with the repo's standing position that trading
work is research in paper or synthetic environments.
