#!/usr/bin/env python3
"""Tests for the paper runner, sentiment signal, and ML strategy. Offline, no deps.

    python projects/algo_trader/tests/test_features.py
"""

from __future__ import annotations

import sys
import tempfile
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from algo_trader.config import Config
from algo_trader.backtest.engine import Backtester
from algo_trader.data.synthetic import SyntheticFeed
from algo_trader.execution.simulated import SimulatedBroker
from algo_trader.live_runner import PaperRunner
from algo_trader.strategy.registry import create, REGISTRY
from algo_trader.signals.sentiment import (
    LexiconSentimentScorer, FeatureStore, NewsItem, build_feature_store, NewsSentimentStrategy,
)
from algo_trader.ml.features import FeatureBuilder
from algo_trader.ml.model import LogisticRegressionGD
from algo_trader.types import Side, utc


# ---- (1) paper runner ----------------------------------------------------
def test_runner_matches_backtester() -> None:
    """PaperRunner must reproduce the Backtester bar-for-bar on one symbol."""
    cfg = Config(starting_cash=10_000.0, periods_per_year=365)
    bars = list(SyntheticFeed(["SYN/USD"], bars=300, seed=5))

    bt = Backtester(cfg, create("ma_cross", fast=10, slow=30), SimulatedBroker(cfg.costs))
    bt_res = bt.run(iter(bars))

    runner = PaperRunner(cfg, create("ma_cross", fast=10, slow=30))
    for b in bars:
        runner.step(b)

    assert abs(runner.equity_history[-1] - bt_res.metrics.end_equity) < 1e-6
    assert len(runner.portfolio.trades) == bt_res.metrics.num_trades
    print(f"ok  paper runner matches backtester (equity {runner.equity_history[-1]:,.2f})")


def test_runner_state_roundtrip() -> None:
    cfg = Config(starting_cash=10_000.0)
    bars = list(SyntheticFeed(["SYN/USD"], bars=120, seed=9))
    r1 = PaperRunner(cfg, create("ma_cross", fast=5, slow=20))
    for b in bars[:60]:
        r1.step(b)

    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "state.json")
        r1.save_state(path)
        r2 = PaperRunner(cfg, create("ma_cross", fast=5, slow=20))
        r2.load_state(path)
        assert abs(r2.portfolio.cash - r1.portfolio.cash) < 1e-9
        assert r2.portfolio.positions.keys() == r1.portfolio.positions.keys()
        assert r2._pending.keys() == r1._pending.keys()
    print("ok  paper runner state round-trips")


# ---- (2) sentiment signal ------------------------------------------------
def test_lexicon_scorer_polarity_and_negation() -> None:
    s = LexiconSentimentScorer()
    assert s.score("Company beats earnings, profit surges to record") > 0.3
    assert s.score("Stock plunges on fraud probe and lawsuit") < -0.3
    assert s.score("The results were not strong") < 0.0   # negation flips
    assert s.score("the cat sat on the mat") == 0.0        # no finance words
    print("ok  lexicon sentiment polarity + negation")


def test_feature_store_no_lookahead() -> None:
    store = FeatureStore()
    store.add("X", utc(2023, 1, 10), 0.8)
    assert store.latest("X", utc(2023, 1, 9)) is None      # before the news
    assert store.latest("X", utc(2023, 1, 10)) == 0.8       # at the news
    assert store.latest("X", utc(2023, 1, 11)) == 0.8       # after → carries
    print("ok  feature store enforces no-lookahead")


def test_news_sentiment_strategy_trades() -> None:
    cfg = Config(starting_cash=10_000.0)
    bars = list(SyntheticFeed(["SYN/USD"], bars=120, seed=2))
    mid = bars[len(bars) // 2].ts
    items = [
        NewsItem(bars[10].ts, "SYN/USD", "record profit, shares surge, strong upgrade"),
        NewsItem(mid, "SYN/USD", "lawsuit and fraud probe, guidance cut, plunge"),
    ]
    store = build_feature_store(items, LexiconSentimentScorer())
    strat = NewsSentimentStrategy(store=store, enter=0.3, exit=0.05)
    res = Backtester(cfg, strat, SimulatedBroker(cfg.costs)).run(iter(bars))
    assert res.metrics.num_trades >= 1   # bullish item opens, bearish closes
    print(f"ok  news-sentiment strategy trades ({res.metrics.num_trades} trades)")


# ---- (3) ML strategy -----------------------------------------------------
def test_feature_builder_shape() -> None:
    fb = FeatureBuilder(lookback=20)
    vec = None
    for i in range(25):
        vec = fb.update(100 + i)
    assert vec is not None and len(vec) == fb.n_features == 6
    print("ok  feature builder emits fixed-length vectors")


def test_logreg_learns_separable() -> None:
    # feature0 positive → class 1, negative → class 0 (with a little noise dim).
    X, y = [], []
    for k in range(-10, 11):
        if k == 0:
            continue
        X.append([float(k), 0.1 * k])
        y.append(1 if k > 0 else 0)
    model = LogisticRegressionGD(lr=0.5, epochs=500).fit(X, y)
    assert model.predict_proba_up([5.0, 0.5]) > 0.8
    assert model.predict_proba_up([-5.0, -0.5]) < 0.2
    print("ok  logistic regression learns a separable set")


def test_ml_strategy_registered_and_runs() -> None:
    assert "ml_scored" in REGISTRY
    cfg = Config(starting_cash=10_000.0)
    strat = create("ml_scored", lookback=20, horizon=3, min_train=40, retrain_every=20)
    res = Backtester(cfg, strat, SimulatedBroker(cfg.costs)).run(
        SyntheticFeed(["SYN/USD"], bars=300, seed=4))
    assert len(res.equity_curve) == 300
    print(f"ok  ml_scored strategy runs ({res.metrics.num_trades} trades, "
          f"end {res.metrics.end_equity:,.2f})")


def test_ml_no_trade_before_min_train() -> None:
    """No model, no trades: with min_train high, the early book stays flat."""
    cfg = Config(starting_cash=10_000.0)
    strat = create("ml_scored", lookback=10, horizon=5, min_train=200, retrain_every=10)
    # Only 120 bars < lookback+horizon+min_train warmup → never trains → no trades.
    res = Backtester(cfg, strat, SimulatedBroker(cfg.costs)).run(
        SyntheticFeed(["SYN/USD"], bars=120, seed=1))
    assert res.metrics.num_trades == 0
    print("ok  ml_scored does not trade before it can train (no lookahead)")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
    print(f"\nAll {len(fns)} feature/runner/ml tests passed.")
