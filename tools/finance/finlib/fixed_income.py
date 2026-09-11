"""Fixed income — pricing, yield, and interest-rate risk.

Bond pricing and YTM, the duration/convexity risk toolkit, spot-curve
bootstrapping and forward rates, and the par swap rate.

Curriculum anchors
------------------
* 15.415.1x — valuation of fixed income securities.
* 15.435x — duration, convexity, hedging with forwards, and swap pricing.
  The duration/convexity and swap identities here follow the formula set in
  the course cheat sheet read for these notes (see ``notes/mitx-finance/``);
  they are also standard textbook results (Hull, *Options, Futures and Other
  Derivatives*), so the identities are checkable independently of that sheet.

Conventions
-----------
* ``ytm`` and ``coupon_rate`` are **annual** decimals; ``freq`` is coupons per
  year. Internally everything works in periods and converts back to years.
* Duration and convexity are reported **in years** (convexity in years^2).
"""

from __future__ import annotations

import math

__all__ = [
    "bond_cashflows",
    "bond_price",
    "bond_ytm",
    "macaulay_duration",
    "modified_duration",
    "dollar_duration",
    "convexity",
    "dollar_convexity",
    "effective_duration",
    "effective_convexity",
    "price_change_approx",
    "portfolio_modified_duration",
    "discount_factors_from_spot",
    "forward_rate",
    "bootstrap_spot_curve",
    "par_swap_rate",
    "hedge_ratio_duration",
]


def bond_cashflows(
    face: float, coupon_rate: float, years: float, freq: int = 2
) -> list[tuple[int, float]]:
    """``(period_index, cash_flow)`` pairs for a plain vanilla coupon bond.

    Period indices run 1..N where ``N = years * freq``. The final period
    carries the coupon plus the face value.
    """
    if freq <= 0:
        raise ValueError("freq must be positive")
    n = int(round(years * freq))
    if n <= 0:
        raise ValueError("bond must have at least one period to maturity")
    coupon = face * coupon_rate / freq
    flows = [(t, coupon) for t in range(1, n + 1)]
    flows[-1] = (n, coupon + face)
    return flows


def bond_price(
    face: float, coupon_rate: float, ytm: float, years: float, freq: int = 2
) -> float:
    """Price of a coupon bond at a flat yield to maturity.

    >>> round(bond_price(100, 0.05, 0.05, 10, freq=2), 6)   # par when y == c
    100.0
    """
    y = ytm / freq
    if y <= -1:
        raise ValueError("per-period yield must exceed -100%")
    return sum(
        cf * (1 + y) ** -t for t, cf in bond_cashflows(face, coupon_rate, years, freq)
    )


def bond_ytm(
    price: float,
    face: float,
    coupon_rate: float,
    years: float,
    freq: int = 2,
    low: float = -0.99,
    high: float = 5.0,
    tol: float = 1e-12,
    max_iter: int = 300,
) -> float:
    """Yield to maturity implied by a price, by bisection.

    Price is monotonically decreasing in yield for a vanilla bond, so the
    bracket is guaranteed to contain exactly one root.
    """
    if price <= 0:
        raise ValueError("price must be positive")

    def f(y: float) -> float:
        return bond_price(face, coupon_rate, y, years, freq) - price

    f_low, f_high = f(low), f(high)
    if f_low * f_high > 0:
        raise ValueError("yield not bracketed; check price and bond terms")

    for _ in range(max_iter):
        mid = 0.5 * (low + high)
        f_mid = f(mid)
        if abs(f_mid) < tol or (high - low) < tol:
            return mid
        if f_low * f_mid < 0:
            high, f_high = mid, f_mid
        else:
            low, f_low = mid, f_mid
    return 0.5 * (low + high)


def macaulay_duration(
    face: float, coupon_rate: float, ytm: float, years: float, freq: int = 2
) -> float:
    """PV-weighted average time to cash flow, in years.

    A zero-coupon bond's Macaulay duration equals its maturity — the sanity
    check the test suite pins.
    """
    y = ytm / freq
    flows = bond_cashflows(face, coupon_rate, years, freq)
    price = sum(cf * (1 + y) ** -t for t, cf in flows)
    if price == 0:
        raise ValueError("bond price is zero; cannot compute duration")
    weighted = sum((t / freq) * cf * (1 + y) ** -t for t, cf in flows)
    return weighted / price


def modified_duration(
    face: float, coupon_rate: float, ytm: float, years: float, freq: int = 2
) -> float:
    """``D_mod = D_macaulay / (1 + y/k)`` — the first-order price sensitivity.

    ``dP/P = -D_mod * dy``.
    """
    d_mac = macaulay_duration(face, coupon_rate, ytm, years, freq)
    return d_mac / (1 + ytm / freq)


def dollar_duration(
    face: float, coupon_rate: float, ytm: float, years: float, freq: int = 2
) -> float:
    """``D$ = D_mod * P`` — price change per unit yield change, in currency.

    Dollar durations add across a portfolio, which is what makes them the
    natural unit for hedging.
    """
    price = bond_price(face, coupon_rate, ytm, years, freq)
    return modified_duration(face, coupon_rate, ytm, years, freq) * price


def convexity(
    face: float, coupon_rate: float, ytm: float, years: float, freq: int = 2
) -> float:
    """Second-order price sensitivity, in years^2.

    ``C = sum t(t+1) CF_t (1+y)^-(t+2) / k^2 / P``.
    """
    y = ytm / freq
    flows = bond_cashflows(face, coupon_rate, years, freq)
    price = sum(cf * (1 + y) ** -t for t, cf in flows)
    if price == 0:
        raise ValueError("bond price is zero; cannot compute convexity")
    raw = sum(t * (t + 1) * cf * (1 + y) ** -(t + 2) for t, cf in flows)
    return raw / (freq**2) / price


def dollar_convexity(
    face: float, coupon_rate: float, ytm: float, years: float, freq: int = 2
) -> float:
    """``C$ = C * P``."""
    return convexity(face, coupon_rate, ytm, years, freq) * bond_price(
        face, coupon_rate, ytm, years, freq
    )


def effective_duration(
    price_fn, y0: float, dy: float = 1e-4
) -> float:
    """Duration by central differencing — for bonds with embedded options.

    ``price_fn(y)`` returns the price at yield ``y``. Use this when the cash
    flows themselves depend on the rate path (callable/puttable bonds, MBS),
    where the analytic formulas above do not apply.

    Sign convention: returns a **positive** number for an ordinary bond, i.e.
    ``(P(y-dy) - P(y+dy)) / (2 * P(y) * dy)``. The course cheat sheet writes
    this as ``(P_rise - P_fall) / (2*dy) / P``; "rise"/"fall" there refers to
    the price, not the yield. Written with yields, as here, the falling-yield
    price comes first — otherwise the sign flips.
    """
    if dy <= 0:
        raise ValueError("dy must be positive")
    p0 = price_fn(y0)
    if p0 == 0:
        raise ValueError("base price is zero")
    return (price_fn(y0 - dy) - price_fn(y0 + dy)) / (2 * p0 * dy)


def effective_convexity(price_fn, y0: float, dy: float = 1e-4) -> float:
    """Convexity by central differencing: ``(P+ + P- - 2P0) / (P0 * dy^2)``."""
    if dy <= 0:
        raise ValueError("dy must be positive")
    p0 = price_fn(y0)
    if p0 == 0:
        raise ValueError("base price is zero")
    return (price_fn(y0 + dy) + price_fn(y0 - dy) - 2 * p0) / (p0 * dy * dy)


def price_change_approx(
    price: float, mod_duration: float, convexity_: float, dy: float
) -> float:
    """Second-order price change: ``dP ≈ P(-D_mod*dy + ½*C*dy²)``.

    The convexity term is what makes the approximation usable for large rate
    moves: duration alone always *understates* the price of a vanilla bond
    because the true price/yield curve is convex.
    """
    return price * (-mod_duration * dy + 0.5 * convexity_ * dy * dy)


def portfolio_modified_duration(
    values: list[float], durations: list[float]
) -> float:
    """Value-weighted modified duration of a portfolio."""
    if len(values) != len(durations):
        raise ValueError("values and durations must be the same length")
    total = sum(values)
    if total == 0:
        raise ValueError("portfolio value is zero")
    return sum(v * d for v, d in zip(values, durations)) / total


def hedge_ratio_duration(
    asset_value: float,
    asset_duration: float,
    hedge_value: float,
    hedge_duration: float,
) -> float:
    """Units of the hedging instrument that zero out dollar duration.

    From ``P_B * D_B = F * D_F``: match dollar durations so a parallel yield
    shift leaves the combined position flat to first order.
    """
    denom = hedge_value * hedge_duration
    if denom == 0:
        raise ValueError("hedging instrument has zero dollar duration")
    return -(asset_value * asset_duration) / denom


def discount_factors_from_spot(
    spot_rates: list[float], continuous: bool = False
) -> list[float]:
    """Discount factors from annually compounded spot rates for t = 1..N."""
    out = []
    for i, r in enumerate(spot_rates, start=1):
        out.append(math.exp(-r * i) if continuous else (1 + r) ** -i)
    return out


def forward_rate(
    spot_near: float, t_near: float, spot_far: float, t_far: float
) -> float:
    """Implied forward rate between ``t_near`` and ``t_far``.

    From no-arbitrage: rolling the near spot into the forward must equal the
    far spot.
    """
    if t_far <= t_near:
        raise ValueError("t_far must exceed t_near")
    num = (1 + spot_far) ** t_far
    den = (1 + spot_near) ** t_near
    return (num / den) ** (1 / (t_far - t_near)) - 1


def bootstrap_spot_curve(
    par_rates: list[float], freq: int = 1, face: float = 100.0
) -> list[float]:
    """Spot (zero) rates implied by a par-bond yield curve.

    ``par_rates[i]`` is the coupon rate of a bond priced at par maturing in
    ``i+1`` periods. Returns per-period spot rates of the same length.

    Bootstrapping is sequential: each maturity's spot rate is the only unknown
    once all the earlier ones are known.
    """
    spots: list[float] = []
    for i, c in enumerate(par_rates, start=1):
        coupon = face * c / freq
        # Discount the coupons that fall on already-solved maturities.
        pv_known = sum(coupon * (1 + s) ** -t for t, s in enumerate(spots, start=1))
        residual = face - pv_known
        if residual <= 0:
            raise ValueError(
                f"cannot bootstrap maturity {i}: non-positive residual value"
            )
        final = coupon + face
        spots.append((final / residual) ** (1 / i) - 1)
    return spots


def par_swap_rate(discount_factors: list[float], freq: int = 1) -> float:
    """Fixed rate that makes a vanilla fixed-for-floating swap worth zero.

    ``c = n * (1 - D_T) / (D_1 + D_2 + ... + D_T)`` where ``n`` is coupon
    periods per year and ``D_i`` are the discount factors on payment dates.

    Intuition: the floating leg is worth par minus the PV of the final
    principal, so the fixed leg must be worth the same.
    """
    if not discount_factors:
        raise ValueError("need at least one discount factor")
    annuity = sum(discount_factors)
    if annuity == 0:
        raise ValueError("discount factors sum to zero")
    return freq * (1 - discount_factors[-1]) / annuity
