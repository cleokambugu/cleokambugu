#!/usr/bin/env python3
"""fin.py — one front door to finlib from the command line.

Every subcommand prints a readable summary, or machine-readable JSON with
``--json``. No dependencies, no network, no config.

    python tools/finance/fin.py option --spot 100 --strike 100 --rate 0.05 \
        --vol 0.2 --years 1 --compare
    python tools/finance/fin.py bond --face 100 --coupon 0.05 --ytm 0.045 --years 10
    python tools/finance/fin.py npv --rate 0.10 --flows -100,60,60
    python tools/finance/fin.py portfolio --returns 0.08,0.12,0.15 \
        --cov 0.04,0.01,0.02;0.01,0.09,0.015;0.02,0.015,0.16 --rf 0.03

Run ``fin.py <command> -h`` for the options of any one command.

This prices and analyses instruments. It is not investment advice and knows
nothing about any real market.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from finlib import accounting, derivatives, equity, fixed_income  # noqa: E402
from finlib import portfolio as pf  # noqa: E402
from finlib import stochastic, tvm  # noqa: E402


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _floats(text: str) -> list[float]:
    """Parse "1,2,3" or "1 2 3" into a list of floats."""
    cleaned = text.replace(";", ",").replace(" ", ",")
    return [float(x) for x in cleaned.split(",") if x != ""]


def _matrix(text: str) -> list[list[float]]:
    """Parse "a,b;c,d" into a matrix (rows separated by ';')."""
    rows = [r for r in text.split(";") if r.strip()]
    return [[float(x) for x in r.replace(" ", ",").split(",") if x != ""] for r in rows]


def _emit(payload: dict, as_json: bool, title: str = "") -> None:
    if as_json:
        print(json.dumps(payload, indent=2, default=float))
        return
    if title:
        print(f"\n{title}")
        print("-" * len(title))
    width = max((len(k) for k in payload), default=0)
    for key, value in payload.items():
        if isinstance(value, float):
            print(f"  {key.ljust(width)}  {value:,.6g}")
        elif isinstance(value, list):
            rendered = ", ".join(
                f"{v:,.6g}" if isinstance(v, (int, float)) else str(v) for v in value
            )
            print(f"  {key.ljust(width)}  [{rendered}]")
        else:
            print(f"  {key.ljust(width)}  {value}")
    print()


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------


def cmd_npv(a: argparse.Namespace) -> int:
    flows = _floats(a.flows)
    out = {"rate": a.rate, "npv": tvm.npv(a.rate, flows), "n_flows": len(flows)}
    try:
        out["irr"] = tvm.irr(flows)
    except ValueError as exc:
        out["irr"] = f"not available ({exc})"
    payback = tvm.payback_period(flows, a.rate)
    out["discounted_payback"] = payback if payback is not None else "never"
    _emit(out, a.json, "Net present value")
    return 0


def cmd_irr(a: argparse.Namespace) -> int:
    flows = _floats(a.flows)
    rate = tvm.irr(flows)
    _emit(
        {"irr": rate, "npv_at_irr": tvm.npv(rate, flows), "n_flows": len(flows)},
        a.json,
        "Internal rate of return",
    )
    return 0


def cmd_bond(a: argparse.Namespace) -> int:
    price = fixed_income.bond_price(a.face, a.coupon, a.ytm, a.years, a.freq)
    out = {
        "price": price,
        "clean_price_pct_of_par": 100.0 * price / a.face,
        "macaulay_duration": fixed_income.macaulay_duration(
            a.face, a.coupon, a.ytm, a.years, a.freq
        ),
        "modified_duration": fixed_income.modified_duration(
            a.face, a.coupon, a.ytm, a.years, a.freq
        ),
        "dollar_duration": fixed_income.dollar_duration(
            a.face, a.coupon, a.ytm, a.years, a.freq
        ),
        "convexity": fixed_income.convexity(
            a.face, a.coupon, a.ytm, a.years, a.freq
        ),
    }
    if a.shock:
        dy = a.shock / 10_000.0
        approxed = fixed_income.price_change_approx(
            price, out["modified_duration"], out["convexity"], dy
        )
        actual = fixed_income.bond_price(
            a.face, a.coupon, a.ytm + dy, a.years, a.freq
        )
        out[f"est_price_change_{a.shock:+.0f}bp"] = approxed
        out[f"actual_price_change_{a.shock:+.0f}bp"] = actual - price
        out["approximation_error"] = (price + approxed) - actual
    _emit(out, a.json, "Bond")
    return 0


def cmd_ytm(a: argparse.Namespace) -> int:
    y = fixed_income.bond_ytm(a.price, a.face, a.coupon, a.years, a.freq)
    _emit(
        {
            "ytm": y,
            "ytm_pct": 100 * y,
            "check_price": fixed_income.bond_price(
                a.face, a.coupon, y, a.years, a.freq
            ),
        },
        a.json,
        "Yield to maturity",
    )
    return 0


def cmd_swap(a: argparse.Namespace) -> int:
    dfs = _floats(a.discount_factors)
    _emit(
        {
            "par_swap_rate": fixed_income.par_swap_rate(dfs, a.freq),
            "n_payments": len(dfs),
            "annuity_factor": sum(dfs),
        },
        a.json,
        "Par swap rate",
    )
    return 0


def cmd_option(a: argparse.Namespace) -> int:
    common = dict(spot=a.spot, strike=a.strike, r=a.rate, sigma=a.vol, T=a.years)
    out: dict = {"model": a.model, "kind": a.kind}

    if a.model == "bs":
        out["price"] = derivatives.black_scholes(**common, kind=a.kind, q=a.div)
    elif a.model == "binomial":
        out["price"] = derivatives.binomial_price(
            **common, kind=a.kind, q=a.div, steps=a.steps, american=a.american
        )
        out["steps"] = a.steps
        out["american"] = a.american
    else:  # mc
        mc = stochastic.monte_carlo_european(
            a.spot, a.strike, a.rate, a.vol, a.years,
            paths=a.paths, kind=a.kind, q=a.div, seed=a.seed,
        )
        out.update(mc)

    if a.compare:
        out["black_scholes"] = derivatives.black_scholes(
            **common, kind=a.kind, q=a.div
        )
        out["binomial_1000"] = derivatives.binomial_price(
            **common, kind=a.kind, q=a.div, steps=1000
        )
        mc = stochastic.monte_carlo_european(
            a.spot, a.strike, a.rate, a.vol, a.years,
            paths=a.paths, kind=a.kind, q=a.div, seed=a.seed,
        )
        out["monte_carlo"] = mc["price"]
        out["monte_carlo_stderr"] = mc["stderr"]
        out["american_binomial"] = derivatives.binomial_price(
            **common, kind=a.kind, q=a.div, steps=1000, american=True
        )

    if a.greeks:
        out.update(derivatives.greeks(**common, kind=a.kind, q=a.div))

    other = "put" if a.kind == "call" else "call"
    out[f"parity_implied_{other}"] = derivatives.put_call_parity(
        **{a.kind: derivatives.black_scholes(**common, kind=a.kind, q=a.div)},
        spot=a.spot, strike=a.strike, r=a.rate, T=a.years, q=a.div,
    )
    _emit(out, a.json, "Option")
    return 0


def cmd_greeks(a: argparse.Namespace) -> int:
    g = derivatives.greeks(
        spot=a.spot, strike=a.strike, r=a.rate, sigma=a.vol, T=a.years,
        kind=a.kind, q=a.div,
    )
    g["theta_per_day"] = g["theta"] / 365.0
    g["vega_per_vol_point"] = g["vega"] / 100.0
    _emit(g, a.json, f"Greeks ({a.kind})")
    return 0


def cmd_impliedvol(a: argparse.Namespace) -> int:
    iv = derivatives.implied_volatility(
        a.price, a.spot, a.strike, a.rate, a.years, a.kind, a.div
    )
    _emit(
        {
            "implied_vol": iv,
            "implied_vol_pct": 100 * iv,
            "check_price": derivatives.black_scholes(
                a.spot, a.strike, a.rate, iv, a.years, a.kind, a.div
            ),
        },
        a.json,
        "Implied volatility",
    )
    return 0


def cmd_hedge(a: argparse.Namespace) -> int:
    pos = derivatives.greeks(
        spot=a.spot, strike=a.strike, r=a.rate, sigma=a.vol, T=a.years, kind=a.kind
    )
    hedge = derivatives.greeks(
        spot=a.spot, strike=a.hedge_strike, r=a.rate, sigma=a.vol,
        T=a.hedge_years, kind=a.kind,
    )
    n_opt, n_shares = derivatives.delta_gamma_hedge(
        pos["delta"], pos["gamma"], hedge["delta"], hedge["gamma"]
    )
    _emit(
        {
            "position_delta": pos["delta"],
            "position_gamma": pos["gamma"],
            "hedge_option_units": n_opt,
            "hedge_shares": n_shares,
            "residual_delta": pos["delta"] + n_opt * hedge["delta"] + n_shares,
            "residual_gamma": pos["gamma"] + n_opt * hedge["gamma"],
        },
        a.json,
        "Delta-gamma hedge (per unit of position)",
    )
    return 0


def cmd_portfolio(a: argparse.Namespace) -> int:
    mu = _floats(a.returns)
    cov = _matrix(a.cov)
    out: dict = {
        "n_assets": len(mu),
        "min_variance_weights": pf.global_min_variance_weights(cov),
    }
    out["min_variance_std"] = pf.portfolio_std(out["min_variance_weights"], cov)
    out["min_variance_return"] = pf.portfolio_return(
        out["min_variance_weights"], mu
    )
    if a.rf is not None:
        w = pf.tangency_weights(mu, cov, a.rf)
        out["tangency_weights"] = w
        out["tangency_return"] = pf.portfolio_return(w, mu)
        out["tangency_std"] = pf.portfolio_std(w, cov)
        out["tangency_sharpe"] = pf.sharpe_ratio(
            out["tangency_return"], a.rf, out["tangency_std"]
        )
    if a.target is not None:
        w = pf.frontier_weights(mu, cov, a.target)
        out["target_weights"] = w
        out["target_std"] = pf.portfolio_std(w, cov)
    if any(w < 0 for w in out["min_variance_weights"]):
        out["note"] = (
            "negative weights are short positions; this optimiser does not "
            "impose a no-short-sales constraint"
        )
    _emit(out, a.json, "Portfolio")
    return 0


def cmd_capm(a: argparse.Namespace) -> int:
    er = pf.capm_expected_return(a.rf, a.beta, a.premium)
    out = {"expected_return": er, "expected_return_pct": 100 * er}
    if a.realised is not None:
        out["jensen_alpha"] = pf.jensen_alpha(
            a.realised, a.rf, a.beta, a.rf + a.premium
        )
    _emit(out, a.json, "CAPM")
    return 0


def cmd_dcf(a: argparse.Namespace) -> int:
    flows = _floats(a.flows)
    out = equity.dcf_enterprise_value(flows, a.rate, a.growth)
    if a.debt is not None:
        out["equity_value"] = equity.equity_value_from_enterprise(
            out["value"], a.debt, a.cash
        )
    if out["terminal_share"] > 0.75:
        out["warning"] = (
            f"{out['terminal_share']:.0%} of value sits in the terminal "
            "assumption; the forecast is doing little of the work"
        )
    _emit(out, a.json, "Discounted cash flow")
    return 0


def cmd_ddm(a: argparse.Namespace) -> int:
    out = equity.multistage_ddm(_floats(a.dividends), a.rate, a.growth)
    _emit(out, a.json, "Dividend discount model")
    return 0


def cmd_wacc(a: argparse.Namespace) -> int:
    _emit(
        {
            "wacc": equity.wacc(a.equity, a.debt, a.cost_equity, a.cost_debt, a.tax),
            "equity_weight": a.equity / (a.equity + a.debt),
            "debt_weight": a.debt / (a.equity + a.debt),
            "after_tax_cost_of_debt": a.cost_debt * (1 - a.tax),
        },
        a.json,
        "Weighted average cost of capital",
    )
    return 0


def cmd_ratios(a: argparse.Namespace) -> int:
    out = accounting.dupont_three_factor(
        a.net_income, a.revenue, a.assets, a.equity
    )
    out.update(
        accounting.leverage_ratios(a.debt, a.equity, a.assets)
        if a.debt is not None
        else {}
    )
    out["accruals"] = (
        accounting.accruals(a.net_income, a.cfo) if a.cfo is not None else "n/a"
    )
    _emit(out, a.json, "Ratio analysis")
    return 0


def cmd_articulate(a: argparse.Namespace) -> int:
    out = accounting.articulation_check(
        opening_cash=a.opening_cash, closing_cash=a.closing_cash,
        cfo=a.cfo, cfi=a.cfi, cff=a.cff,
        opening_retained_earnings=a.opening_re,
        closing_retained_earnings=a.closing_re,
        net_income=a.net_income, dividends=a.dividends,
        assets=a.assets, liabilities=a.liabilities, equity=a.equity,
    )
    _emit(out, a.json, "Statement articulation")
    return 0 if out["articulates"] else 1


# --------------------------------------------------------------------------
# parser
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="fin.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--json", action="store_true", help="emit JSON instead of text")
    sub = p.add_subparsers(dest="command", required=True)

    def add(name: str, fn, help_: str):
        sp = sub.add_parser(name, help=help_)
        sp.set_defaults(func=fn)
        sp.add_argument("--json", action="store_true", help="emit JSON")
        return sp

    s = add("npv", cmd_npv, "NPV, IRR and discounted payback of a cash-flow stream")
    s.add_argument("--rate", type=float, required=True)
    s.add_argument("--flows", required=True, help="comma-separated, t=0 first")

    s = add("irr", cmd_irr, "internal rate of return")
    s.add_argument("--flows", required=True)

    s = add("bond", cmd_bond, "price, duration and convexity of a coupon bond")
    s.add_argument("--face", type=float, default=100.0)
    s.add_argument("--coupon", type=float, required=True, help="annual, e.g. 0.05")
    s.add_argument("--ytm", type=float, required=True)
    s.add_argument("--years", type=float, required=True)
    s.add_argument("--freq", type=int, default=2)
    s.add_argument("--shock", type=float, help="yield shock in bp to stress")

    s = add("ytm", cmd_ytm, "yield implied by a bond price")
    s.add_argument("--price", type=float, required=True)
    s.add_argument("--face", type=float, default=100.0)
    s.add_argument("--coupon", type=float, required=True)
    s.add_argument("--years", type=float, required=True)
    s.add_argument("--freq", type=int, default=2)

    s = add("swap", cmd_swap, "par fixed rate of a vanilla swap")
    s.add_argument("--discount-factors", required=True, dest="discount_factors")
    s.add_argument("--freq", type=int, default=1)

    def option_args(sp, with_model: bool = False):
        sp.add_argument("--spot", type=float, required=True)
        sp.add_argument("--strike", type=float, required=True)
        sp.add_argument("--rate", type=float, required=True)
        sp.add_argument("--vol", type=float, required=True)
        sp.add_argument("--years", type=float, required=True)
        sp.add_argument("--kind", choices=["call", "put"], default="call")
        sp.add_argument("--div", type=float, default=0.0, help="dividend yield")
        if with_model:
            sp.add_argument(
                "--model", choices=["bs", "binomial", "mc"], default="bs"
            )
            sp.add_argument("--steps", type=int, default=500)
            sp.add_argument("--paths", type=int, default=100_000)
            sp.add_argument("--american", action="store_true")
            sp.add_argument("--seed", type=int, default=None)
            sp.add_argument("--compare", action="store_true",
                            help="price by all three models side by side")
            sp.add_argument("--greeks", action="store_true")

    s = add("option", cmd_option, "price an option (closed form, tree or MC)")
    option_args(s, with_model=True)

    s = add("greeks", cmd_greeks, "analytic Black-Scholes Greeks")
    option_args(s)

    s = add("impliedvol", cmd_impliedvol, "volatility implied by an option price")
    option_args(s)
    s.add_argument("--price", type=float, required=True)

    s = add("hedge", cmd_hedge, "delta-gamma hedge for one unit of a position")
    option_args(s)
    s.add_argument("--hedge-strike", type=float, required=True, dest="hedge_strike")
    s.add_argument("--hedge-years", type=float, required=True, dest="hedge_years")

    s = add("portfolio", cmd_portfolio, "mean-variance optimisation")
    s.add_argument("--returns", required=True, help="expected returns, comma separated")
    s.add_argument("--cov", required=True, help='covariance rows: "a,b;c,d"')
    s.add_argument("--rf", type=float, help="risk-free rate → tangency portfolio")
    s.add_argument("--target", type=float, help="target return → frontier weights")

    s = add("capm", cmd_capm, "CAPM expected return and Jensen's alpha")
    s.add_argument("--rf", type=float, required=True)
    s.add_argument("--beta", type=float, required=True)
    s.add_argument("--premium", type=float, required=True, help="market risk premium")
    s.add_argument("--realised", type=float, help="realised return → alpha")

    s = add("dcf", cmd_dcf, "discounted cash flow with a Gordon terminal value")
    s.add_argument("--flows", required=True, help="forecast FCF, t=1 first")
    s.add_argument("--rate", type=float, required=True)
    s.add_argument("--growth", type=float, required=True)
    s.add_argument("--debt", type=float, help="net debt → equity bridge")
    s.add_argument("--cash", type=float, default=0.0)

    s = add("ddm", cmd_ddm, "multi-stage dividend discount model")
    s.add_argument("--dividends", required=True)
    s.add_argument("--rate", type=float, required=True)
    s.add_argument("--growth", type=float, required=True)

    s = add("wacc", cmd_wacc, "weighted average cost of capital")
    s.add_argument("--equity", type=float, required=True, help="market value")
    s.add_argument("--debt", type=float, required=True, help="market value")
    s.add_argument("--cost-equity", type=float, required=True, dest="cost_equity")
    s.add_argument("--cost-debt", type=float, required=True, dest="cost_debt")
    s.add_argument("--tax", type=float, default=0.0)

    s = add("ratios", cmd_ratios, "DuPont decomposition and leverage ratios")
    s.add_argument("--net-income", type=float, required=True, dest="net_income")
    s.add_argument("--revenue", type=float, required=True)
    s.add_argument("--assets", type=float, required=True)
    s.add_argument("--equity", type=float, required=True)
    s.add_argument("--debt", type=float)
    s.add_argument("--cfo", type=float, help="cash from operations → accruals")

    s = add("articulate", cmd_articulate,
            "check the three statements tie together (exit 1 if not)")
    s.add_argument("--opening-cash", type=float, required=True, dest="opening_cash")
    s.add_argument("--closing-cash", type=float, required=True, dest="closing_cash")
    s.add_argument("--cfo", type=float, required=True)
    s.add_argument("--cfi", type=float, required=True)
    s.add_argument("--cff", type=float, required=True)
    s.add_argument("--opening-re", type=float, required=True, dest="opening_re")
    s.add_argument("--closing-re", type=float, required=True, dest="closing_re")
    s.add_argument("--net-income", type=float, required=True, dest="net_income")
    s.add_argument("--dividends", type=float, default=0.0)
    s.add_argument("--assets", type=float, required=True)
    s.add_argument("--liabilities", type=float, required=True)
    s.add_argument("--equity", type=float, required=True)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, ZeroDivisionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
