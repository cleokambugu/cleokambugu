---
name: finance-valuation
description: "Value cash flows, bonds, projects and companies. Use for present value, NPV, IRR, payback, annuities and perpetuities; bond pricing, yield to maturity, duration, convexity, spot/forward curves, bootstrapping and par swap rates; dividend discount and DCF valuation, terminal value, WACC, cost of equity, CAPM-based discount rates, capital budgeting, project ranking, unequal project lives, capital structure and Modigliani-Miller, levering and unlevering beta. Triggers on: 'what is this worth', 'value this company', 'NPV', 'IRR', 'discount rate', 'DCF', 'bond price', 'yield', 'duration', 'WACC', 'cost of capital', 'terminal value', 'should we do this project'. Do NOT use for option/derivative pricing (use derivatives-pricing) or portfolio allocation (use portfolio-theory)."
---

# Valuation — cash flows, fixed income, and the firm

Everything here is one idea applied repeatedly: **a claim is worth the present
value of the cash it produces, discounted at a rate that reflects its risk.**
Bonds, projects and companies differ only in how confident you can be about
the cash and the rate.

Curriculum source: MITx 15.415.1x *Foundations of Modern Finance I* and the
corporate-finance half of 15.415.2x. See `notes/mitx-finance/` for provenance.

## Use the engine, don't re-derive

Zero dependencies, pure stdlib, verified by `tools/finance/test_finlib.py`:

```bash
python tools/finance/fin.py npv  --rate 0.10 --flows -100,60,60
python tools/finance/fin.py irr  --flows -1000,400,400,400
python tools/finance/fin.py bond --coupon 0.05 --ytm 0.045 --years 10 --shock 100
python tools/finance/fin.py ytm  --price 104 --coupon 0.05 --years 10
python tools/finance/fin.py dcf  --flows 100,110,120 --rate 0.10 --growth 0.03 --debt 400
python tools/finance/fin.py ddm  --dividends 1.0,1.2,1.4 --rate 0.10 --growth 0.03
python tools/finance/fin.py wacc --equity 600 --debt 400 --cost-equity 0.12 --cost-debt 0.06 --tax 0.25
python tools/finance/fin.py swap --discount-factors 0.97,0.94,0.91,0.88
```

Add `--json` to any command for machine-readable output.

From Python:

```python
import sys; sys.path.insert(0, "tools/finance")
from finlib import tvm, fixed_income, equity

tvm.npv(0.10, [-100, 60, 60])
fixed_income.modified_duration(100, 0.05, 0.045, 10, freq=2)
equity.dcf_enterprise_value([100, 110, 120], 0.10, 0.02)
```

## What to reach for

| Question | Call |
|---|---|
| Worth doing? | `tvm.npv` — and rank by NPV, not IRR |
| Return on a stream | `tvm.irr` (watch for multiple roots) |
| Projects of different lengths | `equity.equivalent_annual_annuity` |
| Capital rationed | `equity.profitability_index` |
| Bond price / yield | `fixed_income.bond_price` / `bond_ytm` |
| Rate risk | `modified_duration` + `convexity` |
| Callable bond, MBS | `effective_duration` (cash flows move with rates) |
| Hedge a rate position | `hedge_ratio_duration` (match dollar duration) |
| Zero curve from par bonds | `bootstrap_spot_curve` |
| Swap fixed rate | `par_swap_rate` |
| Company value | `equity.dcf_enterprise_value` → `equity_value_from_enterprise` |
| Discount rate | `equity.wacc`, with `portfolio.capm_expected_return` for the equity leg |
| Peer betas | `unlever_beta` → average → `relever_beta` |

## The judgment that matters more than the arithmetic

**Rank by NPV, not IRR.** IRR is a rate, so it silently prefers small projects
and breaks outright when the cash-flow sign flips more than once (multiple
IRRs) or never flips (none exists). `tvm.irr` raises rather than guessing.

**The terminal value is usually the valuation.** `dcf_enterprise_value` and
`multistage_ddm` both return `terminal_share` for this reason. Above ~75%, the
explicit forecast is decoration — the number is a bet on the perpetuity
assumption, and the sensitivity to `g` is where the scrutiny belongs. `fin.py
dcf` prints a warning when it crosses that line.

**Gordon growth requires `r > g`, permanently.** A growth rate at or above the
discount rate implies infinite value, which is why the function raises instead
of returning a number. If your model needs `g ≥ r`, the model is wrong, not
the constraint.

**Use market values for WACC weights, never book.** This is the most common
way a cost of capital comes out wrong.

**Match the cash flow to the rate.** FCFF discounts at WACC and gives
enterprise value; FCFE discounts at the cost of equity and gives equity value
directly. Crossing them silently double-counts or ignores leverage.

**Duration alone always understates a bond's price** — the price/yield curve
is convex, so add the convexity term for moves beyond a few basis points.
`price_change_approx` does both; the test suite pins the improvement.

**MM is a baseline, not a recommendation.** Without taxes, WACC is invariant
to leverage — the cost of equity rises exactly enough to offset cheaper debt
(`mm_cost_of_equity`, pinned in the tests). Value from leverage has to come
from a friction: taxes, distress costs, signalling. Name the friction.

## Scope

Valuation mechanics. Not investment advice, and no function here knows
anything about a real market or a real security.
