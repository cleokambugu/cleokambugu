#!/usr/bin/env python3
"""Deterministic tests — no network, no external deps. Run:

    python projects/algo_trader/tests/test_algo_trader.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from algo_trader.config import Config, LiveGate, RiskLimits, LIVE_ENV_FLAG
from algo_trader.portfolio import Portfolio
from algo_trader.risk import RiskManager
from algo_trader.backtest.engine import Backtester
from algo_trader.backtest.metrics import compute_metrics, max_drawdown
from algo_trader.data.synthetic import SyntheticFeed
from algo_trader.data.base import DataFeed
from algo_trader.execution.simulated import SimulatedBroker
from algo_trader.execution.live import LiveBroker, LiveTradingBlocked
from algo_trader.strategy.ma_cross import MACrossStrategy
from algo_trader.strategy.registry import create, REGISTRY
from algo_trader.optimize import walk_forward
from algo_trader.types import Bar, Fill, Order, Side, Signal, utc


# --- portfolio accounting -------------------------------------------------
def test_portfolio_roundtrip_pnl() -> None:
    pf = Portfolio(1000.0)
    pf.apply_fill(Fill("X", Side.BUY, 10, 100.0, utc(2023, 1, 1), fee=0.0))
    assert pf.cash == 0.0
    assert pf.position("X").quantity == 10
    pf.apply_fill(Fill("X", Side.SELL, 10, 110.0, utc(2023, 1, 2), fee=0.0))
    assert pf.position("X").quantity == 0
    assert abs(pf.cash - 1100.0) < 1e-9          # +100 profit
    assert len(pf.trades) == 1 and abs(pf.trades[0].pnl - 100.0) < 1e-9
    print("ok  portfolio round-trip PnL")


def test_portfolio_fees_reduce_cash() -> None:
    pf = Portfolio(1000.0)
    pf.apply_fill(Fill("X", Side.BUY, 1, 100.0, utc(2023, 1, 1), fee=5.0))
    assert abs(pf.cash - 895.0) < 1e-9
    print("ok  fees reduce cash")


# --- risk manager ---------------------------------------------------------
def test_risk_caps_position_weight() -> None:
    limits = RiskLimits(max_position_weight=0.10, allow_short=False)
    rm = RiskManager(limits)
    pf = Portfolio(10_000.0)
    prices = {"X": 100.0}
    # Strategy wants 50% weight; risk must cap to 10% -> $1000 -> 10 units.
    sig = Signal("X", Side.BUY, utc(2023, 1, 1), target_weight=0.50)
    dec = rm.evaluate(sig, pf, prices)
    assert dec.order is not None
    assert abs(dec.order.quantity - 10.0) < 1e-9, dec.order.quantity
    print("ok  risk caps position weight")


def test_risk_blocks_short_when_disallowed() -> None:
    rm = RiskManager(RiskLimits(allow_short=False))
    pf = Portfolio(10_000.0)
    sig = Signal("X", Side.SELL, utc(2023, 1, 1), target_weight=-0.2)
    dec = rm.evaluate(sig, pf, {"X": 100.0})
    assert dec.order is None  # long-only: nothing to do from flat
    print("ok  risk blocks short when disallowed")


def test_risk_daily_loss_halt() -> None:
    rm = RiskManager(RiskLimits(max_daily_loss=0.03))
    d = utc(2023, 1, 1).date()
    rm.update_marks(10_000.0, d)
    assert not rm.halted
    rm.update_marks(9_600.0, d)  # -4% on the day
    assert rm.halted and "daily loss" in rm.halt_reason
    print("ok  risk daily-loss kill switch")


# --- execution gate (the important safety test) ---------------------------
def test_live_broker_blocked_by_default() -> None:
    os.environ.pop(LIVE_ENV_FLAG, None)
    try:
        LiveBroker(LiveGate())
    except LiveTradingBlocked as e:
        assert LIVE_ENV_FLAG in str(e)
    else:
        raise AssertionError("LiveBroker must refuse to construct by default")
    print("ok  live broker blocked by default")


def test_live_broker_blocked_without_ack_even_with_env() -> None:
    os.environ[LIVE_ENV_FLAG] = "1"
    try:
        # env set but no paper-first acknowledgement -> still blocked
        LiveBroker(LiveGate(acknowledged_paper_first=False))
    except LiveTradingBlocked:
        pass
    else:
        raise AssertionError("must still block without paper-first acknowledgement")
    finally:
        os.environ.pop(LIVE_ENV_FLAG, None)
    print("ok  live broker still blocked without acknowledgement")


def test_live_broker_gate_open_but_no_venue() -> None:
    os.environ[LIVE_ENV_FLAG] = "1"
    try:
        broker = LiveBroker(LiveGate(acknowledged_paper_first=True))  # constructs now
        bar = Bar("X", utc(2023, 1, 1), 100, 100, 100, 100)
        try:
            broker.submit(Order("X", Side.BUY, 1, bar.ts), bar)
        except LiveTradingBlocked as e:
            assert "No venue client" in str(e)
        else:
            raise AssertionError("must refuse to submit with no venue wired")
    finally:
        os.environ.pop(LIVE_ENV_FLAG, None)
    print("ok  live broker refuses submit with no venue wired")


# --- no-lookahead execution ----------------------------------------------
class _TwoBars(DataFeed):
    """Signal fires on bar 1's close; must fill at bar 2's open, not bar 1."""

    def __iter__(self):
        yield Bar("X", utc(2023, 1, 1), open=100, high=101, low=99, close=100)
        yield Bar("X", utc(2023, 1, 2), open=105, high=106, low=104, close=105)


class _BuyOnceStrategy(MACrossStrategy):
    def __init__(self):
        super().__init__(fast=1, slow=2, target_weight=0.5)
        self._fired = False

    def on_bar(self, bar):
        if not self._fired:
            self._fired = True
            return [Signal(bar.symbol, Side.BUY, bar.ts, 0.5, "test buy")]
        return []


def test_no_lookahead_fill_at_next_open() -> None:
    cfg = Config(starting_cash=10_000.0)
    cfg.costs.fee_rate = 0.0
    cfg.costs.slippage_rate = 0.0
    bt = Backtester(cfg, _BuyOnceStrategy(), SimulatedBroker(cfg.costs))
    result = bt.run(_TwoBars())
    # Bought at bar 2 open (105), not bar 1 close (100).
    pos = bt.portfolio.position("X")
    assert pos.quantity > 0
    assert abs(pos.avg_price - 105.0) < 1e-9, pos.avg_price
    print("ok  no-lookahead: filled at next bar open")


# --- metrics --------------------------------------------------------------
def test_metrics_basic() -> None:
    eq = [100.0, 110.0, 105.0, 121.0]
    m = compute_metrics(eq, [], periods_per_year=252)
    assert abs(m.total_return - 0.21) < 1e-9
    assert abs(max_drawdown([100, 120, 60, 90]) - (-0.5)) < 1e-9
    print("ok  metrics basic")


# --- end-to-end backtest + strategies ------------------------------------
def test_backtest_runs_and_is_deterministic() -> None:
    cfg = Config(starting_cash=10_000.0, periods_per_year=365)
    feed = SyntheticFeed(["SYN/USD"], bars=400, seed=7)
    r1 = Backtester(cfg, create("ma_cross", fast=10, slow=30), SimulatedBroker(cfg.costs)).run(feed)
    r2 = Backtester(cfg, create("ma_cross", fast=10, slow=30), SimulatedBroker(cfg.costs)).run(
        SyntheticFeed(["SYN/USD"], bars=400, seed=7))
    assert len(r1.equity_curve) == 400
    assert abs(r1.metrics.end_equity - r2.metrics.end_equity) < 1e-6  # deterministic
    print(f"ok  backtest deterministic (end equity {r1.metrics.end_equity:,.2f}, "
          f"{r1.metrics.num_trades} trades)")


def test_rsi_strategy_registered_and_runs() -> None:
    assert "rsi_meanrev" in REGISTRY
    cfg = Config(starting_cash=10_000.0)
    r = Backtester(cfg, create("rsi_meanrev"), SimulatedBroker(cfg.costs)).run(
        SyntheticFeed(["SYN/USD"], bars=300, seed=3))
    assert len(r.equity_curve) == 300
    print("ok  rsi strategy runs")


def test_walk_forward_optimize() -> None:
    cfg = Config(starting_cash=10_000.0)
    feed = SyntheticFeed(["SYN/USD"], bars=400, seed=11)
    res = walk_forward(cfg, "ma_cross", {"fast": [10, 20], "slow": [50, 100]}, feed)
    assert res.best_params.get("fast") in (10, 20)
    print(f"ok  walk-forward optimize (best {res.best_params}, "
          f"IS {res.in_sample_sharpe:.2f} / OOS {res.out_sample_sharpe:.2f})")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
    print(f"\nAll {len(fns)} algo_trader tests passed.")
