"""Derivatives — forwards, futures, and option pricing, hedging, and Greeks.

Replicating portfolios and risk-neutral valuation on binomial trees,
Black-Scholes-Merton and Black-76 closed forms, the Greeks, delta-gamma
hedging, and the common exotics (binary, gap, exchange).

Curriculum anchors
------------------
* 15.415.2x — forwards, futures, options, and the no-arbitrage argument.
* 15.435x — the full modelling/valuation/hedging stack.

The identity set implemented here follows the 15.435x formula sheet that was
cloned and read for these notes (``notes/mitx-finance/``), cross-checked
against the standard closed forms. Every closed form has a numerical
counterpart in the test suite — the binomial tree is pinned to converge to
Black-Scholes, and the Monte Carlo estimator in ``stochastic.py`` is pinned to
agree with it inside its standard error. That agreement is the evidence these
are right; nothing here is asserted on the strength of the sheet alone.

**Scope.** These are valuation and risk mechanics. Nothing here is investment
advice, and no function knows anything about a real market.

Conventions
-----------
* ``r``, ``q`` (dividend yield) and ``sigma`` are **continuously compounded
  annual** decimals. ``T`` is in years.
* ``kind`` is ``"call"`` or ``"put"`` throughout.
* Cost of carry ``b`` generalises the underlying: ``b = r`` for a
  non-dividend stock, ``r - q`` with a dividend yield, ``0`` for a futures
  contract, ``r - r_foreign`` for FX. Pass ``q`` and it is derived for you.
"""

from __future__ import annotations

import math

__all__ = [
    "norm_cdf",
    "norm_pdf",
    "forward_price",
    "forward_price_with_income",
    "forward_value",
    "put_call_parity",
    "replicating_portfolio",
    "binomial_price",
    "black_scholes",
    "black_76",
    "greeks",
    "implied_volatility",
    "delta_gamma_hedge",
    "binary_option",
    "gap_option",
    "exchange_option",
    "numerical_gamma",
]

_SQRT_2 = math.sqrt(2.0)
_INV_SQRT_2PI = 1.0 / math.sqrt(2.0 * math.pi)


def norm_cdf(x: float) -> float:
    """Standard normal CDF via ``math.erf`` — no scipy needed."""
    return 0.5 * (1.0 + math.erf(x / _SQRT_2))


def norm_pdf(x: float) -> float:
    """Standard normal PDF."""
    return _INV_SQRT_2PI * math.exp(-0.5 * x * x)


def _check_kind(kind: str) -> str:
    k = kind.lower().strip()
    if k not in ("call", "put"):
        raise ValueError(f"kind must be 'call' or 'put', got {kind!r}")
    return k


# --------------------------------------------------------------------------
# Forwards and futures
# --------------------------------------------------------------------------


def forward_price(
    spot: float, r: float, T: float, q: float = 0.0, carry: float | None = None
) -> float:
    """Forward price under continuous carry: ``F = S e^{bT}``.

    ``b = r - q`` by default. The general rule from the course sheet: inflows
    associated with holding the underlying (dividends, convenience yield) are
    deducted from the carry, outflows (storage costs) are added.
    """
    b = carry if carry is not None else (r - q)
    return spot * math.exp(b * T)


def forward_price_with_income(
    spot: float, r: float, T: float, pv_income: float = 0.0, pv_cost: float = 0.0
) -> float:
    """Forward price with **discrete** income/costs: ``F = (S - PV_I + PV_C)e^{rT}``.

    Use this for a dividend-paying stock with known cash dividends, or a
    coupon-paying bond, where a continuous yield is the wrong model.
    """
    return (spot - pv_income + pv_cost) * math.exp(r * T)


def forward_value(
    forward_now: float, delivery_price: float, r: float, time_to_maturity: float
) -> float:
    """Value of an existing long forward: ``(F_t - K) e^{-r(T-t)}``.

    A forward is worth zero at inception because ``K`` is set to ``F_0``; it
    acquires value only as the forward price moves away from the locked-in
    delivery price.
    """
    return (forward_now - delivery_price) * math.exp(-r * time_to_maturity)


# --------------------------------------------------------------------------
# Parity
# --------------------------------------------------------------------------


def put_call_parity(
    *,
    call: float | None = None,
    put: float | None = None,
    spot: float | None = None,
    strike: float,
    r: float,
    T: float,
    q: float = 0.0,
) -> float:
    """Solve put-call parity for whichever leg is left as ``None``.

    ``C - P = S e^{-qT} - K e^{-rT}``

    Exactly one of ``call``, ``put``, ``spot`` must be omitted. Parity is a
    pure no-arbitrage identity — it holds regardless of which model prices the
    options, which is what makes it the first consistency check to run.
    """
    missing = [n for n, v in (("call", call), ("put", put), ("spot", spot)) if v is None]
    if len(missing) != 1:
        raise ValueError(
            f"supply exactly two of call/put/spot; missing {missing or 'nothing'}"
        )
    disc_k = strike * math.exp(-r * T)

    if missing[0] == "call":
        return put + spot * math.exp(-q * T) - disc_k
    if missing[0] == "put":
        return call - spot * math.exp(-q * T) + disc_k
    # spot
    return (call - put + disc_k) * math.exp(q * T)


# --------------------------------------------------------------------------
# Binomial / replication
# --------------------------------------------------------------------------


def replicating_portfolio(
    s_up: float, s_down: float, v_up: float, v_down: float, r: float, T: float
) -> tuple[float, float]:
    """One-step replication: returns ``(delta, bond)``.

    ``delta = (Vu - Vd) / (Su - Sd)``; ``bond = e^{-rT}(Vu - delta*Su)``.
    The option value is then ``delta * S0 + bond``.

    This is the argument the whole of option pricing rests on: if a portfolio
    of stock and bond reproduces the option's payoff in every state, it must
    cost the same as the option, or there is an arbitrage.
    """
    if s_up == s_down:
        raise ValueError("up and down states must differ")
    delta = (v_up - v_down) / (s_up - s_down)
    bond = math.exp(-r * T) * (v_up - delta * s_up)
    return delta, bond


def binomial_price(
    spot: float,
    strike: float,
    r: float,
    sigma: float,
    T: float,
    steps: int = 200,
    kind: str = "call",
    american: bool = False,
    q: float = 0.0,
    carry: float | None = None,
    is_futures: bool = False,
) -> float:
    """Cox-Ross-Rubinstein binomial price.

    Calibration: ``u = e^{sigma*sqrt(h)}``, ``d = 1/u``, and the risk-neutral
    probability ``q* = (e^{b h} - d) / (u - d)`` with ``b`` the cost of carry
    (``0`` for options on futures, hence ``q* = (1-d)/(u-d)``).

    Set ``american=True`` to allow early exercise — the tree is the natural
    home for that, since the closed forms assume European exercise. Note the
    standard result the test suite pins: an American **call** on a
    non-dividend-paying stock is never optimally exercised early, so its value
    equals the European one.
    """
    kind = _check_kind(kind)
    if steps <= 0:
        raise ValueError("steps must be positive")
    if T < 0:
        raise ValueError("T must be non-negative")
    if sigma < 0:
        raise ValueError("sigma must be non-negative")

    sign = 1.0 if kind == "call" else -1.0
    if T == 0 or sigma == 0:
        # Degenerate tree: fall back to the discounted deterministic payoff.
        b0 = 0.0 if is_futures else (carry if carry is not None else r - q)
        fwd = spot * math.exp(b0 * T)
        return math.exp(-r * T) * max(sign * (fwd - strike), 0.0)

    h = T / steps
    u = math.exp(sigma * math.sqrt(h))
    d = 1.0 / u
    b = 0.0 if is_futures else (carry if carry is not None else r - q)
    p = (math.exp(b * h) - d) / (u - d)
    if not (0.0 <= p <= 1.0):
        raise ValueError(
            f"risk-neutral probability {p:.4f} outside [0,1]: the tree is not "
            "arbitrage-free for these parameters (try more steps or check r/sigma)"
        )
    disc = math.exp(-r * h)

    # Terminal payoffs, then fold back.
    values = [
        max(sign * (spot * (u**j) * (d ** (steps - j)) - strike), 0.0)
        for j in range(steps + 1)
    ]
    for i in range(steps - 1, -1, -1):
        for j in range(i + 1):
            values[j] = disc * (p * values[j + 1] + (1 - p) * values[j])
            if american:
                node_spot = spot * (u**j) * (d ** (i - j))
                values[j] = max(values[j], sign * (node_spot - strike))
    return values[0]


# --------------------------------------------------------------------------
# Closed forms
# --------------------------------------------------------------------------


def _d1_d2(
    spot: float, strike: float, r: float, sigma: float, T: float, q: float
) -> tuple[float, float]:
    vol_t = sigma * math.sqrt(T)
    d1 = (math.log(spot / strike) + (r - q + 0.5 * sigma * sigma) * T) / vol_t
    return d1, d1 - vol_t


def black_scholes(
    spot: float,
    strike: float,
    r: float,
    sigma: float,
    T: float,
    kind: str = "call",
    q: float = 0.0,
) -> float:
    """Black-Scholes-Merton price with a continuous dividend yield ``q``.

    ``c = S e^{-qT} N(d1) - K e^{-rT} N(d2)``
    ``p = K e^{-rT} N(-d2) - S e^{-qT} N(-d1)``

    Setting ``q = r_foreign`` prices an FX option (Garman-Kohlhagen).

    >>> round(black_scholes(100, 100, 0.05, 0.20, 1.0), 4)
    10.4506
    """
    kind = _check_kind(kind)
    if spot <= 0 or strike <= 0:
        raise ValueError("spot and strike must be positive")
    if T < 0 or sigma < 0:
        raise ValueError("T and sigma must be non-negative")

    if T == 0 or sigma == 0:
        fwd = spot * math.exp((r - q) * T)
        sign = 1.0 if kind == "call" else -1.0
        return math.exp(-r * T) * max(sign * (fwd - strike), 0.0)

    d1, d2 = _d1_d2(spot, strike, r, sigma, T, q)
    df_s = spot * math.exp(-q * T)
    df_k = strike * math.exp(-r * T)
    if kind == "call":
        return df_s * norm_cdf(d1) - df_k * norm_cdf(d2)
    return df_k * norm_cdf(-d2) - df_s * norm_cdf(-d1)


def black_76(
    forward: float,
    strike: float,
    r: float,
    sigma: float,
    T: float,
    kind: str = "call",
) -> float:
    """Black-76 price for options on futures/forwards.

    ``c = e^{-rT}[F N(d1) - K N(d2)]``, with ``d1`` built from ``F/K`` and no
    carry term. Equivalent to Black-Scholes with ``q = r``.
    """
    kind = _check_kind(kind)
    if forward <= 0 or strike <= 0:
        raise ValueError("forward and strike must be positive")
    if T == 0 or sigma == 0:
        sign = 1.0 if kind == "call" else -1.0
        return math.exp(-r * T) * max(sign * (forward - strike), 0.0)

    vol_t = sigma * math.sqrt(T)
    d1 = (math.log(forward / strike) + 0.5 * sigma * sigma * T) / vol_t
    d2 = d1 - vol_t
    disc = math.exp(-r * T)
    if kind == "call":
        return disc * (forward * norm_cdf(d1) - strike * norm_cdf(d2))
    return disc * (strike * norm_cdf(-d2) - forward * norm_cdf(-d1))


def greeks(
    spot: float,
    strike: float,
    r: float,
    sigma: float,
    T: float,
    kind: str = "call",
    q: float = 0.0,
) -> dict[str, float]:
    """Analytic Black-Scholes Greeks.

    Returns ``delta``, ``gamma``, ``vega``, ``theta``, ``rho``.

    Units: ``vega`` is per 1.00 of volatility (divide by 100 for "per vol
    point"); ``theta`` is per year (divide by 365 for per-day); ``rho`` is per
    1.00 of rate.
    """
    kind = _check_kind(kind)
    if T <= 0 or sigma <= 0:
        raise ValueError("Greeks require positive T and sigma")

    d1, d2 = _d1_d2(spot, strike, r, sigma, T, q)
    sqrt_t = math.sqrt(T)
    disc_q = math.exp(-q * T)
    disc_r = math.exp(-r * T)
    pdf_d1 = norm_pdf(d1)

    gamma = disc_q * pdf_d1 / (spot * sigma * sqrt_t)
    vega = spot * disc_q * pdf_d1 * sqrt_t
    common_theta = -spot * disc_q * pdf_d1 * sigma / (2 * sqrt_t)

    if kind == "call":
        delta = disc_q * norm_cdf(d1)
        theta = common_theta + q * spot * disc_q * norm_cdf(d1) - r * strike * disc_r * norm_cdf(d2)
        rho = strike * T * disc_r * norm_cdf(d2)
    else:
        delta = -disc_q * norm_cdf(-d1)
        theta = common_theta - q * spot * disc_q * norm_cdf(-d1) + r * strike * disc_r * norm_cdf(-d2)
        rho = -strike * T * disc_r * norm_cdf(-d2)

    return {
        "delta": delta,
        "gamma": gamma,
        "vega": vega,
        "theta": theta,
        "rho": rho,
    }


def implied_volatility(
    price: float,
    spot: float,
    strike: float,
    r: float,
    T: float,
    kind: str = "call",
    q: float = 0.0,
    low: float = 1e-9,
    high: float = 5.0,
    tol: float = 1e-10,
    max_iter: int = 300,
) -> float:
    """Volatility that reproduces an observed option price, by bisection.

    Option value is strictly increasing in volatility, so bisection is safe
    where Newton can overshoot at very low vega (deep ITM/OTM).

    Raises ValueError if the price violates the no-arbitrage bounds, which is
    the honest answer — an unreachable price has no implied volatility.
    """
    kind = _check_kind(kind)
    lo_price = black_scholes(spot, strike, r, low, T, kind, q)
    hi_price = black_scholes(spot, strike, r, high, T, kind, q)
    if not (lo_price - 1e-12 <= price <= hi_price + 1e-12):
        raise ValueError(
            f"price {price} outside attainable range "
            f"[{lo_price:.6f}, {hi_price:.6f}] for vol in [{low}, {high}]"
        )

    for _ in range(max_iter):
        mid = 0.5 * (low + high)
        diff = black_scholes(spot, strike, r, mid, T, kind, q) - price
        if abs(diff) < tol or (high - low) < tol:
            return mid
        if diff > 0:
            high = mid
        else:
            low = mid
    return 0.5 * (low + high)


# --------------------------------------------------------------------------
# Hedging
# --------------------------------------------------------------------------


def delta_gamma_hedge(
    delta: float, gamma: float, hedge_delta: float, hedge_gamma: float
) -> tuple[float, float]:
    """Neutralise delta and gamma on one unit of a position.

    Stock has zero gamma, so a second option is needed to cancel gamma first,
    then stock cleans up the residual delta:

    ``N* = -gamma / hedge_gamma``  (units of the hedging option)
    ``N_S = -(delta + N* * hedge_delta)``  (shares)

    Returns ``(n_hedge_option, n_shares)``.
    """
    if hedge_gamma == 0:
        raise ValueError("hedging instrument must have non-zero gamma")
    n_option = -gamma / hedge_gamma
    n_shares = -(delta + n_option * hedge_delta)
    return n_option, n_shares


def numerical_gamma(price_fn, spot: float, ds: float) -> float:
    """Gamma by the mid-point difference used in the course:

    ``(V(S + ds/2) + V(S - ds/2) - 2 V(S)) / (ds/2)^2``.

    Useful when there is no closed form — exotics, or a tree/MC price.
    """
    if ds <= 0:
        raise ValueError("ds must be positive")
    half = ds / 2.0
    return (price_fn(spot + half) + price_fn(spot - half) - 2 * price_fn(spot)) / (
        half * half
    )


# --------------------------------------------------------------------------
# Exotics with closed forms
# --------------------------------------------------------------------------


def binary_option(
    spot: float,
    strike: float,
    r: float,
    sigma: float,
    T: float,
    kind: str = "call",
    style: str = "cash",
    q: float = 0.0,
    cash_payoff: float = 1.0,
) -> float:
    """Cash-or-nothing / asset-or-nothing binary.

    * cash-or-nothing call: pays ``cash_payoff`` if ``S_T > K``; price
      ``cash_payoff * e^{-rT} N(d2)``.
    * asset-or-nothing call: pays ``S_T`` if ``S_T > K``; price
      ``S e^{-qT} N(d1)``.

    The decomposition the course sheet pins:
    *asset-or-nothing call − K × cash-or-nothing call = vanilla call*. The
    test suite checks that identity numerically.
    """
    kind = _check_kind(kind)
    style = style.lower().strip()
    if style not in ("cash", "asset"):
        raise ValueError("style must be 'cash' or 'asset'")
    if T <= 0 or sigma <= 0:
        raise ValueError("binary pricing requires positive T and sigma")

    d1, d2 = _d1_d2(spot, strike, r, sigma, T, q)
    if style == "cash":
        n = norm_cdf(d2) if kind == "call" else norm_cdf(-d2)
        return cash_payoff * math.exp(-r * T) * n
    n = norm_cdf(d1) if kind == "call" else norm_cdf(-d1)
    return spot * math.exp(-q * T) * n


def gap_option(
    spot: float,
    strike_payoff: float,
    strike_trigger: float,
    r: float,
    sigma: float,
    T: float,
    kind: str = "call",
    q: float = 0.0,
) -> float:
    """Gap option — the trigger and the payoff strike differ.

    Gap call payoff: ``(S_T - K1) * 1{S_T > K2}``; the payoff can be negative,
    which is what separates it from a vanilla. Price:
    ``S e^{-qT} N(d1) - K1 e^{-rT} N(d2)`` with ``d1`` built from ``K2``.
    """
    kind = _check_kind(kind)
    if T <= 0 or sigma <= 0:
        raise ValueError("gap pricing requires positive T and sigma")

    d1, d2 = _d1_d2(spot, strike_trigger, r, sigma, T, q)
    df_s = spot * math.exp(-q * T)
    df_k = strike_payoff * math.exp(-r * T)
    if kind == "call":
        return df_s * norm_cdf(d1) - df_k * norm_cdf(d2)
    return df_k * norm_cdf(-d2) - df_s * norm_cdf(-d1)


def exchange_option(
    spot_a: float,
    spot_b: float,
    sigma_a: float,
    sigma_b: float,
    rho: float,
    T: float,
    q_a: float = 0.0,
    q_b: float = 0.0,
) -> float:
    """Margrabe: option to exchange asset B for asset A. Payoff ``(A_T - B_T)+``.

    The interest rate drops out — only the **spread volatility** matters:
    ``sigma = sqrt(sigma_a^2 + sigma_b^2 - 2 rho sigma_a sigma_b)``.

    With ``rho = 1`` and equal vols the spread vol is zero and the option is
    worth its intrinsic forward value.
    """
    if T <= 0:
        raise ValueError("T must be positive")
    if not -1.0 <= rho <= 1.0:
        raise ValueError("rho must lie in [-1, 1]")

    fwd_a = spot_a * math.exp(-q_a * T)
    fwd_b = spot_b * math.exp(-q_b * T)
    var = sigma_a**2 + sigma_b**2 - 2 * rho * sigma_a * sigma_b
    sigma = math.sqrt(max(var, 0.0))
    if sigma == 0:
        return max(fwd_a - fwd_b, 0.0)

    vol_t = sigma * math.sqrt(T)
    d1 = (math.log(fwd_a / fwd_b) + 0.5 * var * T) / vol_t
    d2 = d1 - vol_t
    return fwd_a * norm_cdf(d1) - fwd_b * norm_cdf(d2)
