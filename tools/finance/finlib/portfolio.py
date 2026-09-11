"""Portfolio theory — mean-variance optimisation, CAPM, APT, and performance.

Curriculum anchors
------------------
* 15.415.1x — risk analysis, the Arbitrage Pricing Theory, and the Efficient
  Market Hypothesis.
* 15.415.2x — portfolio theory and the Capital Asset Pricing Model.
* 15.455x — the linear algebra and constrained optimisation underneath them
  (covariance matrices, Lagrange multipliers, quadratic programming).

The optimiser here solves the **unconstrained** (long/short allowed, fully
invested) problem in closed form via Lagrange multipliers. That is the
textbook frontier. Adding a no-short-sales constraint turns it into a
quadratic program with inequality constraints, which has no closed form —
:func:`efficient_frontier` will happily return negative weights, and that is
the correct answer to the problem as posed, not a bug. Read the weights before
using them.

**Scope.** Valuation and risk mechanics only. Expected returns are an *input*
here and the hardest thing to estimate in practice; garbage in, confidently
optimised garbage out. Nothing here is investment advice.
"""

from __future__ import annotations

import math

from .linalg import Matrix, Vector, dot, inverse, matvec

__all__ = [
    "portfolio_return",
    "portfolio_variance",
    "portfolio_std",
    "global_min_variance_weights",
    "tangency_weights",
    "frontier_weights",
    "efficient_frontier",
    "frontier_constants",
    "capm_expected_return",
    "apt_expected_return",
    "beta_from_cov",
    "sharpe_ratio",
    "treynor_ratio",
    "jensen_alpha",
    "information_ratio",
]


def _normalise(v: Vector) -> Vector:
    total = sum(v)
    if abs(total) < 1e-14:
        raise ValueError("weights sum to zero; portfolio is undefined")
    return [x / total for x in v]


def portfolio_return(weights: Vector, expected_returns: Vector) -> float:
    """``w' mu``."""
    return dot(weights, expected_returns)


def portfolio_variance(weights: Vector, cov: Matrix) -> float:
    """``w' Sigma w``."""
    return dot(weights, matvec(cov, weights))


def portfolio_std(weights: Vector, cov: Matrix) -> float:
    var = portfolio_variance(weights, cov)
    if var < 0:
        # Only reachable with a covariance matrix that is not PSD.
        raise ValueError(
            f"negative portfolio variance ({var:.3e}); "
            "the covariance matrix is not positive semi-definite"
        )
    return math.sqrt(var)


def frontier_constants(expected_returns: Vector, cov: Matrix) -> dict[str, float]:
    """The efficient-frontier scalars ``A``, ``B``, ``C``, ``D``.

    ``A = 1' S^-1 1``, ``B = 1' S^-1 mu``, ``C = mu' S^-1 mu``, ``D = AC - B^2``.
    Every closed form below is built from these.
    """
    n = len(expected_returns)
    if len(cov) != n:
        raise ValueError("expected_returns and cov disagree on the number of assets")
    inv = inverse(cov)
    ones = [1.0] * n
    inv_ones = matvec(inv, ones)
    inv_mu = matvec(inv, expected_returns)

    a = dot(ones, inv_ones)
    b = dot(ones, inv_mu)
    c = dot(expected_returns, inv_mu)
    d = a * c - b * b
    if abs(d) < 1e-14:
        raise ValueError(
            "degenerate frontier (D ~ 0): all assets have the same expected return, "
            "so no risk/return trade-off exists"
        )
    return {"A": a, "B": b, "C": c, "D": d}


def global_min_variance_weights(cov: Matrix) -> Vector:
    """Minimum-variance portfolio: ``w = S^-1 1 / (1' S^-1 1)``.

    Needs no expected returns at all — which is why it is the one frontier
    portfolio that is robust to the estimation error that wrecks the rest.
    """
    n = len(cov)
    inv_ones = matvec(inverse(cov), [1.0] * n)
    return _normalise(inv_ones)


def tangency_weights(
    expected_returns: Vector, cov: Matrix, risk_free: float
) -> Vector:
    """Maximum-Sharpe portfolio: ``w ∝ S^-1 (mu - rf 1)``, rescaled to sum to 1.

    Under CAPM assumptions this is the market portfolio, and every investor
    holds it levered up or down against the risk-free asset — two-fund
    separation.
    """
    excess = [m - risk_free for m in expected_returns]
    return _normalise(matvec(inverse(cov), excess))


def frontier_weights(
    expected_returns: Vector, cov: Matrix, target_return: float
) -> Vector:
    """Minimum-variance weights achieving ``target_return``, fully invested.

    Closed-form solution of
    ``min w'Sw  s.t.  w'mu = target,  w'1 = 1``
    by Lagrange multipliers. Short sales are permitted.
    """
    k = frontier_constants(expected_returns, cov)
    a, b, c, d = k["A"], k["B"], k["C"], k["D"]
    inv = inverse(cov)
    n = len(expected_returns)
    inv_ones = matvec(inv, [1.0] * n)
    inv_mu = matvec(inv, expected_returns)

    lam = (c - b * target_return) / d
    gam = (a * target_return - b) / d
    return [lam * x + gam * y for x, y in zip(inv_ones, inv_mu)]


def efficient_frontier(
    expected_returns: Vector, cov: Matrix, points: int = 25
) -> list[dict[str, object]]:
    """Sample the frontier from the minimum-variance point upward.

    Returns dicts with ``return``, ``std`` and ``weights``. The lower branch
    (below the minimum-variance return) is dominated and is excluded — those
    portfolios take the same risk for less return.
    """
    if points < 2:
        raise ValueError("need at least two points")
    k = frontier_constants(expected_returns, cov)
    mv_return = k["B"] / k["A"]
    top = max(expected_returns)
    if top <= mv_return:
        top = mv_return + abs(mv_return) * 0.5 + 0.01

    out = []
    for i in range(points):
        target = mv_return + (top - mv_return) * i / (points - 1)
        w = frontier_weights(expected_returns, cov, target)
        out.append(
            {"return": target, "std": portfolio_std(w, cov), "weights": w}
        )
    return out


def beta_from_cov(asset_market_cov: float, market_variance: float) -> float:
    """``beta = Cov(i, m) / Var(m)``."""
    if market_variance == 0:
        raise ValueError("market variance is zero")
    return asset_market_cov / market_variance


def capm_expected_return(
    risk_free: float, beta: float, market_premium: float
) -> float:
    """Security market line: ``E[r] = rf + beta * (E[rm] - rf)``.

    ``market_premium`` is already the **excess** return of the market.
    """
    return risk_free + beta * market_premium


def apt_expected_return(
    risk_free: float, betas: Vector, factor_premiums: Vector
) -> float:
    """Multi-factor APT: ``E[r] = rf + sum_k beta_k * lambda_k``.

    CAPM is the one-factor special case. APT rests on no-arbitrage across a
    factor structure rather than on mean-variance preferences, so it says
    nothing about *which* factors belong in the model — that is an empirical
    question the theory deliberately leaves open.
    """
    if len(betas) != len(factor_premiums):
        raise ValueError("betas and factor_premiums must be the same length")
    return risk_free + dot(betas, factor_premiums)


def sharpe_ratio(
    portfolio_ret: float, risk_free: float, portfolio_sd: float
) -> float:
    """Excess return per unit of **total** risk."""
    if portfolio_sd <= 0:
        raise ValueError("standard deviation must be positive")
    return (portfolio_ret - risk_free) / portfolio_sd


def treynor_ratio(portfolio_ret: float, risk_free: float, beta: float) -> float:
    """Excess return per unit of **systematic** risk.

    Right measure when the portfolio is one sleeve of a diversified whole, so
    its idiosyncratic risk is already diversified away.
    """
    if beta == 0:
        raise ValueError("beta is zero")
    return (portfolio_ret - risk_free) / beta


def jensen_alpha(
    portfolio_ret: float, risk_free: float, beta: float, market_ret: float
) -> float:
    """Return in excess of the CAPM benchmark for the portfolio's beta."""
    return portfolio_ret - capm_expected_return(
        risk_free, beta, market_ret - risk_free
    )


def information_ratio(
    active_returns: Vector, sample: bool = True
) -> float:
    """Mean active return divided by tracking error.

    ``active_returns`` is the per-period series of portfolio-minus-benchmark
    returns.
    """
    n = len(active_returns)
    if n < 2:
        raise ValueError("need at least two observations")
    mean = sum(active_returns) / n
    denom = (n - 1) if sample else n
    var = sum((x - mean) ** 2 for x in active_returns) / denom
    te = math.sqrt(var)
    if te == 0:
        raise ValueError("tracking error is zero")
    return mean / te
