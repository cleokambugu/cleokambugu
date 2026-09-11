---
name: financial-accounting
description: "Read, build and check financial statements. Use for the balance sheet equation, accrual versus cash accounting, the income statement, the cash flow statement (operating/investing/financing), how the three statements articulate and tie together, retained earnings roll-forward, revenue recognition, receivables and allowances, inventory costing (FIFO, LIFO, weighted average), depreciation policy (straight-line, declining balance), working capital, and ratio analysis (liquidity, leverage, profitability, efficiency, DuPont decomposition, cash conversion cycle, accruals quality). Triggers on: 'balance sheet', 'income statement', 'cash flow statement', 'financial statements', 'does this tie out', 'accruals', 'EBITDA', 'ROE', 'ROA', 'margin', 'working capital', 'FIFO', 'LIFO', 'depreciation', 'financial ratios', 'read these financials', 'build a three-statement model'."
---

# Financial accounting — articulation, accruals, and ratios

Two ideas carry most of the subject.

**The statements articulate.** The balance sheet balances, retained earnings
rolls forward through net income and dividends, and the cash flow statement
reconciles opening to closing cash. Three identities that must hold *at the
same time*. A model that breaks one is producing numbers that cannot describe
any real firm — and in a spreadsheet the break is usually silent.

**Accrual earnings are not cash.** Revenue is recognised when earned, not when
collected, so net income and operating cash flow diverge. That gap is
legitimate for a growing business and is also where aggressive recognition
hides. The number tells you where to look, not what you'll find.

Curriculum source: MITx 15.516x *Financial Accounting*. See
`notes/mitx-finance/` for provenance.

## Use the engine

```bash
# exits 1 if the statements don't tie — usable as a CI gate on a model
python tools/finance/fin.py articulate \
    --opening-cash 100 --closing-cash 140 --cfo 90 --cfi -40 --cff -10 \
    --opening-re 300 --closing-re 350 --net-income 70 --dividends 20 \
    --assets 1000 --liabilities 500 --equity 500

python tools/finance/fin.py ratios --net-income 120 --revenue 1000 \
    --assets 800 --equity 400 --debt 250 --cfo 150
```

```python
import sys; sys.path.insert(0, "tools/finance")
from finlib import accounting as acc

acc.articulation_check(...)                      # all three identities at once
acc.accruals(net_income, cash_from_operations)
acc.dupont_three_factor(ni, revenue, assets, equity)
acc.dupont_five_factor(ni, pretax, ebit, revenue, assets, equity)
acc.cogs_fifo(layers, units_sold)                # layers = [(units, unit_cost), ...]
acc.efficiency_ratios(...)                       # → DSO / DIO / DPO
acc.cash_conversion_cycle(dio, dso, dpo)
```

## Always run articulation before analysing

`articulation_check` returns per-identity residuals and names whichever one
broke. Make it the assertion at the end of any statement model you build or
ingest. `fin.py articulate` exits non-zero on failure so it drops straight
into CI.

Residuals point at the cause: a balance-sheet break with clean retained
earnings and cash usually means a misclassified balance; a retained-earnings
break means net income or dividends didn't post; a cash break means a
cash-flow section is miscategorised.

## Reading ratios without fooling yourself

**Decompose before you judge.** ROE alone conflates three different stories:

```
ROE = net margin × asset turnover × equity multiplier
```

A discounter and a luxury brand can post identical ROE with opposite margin
and turnover profiles, and a mediocre operator can match both purely on
leverage. `dupont_five_factor` splits further, separating tax and interest
burden from operating performance — the version to use when leverage or tax
position differs across comparables.

**Policy choices move reported numbers without moving the business.** With
rising prices, FIFO charges the oldest, cheapest units to COGS and so reports
*higher* income than LIFO, with a more current inventory balance; the test
suite pins that ordering. Accelerated depreciation front-loads expense against
straight line — but the **total** over the asset's life is identical. Only the
timing differs, which is the entire point of the choice. Never compare two
firms on a ratio without checking they use the same policy.

**A negative cash conversion cycle is a financing model.** `DIO + DSO − DPO`
below zero means suppliers fund the business — cash arrives from customers
before it leaves for inventory.

**Watch persistent accruals.** Net income consistently well above operating
cash flow means earnings are being booked far ahead of collection. Sometimes
that is growth in receivables; sometimes it is revenue recognition under
strain. It is a flag, not a verdict.

**End-of-period or average balances — pick one and say which.** `ROA` and
`ROE` here use closing balances. Averaging opening and closing is more
defensible when the balance sheet moved a lot during the year. Inconsistency
between comparables is the failure mode.

**A zero denominator is reported, not silently swallowed.** The ratio helpers
raise `ZeroDivisionError` naming the ratio, so a division by zero surfaces
instead of propagating a `0` or `inf` into a conclusion.

## Scope

Statement mechanics and analysis. This is not accounting, audit, tax or
investment advice, and it does not implement any specific GAAP or IFRS
standard — it implements the identities and ratios those standards report
under.
