"""Equity valuation and corporate finance.

Dividend discount and free-cash-flow valuation, the cost of capital, and the
capital-structure results (Modigliani-Miller, Hamada relevering, the tax
shield).

Curriculum anchors
------------------
* 15.415.1x — valuation of common stocks; introduction to corporate finance
  and capital budgeting.
* 15.415.2x — capital budgeting and real options, financing and capital
  structure, and the interaction between investing and financing.

A standing warning that the course makes early and often: a terminal value
computed by Gordon growth usually dominates a DCF, and it is the least
reliable number in the model. :func:`dcf_enterprise_value` returns the
terminal share of value alongside the total so that dominance is visible
rather than buried.
"""

from __future__ import annotations

from .tvm import discount_factor, growing_perpetuity_pv, npv

__all__ = [
    "gordon_growth_value",
    "multistage_ddm",
    "wacc",
    "unlever_beta",
    "relever_beta",
    "mm_cost_of_equity",
    "tax_shield_value",
    "fcff",
    "fcfe",
    "dcf_enterprise_value",
    "equity_value_from_enterprise",
    "profitability_index",
    "equivalent_annual_annuity",
]


def gordon_growth_value(next_cashflow: float, rate: float, growth: float) -> float:
    """Value of a perpetually growing cash flow.

    ``next_cashflow`` is the flow **one period out** (D1, not D0). If you hold
    D0, pass ``D0 * (1 + g)``.
    """
    return growing_perpetuity_pv(next_cashflow, rate, growth)


def multistage_ddm(
    dividends: list[float],
    rate: float,
    terminal_growth: float,
    terminal_dividend: float | None = None,
) -> dict[str, float]:
    """Multi-stage dividend discount model.

    ``dividends`` are the explicit-forecast dividends for t = 1..N. The
    terminal value is a Gordon perpetuity starting at ``terminal_dividend``
    (defaults to the last forecast dividend grown one period), discounted from
    t = N.

    Returns the ``explicit`` PV, the ``terminal`` PV, the ``value``, and
    ``terminal_share`` — the fraction of value sitting in the terminal
    assumption.
    """
    if not dividends:
        raise ValueError("need at least one forecast dividend")
    n = len(dividends)

    explicit = sum(d * discount_factor(rate, t) for t, d in enumerate(dividends, 1))
    d_next = (
        terminal_dividend
        if terminal_dividend is not None
        else dividends[-1] * (1 + terminal_growth)
    )
    terminal_at_n = growing_perpetuity_pv(d_next, rate, terminal_growth)
    terminal = terminal_at_n * discount_factor(rate, n)

    value = explicit + terminal
    return {
        "explicit": explicit,
        "terminal": terminal,
        "value": value,
        "terminal_share": terminal / value if value else 0.0,
    }


def wacc(
    equity_value: float,
    debt_value: float,
    cost_equity: float,
    cost_debt: float,
    tax_rate: float = 0.0,
) -> float:
    """``WACC = E/V * re + D/V * rd * (1 - t)``.

    Weights are **market** values, not book. Using book weights is the single
    most common way to get a cost of capital wrong.
    """
    total = equity_value + debt_value
    if total <= 0:
        raise ValueError("total firm value must be positive")
    if not 0.0 <= tax_rate < 1.0:
        raise ValueError("tax_rate must be in [0, 1)")
    we = equity_value / total
    wd = debt_value / total
    return we * cost_equity + wd * cost_debt * (1 - tax_rate)


def unlever_beta(
    levered_beta: float, debt_to_equity: float, tax_rate: float = 0.0
) -> float:
    """Hamada: strip financial risk out of an observed equity beta.

    ``beta_U = beta_L / (1 + (1 - t) D/E)``

    Asset beta is the comparable quantity across firms with different capital
    structures — the reason you unlever peers before averaging.
    """
    return levered_beta / (1 + (1 - tax_rate) * debt_to_equity)


def relever_beta(
    asset_beta: float, debt_to_equity: float, tax_rate: float = 0.0
) -> float:
    """Hamada in reverse: put the target capital structure's risk back in."""
    return asset_beta * (1 + (1 - tax_rate) * debt_to_equity)


def mm_cost_of_equity(
    cost_assets: float, cost_debt: float, debt_to_equity: float, tax_rate: float = 0.0
) -> float:
    """Modigliani-Miller Proposition II.

    ``re = rA + (rA - rd) * D/E * (1 - t)``

    Leverage does not create value in a frictionless world; it reshuffles it.
    The cost of equity rises exactly enough to offset the cheaper debt, which
    is why MM I says firm value is invariant to capital structure. With taxes,
    the ``(1-t)`` term is what lets the tax shield break that invariance.
    """
    return cost_assets + (cost_assets - cost_debt) * debt_to_equity * (1 - tax_rate)


def tax_shield_value(debt: float, tax_rate: float, permanent: bool = True) -> float:
    """PV of the interest tax shield.

    For permanent debt the classic result is simply ``t * D`` — the discount
    rate cancels. Set ``permanent=False`` to get the one-period shield instead.
    """
    if not 0.0 <= tax_rate < 1.0:
        raise ValueError("tax_rate must be in [0, 1)")
    return tax_rate * debt if permanent else tax_rate * debt


def fcff(
    ebit: float,
    tax_rate: float,
    depreciation: float,
    capex: float,
    change_in_nwc: float,
) -> float:
    """Free cash flow to the **firm**: ``EBIT(1-t) + D&A - capex - ΔNWC``.

    Discount at WACC to get enterprise value.
    """
    return ebit * (1 - tax_rate) + depreciation - capex - change_in_nwc


def fcfe(
    net_income: float,
    depreciation: float,
    capex: float,
    change_in_nwc: float,
    net_borrowing: float,
) -> float:
    """Free cash flow to **equity**: ``NI + D&A - capex - ΔNWC + net borrowing``.

    Discount at the cost of equity to get equity value directly.
    """
    return net_income + depreciation - capex - change_in_nwc + net_borrowing


def dcf_enterprise_value(
    free_cashflows: list[float], discount_rate: float, terminal_growth: float
) -> dict[str, float]:
    """DCF with a Gordon terminal value.

    ``free_cashflows`` are for t = 1..N. Returns ``explicit``, ``terminal``,
    ``value`` and ``terminal_share``.

    A ``terminal_share`` above roughly 0.75 means the valuation is mostly an
    assumption about the far future, not about the forecast. That is not
    automatically wrong — it is normal for a growing firm — but it tells you
    where to spend your scrutiny.
    """
    if not free_cashflows:
        raise ValueError("need at least one forecast cash flow")
    n = len(free_cashflows)

    explicit = sum(
        cf * discount_factor(discount_rate, t)
        for t, cf in enumerate(free_cashflows, 1)
    )
    terminal_at_n = growing_perpetuity_pv(
        free_cashflows[-1] * (1 + terminal_growth), discount_rate, terminal_growth
    )
    terminal = terminal_at_n * discount_factor(discount_rate, n)
    value = explicit + terminal
    return {
        "explicit": explicit,
        "terminal": terminal,
        "value": value,
        "terminal_share": terminal / value if value else 0.0,
    }


def equity_value_from_enterprise(
    enterprise_value: float,
    total_debt: float,
    cash: float = 0.0,
    minority_interest: float = 0.0,
) -> float:
    """The EV-to-equity bridge: ``EV - debt + cash - minority interest``."""
    return enterprise_value - total_debt + cash - minority_interest


def profitability_index(rate: float, cashflows: list[float]) -> float:
    """``PI = PV(inflows) / |initial outlay|``.

    Used to rank projects when capital is rationed, where raw NPV would favour
    whichever project is simply biggest.
    """
    if not cashflows or cashflows[0] >= 0:
        raise ValueError("expected a negative initial outlay at t = 0")
    pv_inflows = npv(rate, cashflows) - cashflows[0]
    return pv_inflows / abs(cashflows[0])


def equivalent_annual_annuity(
    rate: float, cashflows: list[float], years: int
) -> float:
    """Level annual cash flow with the same NPV over ``years``.

    The correct way to compare projects with **different lives** — plain NPV
    silently favours the longer one.
    """
    from .tvm import annuity_payment

    if years <= 0:
        raise ValueError("years must be positive")
    return annuity_payment(npv(rate, cashflows), rate, years)
