"""Time value of money — the discounting spine everything else stands on.

Present value, NPV, IRR, annuities and perpetuities, and rate conversions.

Curriculum anchor: 15.415.1x *Foundations of Modern Finance I* opens on the
present-value machinery and capital budgeting; every later valuation (bonds,
equity, projects, derivatives) is a special case of "discount the cash flows at
a rate that reflects their risk".

Convention used throughout this package
---------------------------------------
* ``rate`` is a **per-period** rate expressed as a decimal (0.05 == 5%).
* Cash flows are lists indexed from **t = 0**, so ``cashflows[0]`` is today.
* Inflows are positive, outflows negative.
* ``continuous=True`` switches discounting from ``(1+r)^-t`` to ``e^(-rt)``.
"""

from __future__ import annotations

import math

__all__ = [
    "discount_factor",
    "pv",
    "fv",
    "npv",
    "irr",
    "payback_period",
    "annuity_pv",
    "annuity_fv",
    "annuity_payment",
    "perpetuity_pv",
    "growing_annuity_pv",
    "growing_perpetuity_pv",
    "ear_from_apr",
    "apr_from_ear",
    "continuous_from_periodic",
    "periodic_from_continuous",
]


def discount_factor(rate: float, t: float, continuous: bool = False) -> float:
    """Value today of 1 unit received at time ``t``."""
    if continuous:
        return math.exp(-rate * t)
    if rate <= -1:
        raise ValueError("periodic rate must exceed -100%")
    return (1.0 + rate) ** (-t)


def pv(amount: float, rate: float, t: float, continuous: bool = False) -> float:
    """Present value of a single cash flow at time ``t``."""
    return amount * discount_factor(rate, t, continuous)


def fv(amount: float, rate: float, t: float, continuous: bool = False) -> float:
    """Future value at time ``t`` of an amount invested today."""
    if continuous:
        return amount * math.exp(rate * t)
    return amount * (1.0 + rate) ** t


def npv(rate: float, cashflows: list[float], continuous: bool = False) -> float:
    """Net present value of a cash-flow stream indexed from t = 0.

    >>> round(npv(0.10, [-100, 60, 60]), 4)
    4.1322
    """
    return sum(
        cf * discount_factor(rate, t, continuous) for t, cf in enumerate(cashflows)
    )


def irr(
    cashflows: list[float],
    low: float = -0.9999,
    high: float = 10.0,
    tol: float = 1e-10,
    max_iter: int = 200,
) -> float:
    """Internal rate of return — the rate that sets NPV to zero.

    Solved by bisection on a bracket, which cannot diverge the way Newton can
    on badly behaved streams.

    Raises ValueError when the stream has no sign change (no IRR exists) or
    when NPV does not change sign across the bracket. Note the standard caveat
    from capital budgeting: a stream whose sign flips more than once can have
    several IRRs, and this returns only the one inside the bracket. For
    ranking mutually exclusive projects, prefer :func:`npv`.
    """
    if not cashflows:
        raise ValueError("no cash flows")
    if all(cf >= 0 for cf in cashflows) or all(cf <= 0 for cf in cashflows):
        raise ValueError("IRR requires at least one sign change in the cash flows")

    f_low, f_high = npv(low, cashflows), npv(high, cashflows)
    if f_low * f_high > 0:
        raise ValueError(
            f"NPV does not change sign on [{low}, {high}]; widen the bracket "
            "or check the cash-flow stream for multiple IRRs"
        )

    for _ in range(max_iter):
        mid = 0.5 * (low + high)
        f_mid = npv(mid, cashflows)
        if abs(f_mid) < tol or (high - low) < tol:
            return mid
        if f_low * f_mid < 0:
            high, f_high = mid, f_mid
        else:
            low, f_low = mid, f_mid
    return 0.5 * (low + high)


def payback_period(cashflows: list[float], rate: float = 0.0) -> float | None:
    """Periods until cumulative (optionally discounted) cash flow turns positive.

    Returns ``None`` if the project never pays back. Interpolates linearly
    within the period in which recovery happens. ``rate=0`` gives the plain
    payback period; a positive rate gives discounted payback.
    """
    cumulative = 0.0
    for t, cf in enumerate(cashflows):
        step = cf * discount_factor(rate, t)
        previous = cumulative
        cumulative += step
        if cumulative >= 0 and t > 0 and step != 0:
            # Linear interpolation inside the period that crossed zero.
            return (t - 1) + (-previous / step)
    return None


def annuity_pv(payment: float, rate: float, n: int, due: bool = False) -> float:
    """PV of ``n`` level payments. ``due=True`` for payments at period start."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if rate == 0:
        value = payment * n
    else:
        value = payment * (1 - (1 + rate) ** -n) / rate
    return value * (1 + rate) if due else value


def annuity_fv(payment: float, rate: float, n: int, due: bool = False) -> float:
    """FV at time ``n`` of ``n`` level payments."""
    if rate == 0:
        value = payment * n
    else:
        value = payment * ((1 + rate) ** n - 1) / rate
    return value * (1 + rate) if due else value


def annuity_payment(present_value: float, rate: float, n: int) -> float:
    """Level payment that amortises ``present_value`` over ``n`` periods."""
    if n <= 0:
        raise ValueError("n must be positive")
    if rate == 0:
        return present_value / n
    return present_value * rate / (1 - (1 + rate) ** -n)


def perpetuity_pv(payment: float, rate: float) -> float:
    """PV of a level payment forever."""
    if rate <= 0:
        raise ValueError("perpetuity requires a positive discount rate")
    return payment / rate


def growing_annuity_pv(payment: float, rate: float, growth: float, n: int) -> float:
    """PV of ``n`` payments growing at ``growth``; ``payment`` is the first one."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if abs(rate - growth) < 1e-12:
        return payment * n / (1 + rate)
    return payment / (rate - growth) * (1 - ((1 + growth) / (1 + rate)) ** n)


def growing_perpetuity_pv(payment: float, rate: float, growth: float) -> float:
    """Gordon growth: PV of a payment growing at ``growth`` forever.

    ``payment`` is the cash flow **one period from now**, not today's.
    """
    if rate <= growth:
        raise ValueError(
            "discount rate must exceed growth rate for a finite value "
            f"(got rate={rate}, growth={growth})"
        )
    return payment / (rate - growth)


def ear_from_apr(apr: float, periods_per_year: int) -> float:
    """Effective annual rate from a nominal APR compounded m times a year."""
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    return (1 + apr / periods_per_year) ** periods_per_year - 1


def apr_from_ear(ear: float, periods_per_year: int) -> float:
    """Nominal APR that produces a given effective annual rate."""
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    return periods_per_year * ((1 + ear) ** (1 / periods_per_year) - 1)


def continuous_from_periodic(rate: float, periods_per_year: int = 1) -> float:
    """Continuously compounded rate equivalent to a periodic one."""
    return periods_per_year * math.log(1 + rate / periods_per_year)


def periodic_from_continuous(rate: float, periods_per_year: int = 1) -> float:
    """Periodic rate equivalent to a continuously compounded one."""
    return periods_per_year * (math.exp(rate / periods_per_year) - 1)
