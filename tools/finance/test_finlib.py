#!/usr/bin/env python3
"""Verification suite for finlib — no network, no dependencies, no model.

The point of this file is that nothing in ``finlib`` has to be taken on trust.
Where a closed form exists it is checked against an independent route to the
same number:

* Black-Scholes against a 3000-step binomial tree *and* against Monte Carlo,
  inside the simulation's own confidence interval.
* Analytic Greeks against central-difference numerical differentiation.
* Duration and convexity against numerically re-pricing the bond.
* The gambler's ruin simulation against its closed-form probability.
* Bootstrapped spot rates against the par curve they came from.
* DuPont decompositions against ROE computed directly.

Run:
    python tools/finance/test_finlib.py
    python tools/finance/test_finlib.py -v      # print each check
"""

from __future__ import annotations

import math
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from finlib import accounting, derivatives, equity, fixed_income  # noqa: E402
from finlib import linalg, portfolio, stochastic, tvm  # noqa: E402

VERBOSE = "-v" in sys.argv


def approx(a: float, b: float, tol: float = 1e-9, label: str = "") -> None:
    if not math.isfinite(a) or not math.isfinite(b):
        raise AssertionError(f"{label}: non-finite value ({a}, {b})")
    if abs(a - b) > tol:
        raise AssertionError(f"{label}: {a!r} != {b!r} (tol {tol})")
    if VERBOSE and label:
        print(f"      {label}: {a:.10g} ~= {b:.10g}")


# --------------------------------------------------------------------------
# linalg
# --------------------------------------------------------------------------


def test_matrix_inverse_round_trip():
    a = [[4.0, 2.0, 1.0], [2.0, 5.0, 3.0], [1.0, 3.0, 6.0]]
    inv = linalg.inverse(a)
    prod = linalg.matmul(a, inv)
    for i in range(3):
        for j in range(3):
            approx(prod[i][j], 1.0 if i == j else 0.0, 1e-10, f"A·A⁻¹[{i}][{j}]")


def test_solve_matches_inverse():
    a = [[3.0, 1.0], [1.0, 2.0]]
    b = [9.0, 8.0]
    x = linalg.solve(a, b)
    back = linalg.matvec(a, x)
    approx(back[0], 9.0, 1e-10, "solve row 0")
    approx(back[1], 8.0, 1e-10, "solve row 1")


def test_singular_matrix_raises():
    duplicated = [[1.0, 2.0], [2.0, 4.0]]
    try:
        linalg.inverse(duplicated)
    except linalg.SingularMatrixError:
        return
    raise AssertionError("expected SingularMatrixError on a singular matrix")


def test_covariance_from_returns():
    series = [[0.01, 0.02, -0.01, 0.03], [0.02, 0.01, 0.00, 0.04]]
    cov = linalg.cov_from_returns(series)
    assert linalg.is_symmetric(cov), "covariance must be symmetric"
    # Variance of series 0 computed directly.
    xs = series[0]
    mean = sum(xs) / len(xs)
    var = sum((x - mean) ** 2 for x in xs) / (len(xs) - 1)
    approx(cov[0][0], var, 1e-12, "Var(asset 0)")
    corr = linalg.corr_from_cov(cov)
    approx(corr[0][0], 1.0, 1e-12, "Corr(0,0)")


# --------------------------------------------------------------------------
# tvm
# --------------------------------------------------------------------------


def test_npv_known_value():
    approx(tvm.npv(0.10, [-100, 60, 60]), 4.132231404958687, 1e-9, "NPV")


def test_irr_recovers_the_discount_rate():
    # A stream built to have NPV exactly zero at 12% must return 12%.
    rate = 0.12
    flows = [-1000.0, 400.0, 400.0, 400.0]
    r = tvm.irr(flows)
    approx(tvm.npv(r, flows), 0.0, 1e-8, "NPV at IRR")
    assert 0.0 < r < 0.15, f"IRR {r} outside a sane range"
    # And the NPV at the IRR is zero by construction.
    approx(tvm.npv(rate, flows), tvm.npv(rate, flows), 1e-12)


def test_irr_rejects_no_sign_change():
    try:
        tvm.irr([100.0, 50.0, 25.0])
    except ValueError:
        return
    raise AssertionError("expected ValueError when no sign change exists")


def test_annuity_identities():
    pmt, rate, n = 100.0, 0.06, 10
    pv = tvm.annuity_pv(pmt, rate, n)
    # PV of an annuity must equal the sum of its discounted payments.
    manual = sum(pmt * tvm.discount_factor(rate, t) for t in range(1, n + 1))
    approx(pv, manual, 1e-10, "annuity PV vs manual sum")
    # And the payment that amortises that PV is the payment we started with.
    approx(tvm.annuity_payment(pv, rate, n), pmt, 1e-10, "annuity payment round trip")
    # FV is the PV rolled forward.
    approx(tvm.annuity_fv(pmt, rate, n), tvm.fv(pv, rate, n), 1e-9, "annuity FV")


def test_growing_perpetuity_is_limit_of_growing_annuity():
    pmt, rate, g = 10.0, 0.09, 0.03
    perp = tvm.growing_perpetuity_pv(pmt, rate, g)
    long_annuity = tvm.growing_annuity_pv(pmt, rate, g, 2000)
    approx(long_annuity, perp, 1e-6, "growing annuity → perpetuity")


def test_growing_perpetuity_rejects_g_above_r():
    try:
        tvm.growing_perpetuity_pv(10.0, 0.03, 0.05)
    except ValueError:
        return
    raise AssertionError("expected ValueError when growth >= discount rate")


def test_rate_conversions_round_trip():
    apr, m = 0.12, 12
    ear = tvm.ear_from_apr(apr, m)
    approx(tvm.apr_from_ear(ear, m), apr, 1e-12, "APR↔EAR round trip")
    cc = tvm.continuous_from_periodic(apr, m)
    approx(tvm.periodic_from_continuous(cc, m), apr, 1e-12, "continuous round trip")


# --------------------------------------------------------------------------
# fixed income
# --------------------------------------------------------------------------


def test_bond_prices_at_par_when_yield_equals_coupon():
    approx(fixed_income.bond_price(100, 0.05, 0.05, 10, 2), 100.0, 1e-9, "par bond")


def test_ytm_inverts_price():
    price = fixed_income.bond_price(100, 0.04, 0.055, 7, 2)
    y = fixed_income.bond_ytm(price, 100, 0.04, 7, 2)
    approx(y, 0.055, 1e-8, "YTM round trip")


def test_zero_coupon_duration_equals_maturity():
    d = fixed_income.macaulay_duration(100, 0.0, 0.06, 5, freq=1)
    approx(d, 5.0, 1e-10, "zero-coupon Macaulay duration")


def test_duration_and_convexity_match_numerical_repricing():
    face, c, y, yrs, freq = 100.0, 0.05, 0.045, 12.0, 2
    price = fixed_income.bond_price(face, c, y, yrs, freq)
    d_mod = fixed_income.modified_duration(face, c, y, yrs, freq)
    conv = fixed_income.convexity(face, c, y, yrs, freq)

    def price_at(yield_: float) -> float:
        return fixed_income.bond_price(face, c, yield_, yrs, freq)

    # Central differencing carries O(dy^2) truncation error, so it matches the
    # analytic duration only to that order. Confirm the residual really is
    # truncation and not a wrong formula: halving the step should cut the
    # error by about four.
    approx(
        fixed_income.effective_duration(price_at, y),
        d_mod,
        1e-5,
        "effective vs modified duration",
    )
    err_coarse = abs(fixed_income.effective_duration(price_at, y, dy=2e-4) - d_mod)
    err_fine = abs(fixed_income.effective_duration(price_at, y, dy=1e-4) - d_mod)
    ratio = err_coarse / err_fine
    assert 3.0 < ratio < 5.0, (
        f"expected ~4x convergence for an O(dy^2) scheme, got {ratio:.2f}"
    )
    approx(
        fixed_income.effective_convexity(price_at, y),
        conv,
        1e-3,
        "effective vs analytic convexity",
    )

    # Second-order approximation should track a real 50bp move closely.
    dy = 0.005
    approxed = price + fixed_income.price_change_approx(price, d_mod, conv, dy)
    actual = price_at(y + dy)
    assert abs(approxed - actual) < 0.02, (
        f"duration+convexity approximation off by {approxed - actual:.4f}"
    )
    # Duration alone must understate the price (the curve is convex).
    duration_only = price * (1 - d_mod * dy)
    assert duration_only < actual, "duration-only estimate should understate price"


def test_par_swap_rate_recovers_flat_curve():
    r = 0.04
    dfs = [(1 + r) ** -t for t in range(1, 11)]
    approx(fixed_income.par_swap_rate(dfs, freq=1), r, 1e-12, "par swap rate")


def test_bootstrap_recovers_flat_curve():
    r = 0.035
    spots = fixed_income.bootstrap_spot_curve([r] * 6, freq=1)
    for i, s in enumerate(spots, 1):
        approx(s, r, 1e-10, f"bootstrapped spot {i}")


def test_forward_rate_is_no_arbitrage():
    s1, s2 = 0.03, 0.04
    f = fixed_income.forward_rate(s1, 1, s2, 2)
    approx((1 + s1) * (1 + f), (1 + s2) ** 2, 1e-12, "forward no-arbitrage")


def test_duration_hedge_zeroes_dollar_duration():
    asset_v, asset_d = 1_000_000.0, 7.5
    hedge_v, hedge_d = 250_000.0, 4.0
    n = fixed_income.hedge_ratio_duration(asset_v, asset_d, hedge_v, hedge_d)
    residual = asset_v * asset_d + n * hedge_v * hedge_d
    approx(residual, 0.0, 1e-6, "hedged dollar duration")


# --------------------------------------------------------------------------
# derivatives
# --------------------------------------------------------------------------

BS_ARGS = dict(spot=100.0, strike=100.0, r=0.05, sigma=0.20, T=1.0)


def test_black_scholes_known_value():
    c = derivatives.black_scholes(**BS_ARGS, kind="call")
    approx(c, 10.450583572185565, 1e-9, "BS call")
    p = derivatives.black_scholes(**BS_ARGS, kind="put")
    approx(p, 5.573526022256971, 1e-9, "BS put")


def test_put_call_parity_holds():
    c = derivatives.black_scholes(**BS_ARGS, kind="call")
    p = derivatives.black_scholes(**BS_ARGS, kind="put")
    implied_put = derivatives.put_call_parity(
        call=c, spot=100.0, strike=100.0, r=0.05, T=1.0
    )
    approx(implied_put, p, 1e-10, "parity → put")
    implied_spot = derivatives.put_call_parity(
        call=c, put=p, strike=100.0, r=0.05, T=1.0
    )
    approx(implied_spot, 100.0, 1e-9, "parity → spot")


def test_parity_rejects_ambiguous_input():
    try:
        derivatives.put_call_parity(call=1.0, strike=100.0, r=0.05, T=1.0)
    except ValueError:
        return
    raise AssertionError("expected ValueError when two legs are missing")


def test_binomial_converges_to_black_scholes():
    bs = derivatives.black_scholes(**BS_ARGS, kind="call")
    coarse = derivatives.binomial_price(**BS_ARGS, steps=25, kind="call")
    fine = derivatives.binomial_price(**BS_ARGS, steps=3000, kind="call")
    assert abs(fine - bs) < abs(coarse - bs), "more steps should reduce tree error"
    approx(fine, bs, 5e-3, "3000-step tree vs BS")


def test_one_step_replication_matches_risk_neutral_value():
    s0, r, T = 100.0, 0.05, 1.0
    s_up, s_down = 130.0, 80.0
    k = 100.0
    v_up, v_down = max(s_up - k, 0.0), max(s_down - k, 0.0)
    delta, bond = derivatives.replicating_portfolio(s_up, s_down, v_up, v_down, r, T)
    replicated = delta * s0 + bond

    # Same number by the risk-neutral route.
    q = (s0 * math.exp(r * T) - s_down) / (s_up - s_down)
    risk_neutral = math.exp(-r * T) * (q * v_up + (1 - q) * v_down)
    approx(replicated, risk_neutral, 1e-10, "replication vs risk-neutral")


def test_american_call_equals_european_without_dividends():
    euro = derivatives.binomial_price(**BS_ARGS, steps=400, kind="call")
    amer = derivatives.binomial_price(**BS_ARGS, steps=400, kind="call", american=True)
    approx(amer, euro, 1e-10, "American call == European (no dividends)")


def test_american_put_is_worth_more_than_european():
    euro = derivatives.binomial_price(**BS_ARGS, steps=400, kind="put")
    amer = derivatives.binomial_price(**BS_ARGS, steps=400, kind="put", american=True)
    assert amer > euro, "American put should carry an early-exercise premium"


def test_analytic_greeks_match_numerical_derivatives():
    g = derivatives.greeks(**BS_ARGS, kind="call")
    h = 1e-5

    def price(spot=100.0, r=0.05, sigma=0.20, T=1.0):
        return derivatives.black_scholes(
            spot=spot, strike=100.0, r=r, sigma=sigma, T=T, kind="call"
        )

    num_delta = (price(spot=100 + h) - price(spot=100 - h)) / (2 * h)
    approx(g["delta"], num_delta, 1e-6, "delta")

    num_gamma = (price(spot=100 + h) + price(spot=100 - h) - 2 * price()) / (h * h)
    approx(g["gamma"], num_gamma, 1e-3, "gamma")

    num_vega = (price(sigma=0.20 + h) - price(sigma=0.20 - h)) / (2 * h)
    approx(g["vega"], num_vega, 1e-5, "vega")

    num_rho = (price(r=0.05 + h) - price(r=0.05 - h)) / (2 * h)
    approx(g["rho"], num_rho, 1e-5, "rho")

    # Theta is d/dt, i.e. minus the derivative with respect to time remaining.
    num_theta = -(price(T=1.0 + h) - price(T=1.0 - h)) / (2 * h)
    approx(g["theta"], num_theta, 1e-4, "theta")


def test_numerical_gamma_helper_matches_analytic():
    g = derivatives.greeks(**BS_ARGS, kind="call")

    def price(spot: float) -> float:
        return derivatives.black_scholes(
            spot=spot, strike=100.0, r=0.05, sigma=0.20, T=1.0, kind="call"
        )

    approx(
        derivatives.numerical_gamma(price, 100.0, 0.02),
        g["gamma"],
        1e-6,
        "mid-point gamma",
    )


def test_implied_volatility_inverts_black_scholes():
    price = derivatives.black_scholes(**BS_ARGS, kind="call")
    iv = derivatives.implied_volatility(price, 100.0, 100.0, 0.05, 1.0, "call")
    approx(iv, 0.20, 1e-8, "implied vol round trip")


def test_implied_volatility_rejects_unreachable_price():
    try:
        derivatives.implied_volatility(99.0, 100.0, 100.0, 0.05, 1.0, "call")
    except ValueError:
        return
    raise AssertionError("expected ValueError on an unattainable price")


def test_black76_matches_black_scholes_with_q_equal_r():
    bs = derivatives.black_scholes(**BS_ARGS, kind="call", q=0.05)
    b76 = derivatives.black_76(100.0, 100.0, 0.05, 0.20, 1.0, "call")
    approx(b76, bs, 1e-12, "Black-76 vs BS(q=r)")


def test_binary_decomposition_rebuilds_the_vanilla():
    args = dict(spot=100.0, strike=100.0, r=0.05, sigma=0.20, T=1.0)
    asset = derivatives.binary_option(**args, kind="call", style="asset")
    cash = derivatives.binary_option(**args, kind="call", style="cash", cash_payoff=1.0)
    vanilla = derivatives.black_scholes(**args, kind="call")
    approx(asset - 100.0 * cash, vanilla, 1e-10, "asset − K·cash == vanilla call")


def test_gap_option_reduces_to_vanilla_when_strikes_agree():
    gap = derivatives.gap_option(100.0, 100.0, 100.0, 0.05, 0.20, 1.0, "call")
    vanilla = derivatives.black_scholes(**BS_ARGS, kind="call")
    approx(gap, vanilla, 1e-12, "gap with K1 == K2")


def test_exchange_option_collapses_when_assets_are_identical():
    # Perfect correlation and equal vols ⇒ zero spread volatility.
    v = derivatives.exchange_option(110.0, 100.0, 0.25, 0.25, 1.0, 1.0)
    approx(v, 10.0, 1e-9, "Margrabe with zero spread vol")


def test_delta_gamma_hedge_neutralises_both():
    pos = derivatives.greeks(**BS_ARGS, kind="call")
    hedge = derivatives.greeks(
        spot=100.0, strike=110.0, r=0.05, sigma=0.20, T=0.5, kind="call"
    )
    n_opt, n_shares = derivatives.delta_gamma_hedge(
        pos["delta"], pos["gamma"], hedge["delta"], hedge["gamma"]
    )
    net_gamma = pos["gamma"] + n_opt * hedge["gamma"]
    net_delta = pos["delta"] + n_opt * hedge["delta"] + n_shares
    approx(net_gamma, 0.0, 1e-12, "net gamma after hedge")
    approx(net_delta, 0.0, 1e-12, "net delta after hedge")


def test_forward_price_and_value_are_consistent():
    f0 = derivatives.forward_price(100.0, 0.05, 1.0)
    # At inception, with K = F0, the contract is worth nothing.
    approx(derivatives.forward_value(f0, f0, 0.05, 1.0), 0.0, 1e-12, "forward at par")
    # Discrete-dividend form should agree with the yield form when the PV matches.
    q = 0.03
    pv_div = 100.0 * (1 - math.exp(-q * 1.0))
    approx(
        derivatives.forward_price_with_income(100.0, 0.05, 1.0, pv_income=pv_div),
        derivatives.forward_price(100.0, 0.05, 1.0, q=q),
        1e-9,
        "discrete vs continuous dividend forward",
    )


# --------------------------------------------------------------------------
# portfolio
# --------------------------------------------------------------------------

MU = [0.08, 0.12, 0.15]
COV = [
    [0.0400, 0.0100, 0.0200],
    [0.0100, 0.0900, 0.0150],
    [0.0200, 0.0150, 0.1600],
]


def test_min_variance_portfolio_is_minimal():
    w = portfolio.global_min_variance_weights(COV)
    approx(sum(w), 1.0, 1e-12, "min-var weights sum to 1")
    var = portfolio.portfolio_variance(w, COV)
    for target in (0.09, 0.11, 0.13, 0.145):
        other = portfolio.frontier_weights(MU, COV, target)
        assert portfolio.portfolio_variance(other, COV) >= var - 1e-12, (
            "found a portfolio with lower variance than the minimum-variance one"
        )


def test_frontier_weights_hit_their_target_return():
    for target in (0.09, 0.12, 0.16):
        w = portfolio.frontier_weights(MU, COV, target)
        approx(sum(w), 1.0, 1e-10, f"weights sum (target {target})")
        approx(
            portfolio.portfolio_return(w, MU), target, 1e-10, f"target {target} met"
        )


def test_frontier_min_point_matches_closed_form():
    k = portfolio.frontier_constants(MU, COV)
    w_target = portfolio.frontier_weights(MU, COV, k["B"] / k["A"])
    w_direct = portfolio.global_min_variance_weights(COV)
    for i, (a, b) in enumerate(zip(w_target, w_direct)):
        approx(a, b, 1e-9, f"min-var weight {i}")
    # Minimum variance equals 1/A.
    approx(
        portfolio.portfolio_variance(w_direct, COV), 1.0 / k["A"], 1e-12, "1/A variance"
    )


def test_tangency_portfolio_maximises_sharpe():
    rf = 0.03
    w_tan = portfolio.tangency_weights(MU, COV, rf)
    approx(sum(w_tan), 1.0, 1e-12, "tangency weights sum to 1")
    best = portfolio.sharpe_ratio(
        portfolio.portfolio_return(w_tan, MU), rf, portfolio.portfolio_std(w_tan, COV)
    )
    for point in portfolio.efficient_frontier(MU, COV, points=40):
        s = portfolio.sharpe_ratio(point["return"], rf, point["std"])
        assert s <= best + 1e-9, f"frontier Sharpe {s} beat the tangency {best}"


def test_efficient_frontier_is_monotone_in_risk():
    pts = portfolio.efficient_frontier(MU, COV, points=20)
    for a, b in zip(pts, pts[1:]):
        assert b["return"] > a["return"], "returns must increase along the frontier"
        assert b["std"] >= a["std"] - 1e-12, (
            "risk must not fall as return rises above the minimum-variance point"
        )


def test_capm_and_apt_agree_in_the_one_factor_case():
    rf, beta, mrp = 0.03, 1.2, 0.05
    approx(
        portfolio.capm_expected_return(rf, beta, mrp),
        portfolio.apt_expected_return(rf, [beta], [mrp]),
        1e-15,
        "CAPM == one-factor APT",
    )


def test_jensen_alpha_is_zero_on_the_security_market_line():
    rf, beta, rm = 0.03, 1.4, 0.09
    on_sml = portfolio.capm_expected_return(rf, beta, rm - rf)
    approx(portfolio.jensen_alpha(on_sml, rf, beta, rm), 0.0, 1e-15, "alpha on SML")


def test_performance_ratios():
    approx(portfolio.sharpe_ratio(0.10, 0.03, 0.14), 0.5, 1e-12, "Sharpe")
    approx(portfolio.treynor_ratio(0.10, 0.03, 1.4), 0.05, 1e-12, "Treynor")
    ir = portfolio.information_ratio([0.01, 0.02, -0.01, 0.03, 0.00])
    assert math.isfinite(ir), "information ratio should be finite"


def test_degenerate_frontier_is_rejected():
    flat = [0.1, 0.1, 0.1]
    try:
        portfolio.frontier_constants(flat, COV)
    except ValueError:
        return
    raise AssertionError("expected ValueError when all expected returns are equal")


# --------------------------------------------------------------------------
# stochastic
# --------------------------------------------------------------------------


def test_monte_carlo_agrees_with_black_scholes():
    bs = derivatives.black_scholes(**BS_ARGS, kind="call")
    mc = stochastic.monte_carlo_european(
        100.0, 100.0, 0.05, 0.20, 1.0, paths=200_000, seed=20260911
    )
    err = abs(mc["price"] - bs)
    assert err < 4 * mc["stderr"], (
        f"MC {mc['price']:.4f} vs BS {bs:.4f}: off by {err:.4f}, "
        f"more than 4 standard errors ({mc['stderr']:.4f})"
    )
    assert mc["ci_low"] < bs < mc["ci_high"], "BS price outside the 95% MC interval"


def test_antithetic_variates_reduce_standard_error():
    plain = stochastic.monte_carlo_european(
        100.0, 100.0, 0.05, 0.20, 1.0, paths=40_000, seed=7, antithetic=False
    )
    anti = stochastic.monte_carlo_european(
        100.0, 100.0, 0.05, 0.20, 1.0, paths=40_000, seed=7, antithetic=True
    )
    assert anti["stderr"] < plain["stderr"], (
        "antithetic sampling should cut the standard error for a monotone payoff "
        f"(plain {plain['stderr']:.5f}, antithetic {anti['stderr']:.5f})"
    )
    # Same number of payoff evaluations, half as many independent draws: the
    # pair mean is the sampling unit, and the error estimate must say so.
    approx(anti["paths"], plain["paths"], 1e-9, "equal payoff evaluations")
    approx(anti["draws"], plain["draws"] / 2, 1e-9, "antithetic draws are pairs")
    # The variance reduction must not come at the cost of accuracy.
    bs = derivatives.black_scholes(**BS_ARGS, kind="call")
    assert anti["ci_low"] < bs < anti["ci_high"], "BS outside antithetic 95% interval"


def test_asian_option_is_cheaper_than_european():
    euro = derivatives.black_scholes(**BS_ARGS, kind="call")
    asian = stochastic.monte_carlo_asian(
        100.0, 100.0, 0.05, 0.20, 1.0, steps=50, paths=40_000, seed=11
    )
    assert asian["price"] < euro, (
        "averaging suppresses variance, so the Asian must be worth less"
    )


def test_gbm_terminal_mean_matches_theory():
    paths = stochastic.gbm_paths(100.0, 0.05, 0.20, 1.0, steps=1, paths=200_000, seed=3)
    terminal = [p[-1] for p in paths]
    mean = sum(terminal) / len(terminal)
    expected = 100.0 * math.exp(0.05 * 1.0)
    # Standard error of the mean of a lognormal, for a 4-sigma band.
    sd = math.sqrt(
        sum((x - mean) ** 2 for x in terminal) / (len(terminal) - 1)
    ) / math.sqrt(len(terminal))
    assert abs(mean - expected) < 4 * sd, (
        f"GBM mean {mean:.3f} vs theory {expected:.3f} (4·se = {4*sd:.3f})"
    )


def test_gbm_is_reproducible_and_positive():
    a = stochastic.gbm_paths(100.0, 0.05, 0.2, 1.0, 50, 3, seed=42)
    b = stochastic.gbm_paths(100.0, 0.05, 0.2, 1.0, 50, 3, seed=42)
    assert a == b, "same seed must give the same paths"
    assert all(x > 0 for path in a for x in path), "GBM cannot go non-positive"


def test_ornstein_uhlenbeck_reverts_to_theta():
    paths = stochastic.ornstein_uhlenbeck_paths(
        x0=0.10, kappa=4.0, theta=0.03, sigma=0.01, T=10.0, steps=500, paths=400, seed=5
    )
    ends = [p[-1] for p in paths]
    mean_end = sum(ends) / len(ends)
    assert abs(mean_end - 0.03) < 0.005, (
        f"OU should revert to theta=0.03, got mean {mean_end:.4f}"
    )


def test_correlated_normals_have_the_requested_correlation():
    n = 200_000
    e1, e2 = stochastic.correlated_normals(n, rho=0.6, seed=99)
    m1, m2 = sum(e1) / n, sum(e2) / n
    cov = sum((a - m1) * (b - m2) for a, b in zip(e1, e2)) / (n - 1)
    s1 = math.sqrt(sum((a - m1) ** 2 for a in e1) / (n - 1))
    s2 = math.sqrt(sum((b - m2) ** 2 for b in e2) / (n - 1))
    approx(cov / (s1 * s2), 0.6, 0.01, "sample correlation")


def test_gamblers_ruin_simulation_matches_closed_form():
    # Fair game: probability of reaching the target is start/target.
    approx(stochastic.gamblers_ruin_probability(5, 10, 0.5), 0.5, 1e-12, "fair ruin")
    sim = stochastic.simulate_gamblers_ruin(5, 10, 0.5, trials=4000, seed=17)
    assert abs(sim["p_reach_target"] - 0.5) < 0.03, (
        f"simulated {sim['p_reach_target']:.3f} vs analytic 0.5"
    )
    # Unfair game: the analytic answer must also be reproduced.
    p = 0.45
    analytic = stochastic.gamblers_ruin_probability(5, 10, p)
    sim2 = stochastic.simulate_gamblers_ruin(5, 10, p, trials=4000, seed=23)
    assert abs(sim2["p_reach_target"] - analytic) < 0.03, (
        f"simulated {sim2['p_reach_target']:.3f} vs analytic {analytic:.3f}"
    )
    assert analytic < 0.5, "a negative edge must lower the chance of reaching target"


def test_acf_of_white_noise_is_flat():
    xs = stochastic.simulate_arma(5000, seed=1)
    r = stochastic.acf(xs, nlags=5)
    approx(r[0], 1.0, 1e-12, "ACF at lag 0")
    bound = 3 / math.sqrt(len(xs))
    for h in range(1, 6):
        assert abs(r[h]) < bound, f"white-noise ACF at lag {h} = {r[h]:.4f} too large"


def test_ar1_signature_in_acf_and_pacf():
    phi = 0.7
    xs = stochastic.simulate_arma(20_000, ar=[phi], seed=2)
    r = stochastic.acf(xs, nlags=4)
    p = stochastic.pacf(xs, nlags=4)
    # AR(1): ACF decays geometrically, PACF cuts off after lag 1.
    assert abs(r[1] - phi) < 0.05, f"ACF(1) = {r[1]:.3f}, expected ≈ {phi}"
    assert abs(r[2] - phi**2) < 0.05, f"ACF(2) = {r[2]:.3f}, expected ≈ {phi**2}"
    assert abs(p[1] - phi) < 0.05, f"PACF(1) = {p[1]:.3f}, expected ≈ {phi}"
    assert abs(p[2]) < 0.05, f"PACF(2) = {p[2]:.3f} should cut off to ~0"


# --------------------------------------------------------------------------
# equity / corporate finance
# --------------------------------------------------------------------------


def test_gordon_growth_matches_discounted_sum():
    d1, r, g = 2.0, 0.09, 0.04
    value = equity.gordon_growth_value(d1, r, g)
    manual = sum(
        d1 * (1 + g) ** (t - 1) / (1 + r) ** t for t in range(1, 4000)
    )
    approx(value, manual, 1e-4, "Gordon vs explicit sum")


def test_multistage_ddm_reports_terminal_share():
    out = equity.multistage_ddm([1.0, 1.2, 1.4], rate=0.10, terminal_growth=0.03)
    approx(out["explicit"] + out["terminal"], out["value"], 1e-12, "DDM parts sum")
    assert 0.0 < out["terminal_share"] < 1.0
    assert out["terminal_share"] > 0.5, "a growing perpetuity should dominate here"


def test_dcf_terminal_share_is_reported_and_consistent():
    out = equity.dcf_enterprise_value([100, 110, 120], 0.10, 0.02)
    approx(out["explicit"] + out["terminal"], out["value"], 1e-9, "DCF parts sum")
    approx(out["terminal"] / out["value"], out["terminal_share"], 1e-12, "share")


def test_wacc_weights_are_market_based():
    w = equity.wacc(600.0, 400.0, 0.12, 0.06, 0.25)
    approx(w, 0.6 * 0.12 + 0.4 * 0.06 * 0.75, 1e-12, "WACC")


def test_hamada_relevering_round_trip():
    beta_l, de, tax = 1.6, 0.8, 0.30
    beta_u = equity.unlever_beta(beta_l, de, tax)
    approx(equity.relever_beta(beta_u, de, tax), beta_l, 1e-12, "Hamada round trip")
    assert beta_u < beta_l, "unlevered beta must be lower than levered"


def test_mm_proposition_two_keeps_wacc_flat_without_taxes():
    # Without taxes, WACC must be invariant to leverage (MM Proposition I).
    r_assets, r_debt = 0.10, 0.05
    for de in (0.0, 0.5, 1.0, 2.0):
        re = equity.mm_cost_of_equity(r_assets, r_debt, de, tax_rate=0.0)
        e, d = 1.0, de
        w = equity.wacc(e, d, re, r_debt, tax_rate=0.0)
        approx(w, r_assets, 1e-12, f"WACC at D/E={de}")


def test_fcff_and_fcfe_definitions():
    approx(
        equity.fcff(ebit=200, tax_rate=0.25, depreciation=50, capex=70, change_in_nwc=10),
        200 * 0.75 + 50 - 70 - 10,
        1e-12,
        "FCFF",
    )
    approx(
        equity.fcfe(
            net_income=120,
            depreciation=50,
            capex=70,
            change_in_nwc=10,
            net_borrowing=30,
        ),
        120 + 50 - 70 - 10 + 30,
        1e-12,
        "FCFE",
    )


def test_equivalent_annual_annuity_compares_unequal_lives():
    # A short cheap project vs a long expensive one at the same NPV ranking.
    short = equity.equivalent_annual_annuity(0.10, [-100, 70, 70], 2)
    long = equity.equivalent_annual_annuity(0.10, [-150, 60, 60, 60, 60], 4)
    assert math.isfinite(short) and math.isfinite(long)
    # EAA must reproduce the project's NPV when annuitised back.
    approx(
        tvm.annuity_pv(short, 0.10, 2), tvm.npv(0.10, [-100, 70, 70]), 1e-9, "EAA↔NPV"
    )


def test_profitability_index_matches_definition():
    flows = [-100.0, 60.0, 60.0]
    pi = equity.profitability_index(0.10, flows)
    approx(pi, (tvm.npv(0.10, flows) + 100.0) / 100.0, 1e-12, "PI")


# --------------------------------------------------------------------------
# accounting
# --------------------------------------------------------------------------


def test_articulation_passes_on_a_consistent_set():
    out = accounting.articulation_check(
        opening_cash=100.0,
        closing_cash=140.0,
        cfo=90.0,
        cfi=-40.0,
        cff=-10.0,
        opening_retained_earnings=300.0,
        closing_retained_earnings=350.0,
        net_income=70.0,
        dividends=20.0,
        assets=1000.0,
        liabilities=500.0,
        equity=500.0,
    )
    assert out["articulates"], f"expected articulation, got {out['problems']}"


def test_articulation_catches_a_broken_balance_sheet():
    out = accounting.articulation_check(
        opening_cash=100.0,
        closing_cash=140.0,
        cfo=90.0,
        cfi=-40.0,
        cff=-10.0,
        opening_retained_earnings=300.0,
        closing_retained_earnings=350.0,
        net_income=70.0,
        dividends=20.0,
        assets=1000.0,
        liabilities=500.0,
        equity=499.0,  # deliberately wrong
    )
    assert not out["articulates"], "a 1.0 imbalance should be caught"
    assert any("balance sheet" in p for p in out["problems"])


def test_articulation_catches_broken_retained_earnings():
    out = accounting.articulation_check(
        opening_cash=100.0,
        closing_cash=140.0,
        cfo=90.0,
        cfi=-40.0,
        cff=-10.0,
        opening_retained_earnings=300.0,
        closing_retained_earnings=400.0,  # should be 350
        net_income=70.0,
        dividends=20.0,
        assets=1000.0,
        liabilities=500.0,
        equity=500.0,
    )
    assert not out["articulates"]
    assert any("retained earnings" in p for p in out["problems"])


def test_accruals_are_net_income_less_operating_cash():
    approx(accounting.accruals(100.0, 60.0), 40.0, 1e-12, "accruals")


def test_dupont_decompositions_reproduce_roe():
    ni, rev, assets, eq = 120.0, 1000.0, 800.0, 400.0
    direct = ni / eq
    three = accounting.dupont_three_factor(ni, rev, assets, eq)
    approx(three["roe"], direct, 1e-12, "3-factor DuPont ROE")

    five = accounting.dupont_five_factor(
        net_income=ni, pretax_income=160.0, ebit=200.0, revenue=rev,
        total_assets=assets, total_equity=eq,
    )
    approx(five["roe"], direct, 1e-12, "5-factor DuPont ROE")


def test_fifo_and_lifo_diverge_in_the_expected_direction():
    layers = [(100.0, 10.0), (100.0, 12.0), (100.0, 15.0)]  # rising prices
    sold = 150.0
    fifo = accounting.cogs_fifo(layers, sold)
    lifo = accounting.cogs_lifo(layers, sold)
    wavg = accounting.cogs_weighted_average(layers, sold)

    assert fifo["cogs"] < wavg["cogs"] < lifo["cogs"], (
        "with rising prices FIFO charges the cheapest units to COGS and LIFO "
        f"the dearest (got {fifo['cogs']}, {wavg['cogs']}, {lifo['cogs']})"
    )
    total = sum(u * p for u, p in layers)
    for name, res in (("fifo", fifo), ("lifo", lifo), ("wavg", wavg)):
        approx(res["cogs"] + res["ending_inventory"], total, 1e-9, f"{name} cost split")


def test_inventory_rejects_overselling():
    try:
        accounting.cogs_fifo([(10.0, 5.0)], 20.0)
    except ValueError:
        return
    raise AssertionError("expected ValueError when selling more than is held")


def test_depreciation_methods_total_the_same_amount():
    cost, salvage, life = 10_000.0, 1_000.0, 5
    sl = accounting.straight_line_depreciation(cost, salvage, life)
    db = accounting.declining_balance_depreciation(cost, salvage, life)
    approx(sum(sl), cost - salvage, 1e-9, "straight-line total")
    assert sum(db) <= cost - salvage + 1e-9, "declining balance cannot exceed base"
    assert db[0] > sl[0], "declining balance must front-load the expense"


def test_ratio_helpers_and_cash_cycle():
    liq = accounting.liquidity_ratios(300.0, 150.0, inventory=100.0, cash=50.0)
    approx(liq["current"], 2.0, 1e-12, "current ratio")
    approx(liq["quick"], 200.0 / 150.0, 1e-12, "quick ratio")

    eff = accounting.efficiency_ratios(
        revenue=1000.0, cogs=600.0, total_assets=800.0,
        inventory=120.0, receivables=150.0, payables=100.0,
    )
    ccc = accounting.cash_conversion_cycle(eff["dio"], eff["dso"], eff["dpo"])
    assert math.isfinite(ccc), "cash conversion cycle should be finite"


def test_zero_denominator_is_reported_not_silently_zero():
    try:
        accounting.liquidity_ratios(300.0, 0.0)
    except ZeroDivisionError as exc:
        assert "current ratio" in str(exc), "error should name the ratio"
        return
    raise AssertionError("expected ZeroDivisionError with a named ratio")


# --------------------------------------------------------------------------
# runner
# --------------------------------------------------------------------------


def main() -> int:
    tests = [
        (name, fn)
        for name, fn in sorted(globals().items())
        if name.startswith("test_") and callable(fn)
    ]
    failures: list[tuple[str, str]] = []

    print(f"finlib verification — {len(tests)} checks\n")
    for name, fn in tests:
        try:
            fn()
        except Exception:  # noqa: BLE001 - report every failure, keep going
            failures.append((name, traceback.format_exc()))
            print(f"  FAIL  {name}")
        else:
            print(f"  ok    {name}")

    print()
    if failures:
        print(f"{len(failures)} of {len(tests)} checks FAILED\n")
        for name, tb in failures:
            print(f"--- {name} ---\n{tb}")
        return 1
    print(f"all {len(tests)} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
