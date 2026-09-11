"""finlib — a zero-dependency finance engine for agents.

Pure Python standard library: no numpy, no scipy, no pandas, no install step.
That is deliberate. These functions are meant to be callable from any agent
session, sandbox, or CI runner without provisioning anything, so the normal
CDF comes from :func:`math.erf` and the matrix inverse is a Gauss-Jordan
elimination rather than a dependency.

Modules
-------
``tvm``            present value, NPV, IRR, annuities, rate conversions
``fixed_income``   bond pricing, YTM, duration/convexity, curves, swap rates
``equity``         DDM, DCF, WACC, capital structure, capital budgeting
``portfolio``      mean-variance optimisation, CAPM, APT, performance metrics
``derivatives``    forwards, binomial trees, Black-Scholes, Greeks, hedging
``stochastic``     Brownian motion, GBM, Monte Carlo, ARMA, ACF/PACF
``accounting``     statement articulation, accruals, ratio analysis
``linalg``         the small dense linear algebra the optimiser needs

Provenance and scope
--------------------
The curriculum this follows is the MITx Finance MicroMasters (15.415.1x,
15.415.2x, 15.516x, 15.455x, 15.435x). See ``notes/mitx-finance/`` for what
was read first-hand versus what came from search snippets — MIT's own hosts
were unreachable from the sandbox this was built in, and the notes say so.

Every identity implemented here is standard and independently checkable, and
``test_finlib.py`` checks them: closed forms against numerical
differentiation, trees against closed forms, Monte Carlo against both inside
its own confidence interval.

**This is analysis machinery, not investment advice.** No function here knows
anything about a real market, and none of them should be read as a
recommendation to trade.
"""

from __future__ import annotations

from . import (
    accounting,
    derivatives,
    equity,
    fixed_income,
    linalg,
    portfolio,
    stochastic,
    tvm,
)

__version__ = "1.0.0"

__all__ = [
    "accounting",
    "derivatives",
    "equity",
    "fixed_income",
    "linalg",
    "portfolio",
    "stochastic",
    "tvm",
    "__version__",
]
