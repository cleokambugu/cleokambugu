"""Stochastic processes, time series, and Monte Carlo.

Brownian motion and geometric Brownian motion, Euler-Maruyama for a general
SDE, Ornstein-Uhlenbeck mean reversion, correlated shocks, Monte Carlo option
pricing with antithetic variates, the gambler's ruin, and ARMA simulation with
ACF/PACF.

Curriculum anchor: 15.455x *Mathematical Methods for Quantitative Finance* —
probability, discrete- and continuous-time stochastic processes, time series,
Ito calculus, and continuous-time finance.

The discrete building blocks here (random walk, gambler's ruin, the binomial
lognormal approximation) are the ones the course uses to *motivate* the
continuous limit: a binomial tree with the time step shrinking to zero becomes
geometric Brownian motion, which is why the same option price falls out of a
tree, a closed form, and a simulation. The test suite pins all three against
each other.

All samplers take an optional ``seed`` and use their own
:class:`random.Random` instance, so results are reproducible and callers never
disturb the global RNG state.
"""

from __future__ import annotations

import math
import random

__all__ = [
    "brownian_paths",
    "gbm_paths",
    "euler_maruyama",
    "ornstein_uhlenbeck_paths",
    "correlated_normals",
    "monte_carlo_european",
    "monte_carlo_asian",
    "gamblers_ruin_probability",
    "simulate_gamblers_ruin",
    "simulate_arma",
    "acf",
    "pacf",
]


def _rng(seed: int | None) -> random.Random:
    return random.Random(seed)


# --------------------------------------------------------------------------
# Continuous-time processes
# --------------------------------------------------------------------------


def brownian_paths(
    steps: int, paths: int = 1, dt: float = 1.0, seed: int | None = None
) -> list[list[float]]:
    """Standard Brownian motion paths, each starting at 0.

    Returns ``paths`` lists of length ``steps + 1``. Increments are
    ``N(0, dt)``; variance grows linearly in time, which is the scaling
    property that makes ``sigma * sqrt(T)`` the natural unit of volatility.
    """
    if steps < 0 or paths <= 0:
        raise ValueError("steps must be non-negative and paths positive")
    rng = _rng(seed)
    sd = math.sqrt(dt)
    out = []
    for _ in range(paths):
        level = 0.0
        path = [0.0]
        for _ in range(steps):
            level += rng.gauss(0.0, sd)
            path.append(level)
        out.append(path)
    return out


def gbm_paths(
    spot: float,
    mu: float,
    sigma: float,
    T: float,
    steps: int,
    paths: int = 1,
    seed: int | None = None,
) -> list[list[float]]:
    """Geometric Brownian motion by exact log-stepping.

    ``S_{t+h} = S_t exp((mu - sigma^2/2) h + sigma sqrt(h) eps)``

    This is the *exact* solution of the SDE, not an Euler approximation, so it
    carries no discretisation bias in the terminal distribution however large
    the step. The ``-sigma^2/2`` is the Ito correction: the drift of
    ``log S`` is not the drift of ``S``, and dropping it is the classic
    first mistake in simulating prices.

    Pass ``mu = r - q`` for risk-neutral pricing.
    """
    if spot <= 0:
        raise ValueError("spot must be positive")
    if steps <= 0 or paths <= 0:
        raise ValueError("steps and paths must be positive")
    rng = _rng(seed)
    h = T / steps
    drift = (mu - 0.5 * sigma * sigma) * h
    vol = sigma * math.sqrt(h)

    out = []
    for _ in range(paths):
        s = spot
        path = [s]
        for _ in range(steps):
            s *= math.exp(drift + vol * rng.gauss(0.0, 1.0))
            path.append(s)
        out.append(path)
    return out


def euler_maruyama(
    x0: float,
    drift,
    diffusion,
    T: float,
    steps: int,
    paths: int = 1,
    seed: int | None = None,
) -> list[list[float]]:
    """Euler-Maruyama for ``dX = a(X,t) dt + b(X,t) dW``.

    ``drift(x, t)`` and ``diffusion(x, t)`` are callables. Use this when the
    SDE has no closed-form solution; unlike :func:`gbm_paths` it carries
    discretisation error of order ``sqrt(dt)``, so shrink the step until the
    answer stops moving.
    """
    if steps <= 0 or paths <= 0:
        raise ValueError("steps and paths must be positive")
    rng = _rng(seed)
    h = T / steps
    sqrt_h = math.sqrt(h)

    out = []
    for _ in range(paths):
        x = x0
        t = 0.0
        path = [x]
        for _ in range(steps):
            x += drift(x, t) * h + diffusion(x, t) * sqrt_h * rng.gauss(0.0, 1.0)
            t += h
            path.append(x)
        out.append(path)
    return out


def ornstein_uhlenbeck_paths(
    x0: float,
    kappa: float,
    theta: float,
    sigma: float,
    T: float,
    steps: int,
    paths: int = 1,
    seed: int | None = None,
) -> list[list[float]]:
    """Mean-reverting OU / Vasicek process, stepped exactly.

    ``dX = kappa (theta - X) dt + sigma dW``

    The workhorse for short rates and spreads: unlike GBM it pulls back toward
    ``theta`` at speed ``kappa`` and can go negative.
    """
    if kappa <= 0:
        raise ValueError("kappa must be positive for mean reversion")
    if steps <= 0 or paths <= 0:
        raise ValueError("steps and paths must be positive")
    rng = _rng(seed)
    h = T / steps
    decay = math.exp(-kappa * h)
    sd = sigma * math.sqrt((1 - decay * decay) / (2 * kappa))

    out = []
    for _ in range(paths):
        x = x0
        path = [x]
        for _ in range(steps):
            x = theta + (x - theta) * decay + sd * rng.gauss(0.0, 1.0)
            path.append(x)
        out.append(path)
    return out


def correlated_normals(
    n: int, rho: float, seed: int | None = None
) -> tuple[list[float], list[float]]:
    """Two correlated standard normal series.

    ``eps2 = rho * eps1 + sqrt(1 - rho^2) * eps``

    The two-asset case of a Cholesky factorisation, and the recipe the course
    gives for Monte Carlo on spread and basket payoffs.
    """
    if not -1.0 <= rho <= 1.0:
        raise ValueError("rho must lie in [-1, 1]")
    rng = _rng(seed)
    root = math.sqrt(1 - rho * rho)
    e1, e2 = [], []
    for _ in range(n):
        a = rng.gauss(0.0, 1.0)
        b = rng.gauss(0.0, 1.0)
        e1.append(a)
        e2.append(rho * a + root * b)
    return e1, e2


# --------------------------------------------------------------------------
# Monte Carlo pricing
# --------------------------------------------------------------------------


def monte_carlo_european(
    spot: float,
    strike: float,
    r: float,
    sigma: float,
    T: float,
    paths: int = 100_000,
    kind: str = "call",
    q: float = 0.0,
    seed: int | None = None,
    antithetic: bool = True,
) -> dict[str, float]:
    """Monte Carlo price of a European option under GBM.

    Returns ``price``, ``stderr``, the 95% confidence bounds ``ci_low`` /
    ``ci_high``, the number of payoff ``evaluations`` as ``paths``, and the
    number of independent ``draws`` behind the error estimate.

    Because the payoff depends only on ``S_T``, terminal values are drawn in
    one step — no path discretisation is needed or wanted. Antithetic variates
    pair each draw with its negation, which cancels much of the sampling error
    for a monotone payoff at no extra cost.

    With antithetic sampling ``draws`` is half of ``paths``: the pair mean is
    the independent unit, because the two halves of a pair are negatively
    correlated on purpose. That is why ``stderr`` still falls — the pair means
    have lower variance than single draws — and why it would be wrong to
    compute it over the pooled payoffs.

    Always read ``stderr``: a Monte Carlo price without its error bar is not a
    price, it is a number. Error falls as ``1/sqrt(draws)``, so four times the
    work buys half the error.
    """
    k = kind.lower().strip()
    if k not in ("call", "put"):
        raise ValueError("kind must be 'call' or 'put'")
    if paths <= 1:
        raise ValueError("need more than one path")

    rng = _rng(seed)
    drift = (r - q - 0.5 * sigma * sigma) * T
    vol = sigma * math.sqrt(T)
    disc = math.exp(-r * T)
    sign = 1.0 if k == "call" else -1.0

    # The independent sampling unit is one *draw*: a single payoff without
    # antithetic sampling, or the mean of the (z, -z) pair with it. Pooling
    # the two halves of a pair and treating them as independent would be
    # wrong — they are deliberately negatively correlated, which is the whole
    # mechanism — and would report a standard error that does not describe
    # the estimator actually being used.
    samples: list[float] = []
    evaluations = 0
    draws = paths // 2 if antithetic else paths
    for _ in range(draws):
        z = rng.gauss(0.0, 1.0)
        if antithetic:
            up = max(sign * (spot * math.exp(drift + vol * z) - strike), 0.0)
            down = max(sign * (spot * math.exp(drift - vol * z) - strike), 0.0)
            samples.append(0.5 * (up + down))
            evaluations += 2
        else:
            s_t = spot * math.exp(drift + vol * z)
            samples.append(max(sign * (s_t - strike), 0.0))
            evaluations += 1

    n = len(samples)
    if n < 2:
        raise ValueError("need at least two independent draws")
    mean = sum(samples) / n
    var = sum((p - mean) ** 2 for p in samples) / (n - 1)
    price = disc * mean
    stderr = disc * math.sqrt(var / n)
    return {
        "price": price,
        "stderr": stderr,
        "ci_low": price - 1.96 * stderr,
        "ci_high": price + 1.96 * stderr,
        "paths": float(evaluations),
        "draws": float(n),
    }


def monte_carlo_asian(
    spot: float,
    strike: float,
    r: float,
    sigma: float,
    T: float,
    steps: int = 50,
    paths: int = 50_000,
    kind: str = "call",
    q: float = 0.0,
    seed: int | None = None,
    average: str = "arithmetic",
) -> dict[str, float]:
    """Average-price Asian option — the case with no general closed form.

    Payoff ``(A_T - K)+`` for a call, where ``A_T`` is the average of the
    monitored prices. Arithmetic averaging has no closed form (a sum of
    lognormals is not lognormal), which is exactly why it is the standard
    motivation for Monte Carlo. Geometric averaging does have one, so it makes
    a useful control.

    Averaging suppresses terminal variance, so an Asian is worth **less** than
    the otherwise identical European — a relation the test suite pins.
    """
    k = kind.lower().strip()
    if k not in ("call", "put"):
        raise ValueError("kind must be 'call' or 'put'")
    avg = average.lower().strip()
    if avg not in ("arithmetic", "geometric"):
        raise ValueError("average must be 'arithmetic' or 'geometric'")
    if steps <= 0 or paths <= 1:
        raise ValueError("steps must be positive and paths > 1")

    rng = _rng(seed)
    h = T / steps
    drift = (r - q - 0.5 * sigma * sigma) * h
    vol = sigma * math.sqrt(h)
    disc = math.exp(-r * T)
    sign = 1.0 if k == "call" else -1.0

    payoffs = []
    for _ in range(paths):
        s = spot
        total = 0.0
        log_total = 0.0
        for _ in range(steps):
            s *= math.exp(drift + vol * rng.gauss(0.0, 1.0))
            total += s
            log_total += math.log(s)
        a = (total / steps) if avg == "arithmetic" else math.exp(log_total / steps)
        payoffs.append(max(sign * (a - strike), 0.0))

    n = len(payoffs)
    mean = sum(payoffs) / n
    var = sum((p - mean) ** 2 for p in payoffs) / (n - 1)
    price = disc * mean
    stderr = disc * math.sqrt(var / n)
    return {
        "price": price,
        "stderr": stderr,
        "ci_low": price - 1.96 * stderr,
        "ci_high": price + 1.96 * stderr,
        "paths": float(n),
    }


# --------------------------------------------------------------------------
# Discrete-time processes
# --------------------------------------------------------------------------


def gamblers_ruin_probability(
    start: float, target: float, p_win: float
) -> float:
    """Closed-form probability of reaching ``target`` before 0.

    Fair game (``p = 1/2``): ``start / target``.
    Otherwise, with ``s = (1-p)/p``: ``(1 - s^start) / (1 - s^target)``.

    The analytic answer the simulation below is checked against — and the
    reason a negative-edge game is near-certain ruin given enough rounds, a
    result that carries straight over to position sizing and leverage.
    """
    if not 0 < p_win < 1:
        raise ValueError("p_win must lie strictly between 0 and 1")
    if not 0 <= start <= target:
        raise ValueError("need 0 <= start <= target")
    if target == 0:
        raise ValueError("target must be positive")
    if abs(p_win - 0.5) < 1e-12:
        return start / target
    s = (1 - p_win) / p_win
    return (1 - s**start) / (1 - s**target)


def simulate_gamblers_ruin(
    start: int,
    target: int,
    p_win: float,
    trials: int = 10_000,
    max_steps: int = 1_000_000,
    seed: int | None = None,
) -> dict[str, float]:
    """Simulate the ruin problem; returns ``p_reach_target`` and mean duration.

    ``undecided`` counts trials that hit ``max_steps`` without absorbing.
    """
    if not 0 < p_win < 1:
        raise ValueError("p_win must lie strictly between 0 and 1")
    if not 0 < start < target:
        raise ValueError("need 0 < start < target")
    rng = _rng(seed)

    wins = 0
    undecided = 0
    durations = []
    for _ in range(trials):
        x = start
        steps = 0
        while 0 < x < target and steps < max_steps:
            x += 1 if rng.random() < p_win else -1
            steps += 1
        if x >= target:
            wins += 1
        elif x > 0:
            undecided += 1
        durations.append(steps)

    return {
        "p_reach_target": wins / trials,
        "mean_duration": sum(durations) / trials,
        "undecided": undecided / trials,
    }


def simulate_arma(
    n: int,
    ar: list[float] | None = None,
    ma: list[float] | None = None,
    const: float = 0.0,
    sigma: float = 1.0,
    seed: int | None = None,
    burn_in: int = 200,
) -> list[float]:
    """Simulate an ARMA(p, q) series.

    ``x_t = const + sum_i ar_i x_{t-i} + eps_t + sum_j ma_j eps_{t-j}``

    ``burn_in`` samples are generated and discarded so the series starts from
    something close to its stationary distribution rather than from zeros.
    """
    ar = list(ar or [])
    ma = list(ma or [])
    if n <= 0:
        raise ValueError("n must be positive")
    rng = _rng(seed)
    total = n + burn_in

    xs: list[float] = []
    eps: list[float] = []
    for t in range(total):
        e = rng.gauss(0.0, sigma)
        eps.append(e)
        value = const + e
        for i, phi in enumerate(ar, start=1):
            if t - i >= 0:
                value += phi * xs[t - i]
        for j, theta in enumerate(ma, start=1):
            if t - j >= 0:
                value += theta * eps[t - j]
        xs.append(value)
    return xs[burn_in:]


def acf(series: list[float], nlags: int = 20) -> list[float]:
    """Sample autocorrelation function, lags 0..nlags.

    Lag 0 is 1 by construction. An AR process decays geometrically in the ACF;
    an MA(q) cuts off sharply after lag q — the pairing with :func:`pacf` is
    how order is identified.
    """
    n = len(series)
    if n < 2:
        raise ValueError("need at least two observations")
    nlags = min(nlags, n - 1)
    mean = sum(series) / n
    dev = [x - mean for x in series]
    denom = sum(d * d for d in dev)
    if denom == 0:
        raise ValueError("series has zero variance")
    return [
        sum(dev[t] * dev[t + h] for t in range(n - h)) / denom
        for h in range(nlags + 1)
    ]


def pacf(series: list[float], nlags: int = 20) -> list[float]:
    """Sample partial autocorrelation by the Durbin-Levinson recursion.

    Lag 0 is 1. PACF removes the effect of the intervening lags, so an AR(p)
    cuts off after lag p while an MA process decays — the mirror image of the
    ACF, and the other half of Box-Jenkins order identification.
    """
    n = len(series)
    r = acf(series, min(nlags, n - 1))
    nlags = len(r) - 1
    out = [1.0]
    if nlags == 0:
        return out

    phi = [0.0] * (nlags + 1)
    phi[1] = r[1]
    out.append(phi[1])

    for k in range(2, nlags + 1):
        prev = phi[1:k]
        num = r[k] - sum(prev[j - 1] * r[k - j] for j in range(1, k))
        den = 1.0 - sum(prev[j - 1] * r[j] for j in range(1, k))
        phi_kk = 0.0 if abs(den) < 1e-14 else num / den
        new = [prev[j - 1] - phi_kk * prev[k - j - 1] for j in range(1, k)]
        phi[1:k] = new
        phi[k] = phi_kk
        out.append(phi_kk)
    return out
