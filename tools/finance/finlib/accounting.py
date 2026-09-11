"""Financial accounting — statement articulation, accruals, and ratio analysis.

Curriculum anchor: 15.516x *Financial Accounting* — the balance sheet equation,
accrual accounting, the three statements and how they tie together, revenue
recognition, inventory and depreciation policy, and introductory statement
analysis.

The organising idea, and the one worth carrying into any analysis tool: **the
statements articulate.** The balance sheet balances, retained earnings rolls
forward through net income and dividends, and the cash-flow statement
reconciles opening to closing cash. Three independent identities that must all
hold at once. :func:`articulation_check` runs all three, because a model that
silently breaks one of them is producing numbers that cannot be true of any
real firm.

The second idea: **accrual earnings are not cash.** Revenue is recognised when
earned, not when collected, so net income and cash from operations diverge —
legitimately, and also when someone is stretching. :func:`accruals` measures
the gap.
"""

from __future__ import annotations

__all__ = [
    "balance_sheet_check",
    "retained_earnings_roll",
    "cash_roll",
    "articulation_check",
    "accruals",
    "working_capital",
    "liquidity_ratios",
    "leverage_ratios",
    "profitability_ratios",
    "efficiency_ratios",
    "dupont_three_factor",
    "dupont_five_factor",
    "cash_conversion_cycle",
    "straight_line_depreciation",
    "declining_balance_depreciation",
    "cogs_fifo",
    "cogs_lifo",
    "cogs_weighted_average",
]

_TOL = 1e-6


def _safe_div(numerator: float, denominator: float, label: str) -> float:
    if denominator == 0:
        raise ZeroDivisionError(f"{label}: denominator is zero")
    return numerator / denominator


# --------------------------------------------------------------------------
# Articulation
# --------------------------------------------------------------------------


def balance_sheet_check(
    assets: float, liabilities: float, equity: float, tol: float = _TOL
) -> dict[str, object]:
    """``Assets = Liabilities + Equity``. Returns the residual and a verdict."""
    residual = assets - (liabilities + equity)
    return {"balances": abs(residual) <= tol, "residual": residual}


def retained_earnings_roll(
    opening: float,
    net_income: float,
    dividends: float = 0.0,
    other: float = 0.0,
) -> float:
    """``RE_close = RE_open + net income - dividends + other``.

    The hinge between the income statement and the balance sheet: this is the
    only route by which a period's earnings reach equity.
    """
    return opening + net_income - dividends + other


def cash_roll(
    opening_cash: float, operating: float, investing: float, financing: float
) -> float:
    """Closing cash from the three cash-flow sections."""
    return opening_cash + operating + investing + financing


def articulation_check(
    *,
    opening_cash: float,
    closing_cash: float,
    cfo: float,
    cfi: float,
    cff: float,
    opening_retained_earnings: float,
    closing_retained_earnings: float,
    net_income: float,
    dividends: float = 0.0,
    assets: float,
    liabilities: float,
    equity: float,
    tol: float = _TOL,
) -> dict[str, object]:
    """Run all three articulation identities at once.

    Returns per-check residuals and an overall ``articulates`` flag, plus a
    human-readable ``problems`` list naming whichever identity failed. Use it
    as the assertion at the end of any model that builds statements.
    """
    bs = balance_sheet_check(assets, liabilities, equity, tol)
    re_expected = retained_earnings_roll(
        opening_retained_earnings, net_income, dividends
    )
    re_residual = closing_retained_earnings - re_expected
    cash_expected = cash_roll(opening_cash, cfo, cfi, cff)
    cash_residual = closing_cash - cash_expected

    problems = []
    if not bs["balances"]:
        problems.append(
            f"balance sheet does not balance (residual {bs['residual']:+.6g})"
        )
    if abs(re_residual) > tol:
        problems.append(
            f"retained earnings does not roll forward (residual {re_residual:+.6g})"
        )
    if abs(cash_residual) > tol:
        problems.append(
            f"cash does not reconcile (residual {cash_residual:+.6g})"
        )

    return {
        "articulates": not problems,
        "balance_sheet_residual": bs["residual"],
        "retained_earnings_residual": re_residual,
        "cash_residual": cash_residual,
        "problems": problems,
    }


def accruals(net_income: float, cash_from_operations: float) -> float:
    """``accruals = net income - cash from operations``.

    Persistently large positive accruals mean earnings are being recognised
    well ahead of collection. That can be ordinary growth in receivables, or
    it can be aggressive revenue recognition — the number does not tell you
    which, it tells you where to look.
    """
    return net_income - cash_from_operations


# --------------------------------------------------------------------------
# Ratio analysis
# --------------------------------------------------------------------------


def working_capital(current_assets: float, current_liabilities: float) -> float:
    return current_assets - current_liabilities


def liquidity_ratios(
    current_assets: float,
    current_liabilities: float,
    inventory: float = 0.0,
    cash: float = 0.0,
) -> dict[str, float]:
    """Current, quick (acid-test), and cash ratios."""
    return {
        "current": _safe_div(current_assets, current_liabilities, "current ratio"),
        "quick": _safe_div(
            current_assets - inventory, current_liabilities, "quick ratio"
        ),
        "cash": _safe_div(cash, current_liabilities, "cash ratio"),
    }


def leverage_ratios(
    total_debt: float,
    total_equity: float,
    total_assets: float,
    ebit: float | None = None,
    interest_expense: float | None = None,
) -> dict[str, float]:
    """Debt/equity, debt/assets, equity multiplier, and interest coverage."""
    out = {
        "debt_to_equity": _safe_div(total_debt, total_equity, "debt/equity"),
        "debt_to_assets": _safe_div(total_debt, total_assets, "debt/assets"),
        "equity_multiplier": _safe_div(
            total_assets, total_equity, "equity multiplier"
        ),
    }
    if ebit is not None and interest_expense is not None:
        out["interest_coverage"] = _safe_div(
            ebit, interest_expense, "interest coverage"
        )
    return out


def profitability_ratios(
    revenue: float,
    gross_profit: float,
    operating_income: float,
    net_income: float,
    total_assets: float,
    total_equity: float,
) -> dict[str, float]:
    """Margins plus ROA and ROE.

    ROA and ROE here use **end-of-period** balances. Averaging opening and
    closing balances is the more defensible choice when the balance sheet
    moved a lot during the year; be consistent and say which you used.
    """
    return {
        "gross_margin": _safe_div(gross_profit, revenue, "gross margin"),
        "operating_margin": _safe_div(
            operating_income, revenue, "operating margin"
        ),
        "net_margin": _safe_div(net_income, revenue, "net margin"),
        "roa": _safe_div(net_income, total_assets, "ROA"),
        "roe": _safe_div(net_income, total_equity, "ROE"),
    }


def efficiency_ratios(
    revenue: float,
    cogs: float,
    total_assets: float,
    inventory: float,
    receivables: float,
    payables: float,
    days: int = 365,
) -> dict[str, float]:
    """Turnover ratios and the day-count conversions (DSO, DIO, DPO)."""
    inv_turn = _safe_div(cogs, inventory, "inventory turnover")
    rec_turn = _safe_div(revenue, receivables, "receivables turnover")
    pay_turn = _safe_div(cogs, payables, "payables turnover")
    return {
        "asset_turnover": _safe_div(revenue, total_assets, "asset turnover"),
        "inventory_turnover": inv_turn,
        "receivables_turnover": rec_turn,
        "payables_turnover": pay_turn,
        "dio": days / inv_turn,
        "dso": days / rec_turn,
        "dpo": days / pay_turn,
    }


def cash_conversion_cycle(dio: float, dso: float, dpo: float) -> float:
    """``CCC = DIO + DSO - DPO`` — days of cash tied up in the operating cycle.

    A negative cycle means suppliers finance the business: cash is collected
    from customers before it is paid out for inventory.
    """
    return dio + dso - dpo


def dupont_three_factor(
    net_income: float, revenue: float, total_assets: float, total_equity: float
) -> dict[str, float]:
    """``ROE = net margin x asset turnover x equity multiplier``.

    Decomposes a single ROE into *how profitable*, *how productive*, and *how
    levered* — three very different stories that produce the same headline.
    """
    net_margin = _safe_div(net_income, revenue, "net margin")
    asset_turnover = _safe_div(revenue, total_assets, "asset turnover")
    equity_multiplier = _safe_div(total_assets, total_equity, "equity multiplier")
    return {
        "net_margin": net_margin,
        "asset_turnover": asset_turnover,
        "equity_multiplier": equity_multiplier,
        "roe": net_margin * asset_turnover * equity_multiplier,
    }


def dupont_five_factor(
    net_income: float,
    pretax_income: float,
    ebit: float,
    revenue: float,
    total_assets: float,
    total_equity: float,
) -> dict[str, float]:
    """Five-way DuPont, splitting out the tax and interest burdens.

    ``ROE = tax burden x interest burden x operating margin
            x asset turnover x equity multiplier``
    """
    tax_burden = _safe_div(net_income, pretax_income, "tax burden")
    interest_burden = _safe_div(pretax_income, ebit, "interest burden")
    operating_margin = _safe_div(ebit, revenue, "operating margin")
    asset_turnover = _safe_div(revenue, total_assets, "asset turnover")
    equity_multiplier = _safe_div(total_assets, total_equity, "equity multiplier")
    return {
        "tax_burden": tax_burden,
        "interest_burden": interest_burden,
        "operating_margin": operating_margin,
        "asset_turnover": asset_turnover,
        "equity_multiplier": equity_multiplier,
        "roe": tax_burden
        * interest_burden
        * operating_margin
        * asset_turnover
        * equity_multiplier,
    }


# --------------------------------------------------------------------------
# Policy choices: depreciation and inventory
# --------------------------------------------------------------------------


def straight_line_depreciation(
    cost: float, salvage: float, life_years: int
) -> list[float]:
    """Equal expense each year over the asset's life."""
    if life_years <= 0:
        raise ValueError("life_years must be positive")
    if salvage > cost:
        raise ValueError("salvage cannot exceed cost")
    annual = (cost - salvage) / life_years
    return [annual] * life_years


def declining_balance_depreciation(
    cost: float, salvage: float, life_years: int, factor: float = 2.0
) -> list[float]:
    """Declining balance (``factor=2`` is double-declining), floored at salvage.

    Accelerated methods front-load expense: lower early earnings, higher early
    tax shield. Same total expense over the asset's life as straight line —
    only the *timing* differs, which is the whole point of the policy choice.
    """
    if life_years <= 0:
        raise ValueError("life_years must be positive")
    if salvage > cost:
        raise ValueError("salvage cannot exceed cost")
    rate = factor / life_years
    book = cost
    out = []
    for _ in range(life_years):
        expense = min(book * rate, max(book - salvage, 0.0))
        out.append(expense)
        book -= expense
    return out


def _check_layers(layers: list[tuple[float, float]]) -> None:
    if not layers:
        raise ValueError("need at least one inventory layer")
    if any(units < 0 or price < 0 for units, price in layers):
        raise ValueError("units and prices must be non-negative")


def cogs_fifo(
    layers: list[tuple[float, float]], units_sold: float
) -> dict[str, float]:
    """FIFO cost of goods sold. ``layers`` are ``(units, unit_cost)`` oldest first.

    In a rising-price period FIFO charges the *oldest, cheapest* units to COGS,
    so it reports higher income and a more current inventory balance than LIFO.
    """
    _check_layers(layers)
    remaining = units_sold
    cost = 0.0
    total_units = sum(u for u, _ in layers)
    total_cost = sum(u * p for u, p in layers)
    if units_sold > total_units + 1e-9:
        raise ValueError(
            f"cannot sell {units_sold} units from inventory of {total_units}"
        )

    for units, price in layers:
        if remaining <= 0:
            break
        take = min(units, remaining)
        cost += take * price
        remaining -= take
    return {"cogs": cost, "ending_inventory": total_cost - cost}


def cogs_lifo(
    layers: list[tuple[float, float]], units_sold: float
) -> dict[str, float]:
    """LIFO cost of goods sold. ``layers`` are ``(units, unit_cost)`` oldest first."""
    _check_layers(layers)
    total_units = sum(u for u, _ in layers)
    total_cost = sum(u * p for u, p in layers)
    if units_sold > total_units + 1e-9:
        raise ValueError(
            f"cannot sell {units_sold} units from inventory of {total_units}"
        )

    remaining = units_sold
    cost = 0.0
    for units, price in reversed(layers):
        if remaining <= 0:
            break
        take = min(units, remaining)
        cost += take * price
        remaining -= take
    return {"cogs": cost, "ending_inventory": total_cost - cost}


def cogs_weighted_average(
    layers: list[tuple[float, float]], units_sold: float
) -> dict[str, float]:
    """Weighted-average-cost COGS."""
    _check_layers(layers)
    total_units = sum(u for u, _ in layers)
    total_cost = sum(u * p for u, p in layers)
    if total_units == 0:
        raise ValueError("inventory has no units")
    if units_sold > total_units + 1e-9:
        raise ValueError(
            f"cannot sell {units_sold} units from inventory of {total_units}"
        )
    avg = total_cost / total_units
    cost = avg * units_sold
    return {"cogs": cost, "ending_inventory": total_cost - cost, "unit_cost": avg}
