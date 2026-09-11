# finance — a zero-dependency finance engine for agents

`finlib` implements the quantitative core of the **MITx Finance MicroMasters**
curriculum as plain Python, with a CLI front door and a verification suite
that checks every closed form against an independent route to the same number.

```
                    ┌─ tvm ──────────── present value, NPV, IRR, annuities
                    ├─ fixed_income ─── bonds, YTM, duration, curves, swaps
fin.py <command> ───┼─ equity ───────── DDM, DCF, WACC, capital structure     ──► text
   or               ├─ portfolio ────── mean-variance, CAPM, APT, Sharpe          or --json
import finlib       ├─ derivatives ──── forwards, trees, Black-Scholes, Greeks
                    ├─ stochastic ───── GBM, Monte Carlo, ARMA, ACF/PACF
                    ├─ accounting ───── articulation, accruals, ratios
                    └─ linalg ───────── the small dense algebra the optimiser needs
```

## No install step

Pure Python standard library. No numpy, no scipy, no pandas — the normal CDF
comes from `math.erf` and the matrix inverse is a Gauss-Jordan elimination.
That is deliberate: these functions are meant to run in any agent session,
sandbox or CI runner without provisioning anything.

```bash
python tools/finance/test_finlib.py      # 74 checks, no network, ~20s
python tools/finance/fin.py --help
```

## Front door

```bash
# price one option three ways and compare
python tools/finance/fin.py option --spot 100 --strike 100 --rate 0.05 \
    --vol 0.2 --years 1 --compare --greeks

# bond risk, stressed 100bp
python tools/finance/fin.py bond --coupon 0.05 --ytm 0.045 --years 10 --shock 100

# mean-variance frontier
python tools/finance/fin.py portfolio --returns 0.08,0.12,0.15 \
    --cov "0.04,0.01,0.02;0.01,0.09,0.015;0.02,0.015,0.16" --rf 0.03

# statement articulation — exits 1 if the three statements don't tie
python tools/finance/fin.py articulate --opening-cash 100 --closing-cash 140 \
    --cfo 90 --cfi -40 --cff -10 --opening-re 300 --closing-re 350 \
    --net-income 70 --dividends 20 --assets 1000 --liabilities 500 --equity 500
```

Every command takes `--json`. Full list: `fin.py --help`, then
`fin.py <command> -h`.

## As a library

```python
import sys; sys.path.insert(0, "tools/finance")
from finlib import derivatives, portfolio, accounting

derivatives.black_scholes(100, 100, 0.05, 0.20, 1.0, "call")   # 10.4506
portfolio.tangency_weights(mu, cov, risk_free=0.03)
accounting.articulation_check(...)
```

## As agent skills

Five skills in [`.claude/skills/`](../../.claude/skills/) load this engine and
carry the judgment that goes with it — when a model is the wrong choice, which
checks catch real errors, and where the standard mistakes are:

| Skill | Covers | Course |
|---|---|---|
| [`finance-valuation`](../../.claude/skills/finance-valuation/SKILL.md) | NPV/IRR, bonds, duration, DCF, WACC, capital structure | 15.415.1x, 15.415.2x |
| [`portfolio-theory`](../../.claude/skills/portfolio-theory/SKILL.md) | Mean-variance, CAPM, APT, performance | 15.415.2x, 15.455x |
| [`derivatives-pricing`](../../.claude/skills/derivatives-pricing/SKILL.md) | Forwards, trees, Black-Scholes, Greeks, hedging | 15.435x |
| [`quant-methods`](../../.claude/skills/quant-methods/SKILL.md) | Stochastic processes, Monte Carlo, time series | 15.455x |
| [`financial-accounting`](../../.claude/skills/financial-accounting/SKILL.md) | Statements, articulation, accruals, ratios | 15.516x |

## How it is verified

Nothing here asks to be taken on trust. Where a closed form exists, the test
suite checks it against a different route to the same number:

| Claim | Checked against |
|---|---|
| Black-Scholes | 3000-step binomial tree **and** Monte Carlo inside its own 95% CI |
| Analytic Greeks | central-difference numerical differentiation |
| Duration & convexity | numerically re-pricing the bond; error confirmed to be O(dy²) by halving the step |
| Risk-neutral valuation | the replicating portfolio, priced independently |
| Gambler's ruin simulation | its closed-form probability |
| Bootstrapped spot curve | the par curve it came from |
| DuPont decompositions | ROE computed directly |
| Min-variance portfolio | no frontier portfolio achieves lower variance |
| MM Proposition II | WACC invariant to leverage without taxes |
| Binary decomposition | `asset-or-nothing − K × cash-or-nothing == vanilla call` |

`python tools/finance/test_finlib.py` — **74 checks, all passing.**

Two bugs surfaced this way while building. The useful one: the Monte Carlo
standard error was being computed across pooled antithetic payoffs as though
they were independent. They are negatively correlated on purpose, so the
reported error bar was invalid. The estimator now treats each `(z, −z)` pair
mean as the sampling unit and reports `draws` separately from `paths`. A
simulator that reports a confident wrong error bar is worse than one that
reports none.

## Provenance and scope

Curriculum source and what was actually read first-hand versus assembled from
search snippets: [`notes/mitx-finance/`](../../notes/mitx-finance/). MIT's own
hosts were unreachable from the sandbox this was built in, and the notes say
so rather than implying otherwise.

**This is analysis machinery, not investment advice.** No function here knows
anything about a real market or a real security. Consistent with the
[portfolio's](../../PORTFOLIO.md) standing position on trading work: research
in paper or synthetic environments, with no performance claim.
