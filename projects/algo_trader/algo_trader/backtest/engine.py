"""Event-driven backtester.

Design choices that matter for honesty of results:

- **Next-bar execution.** A signal formed on bar t is executed at bar t+1's open,
  never on the same close it was computed from. This is the single most important
  guard against look-ahead bias (the mistake that makes a backtest lie).
- **One equity mark per timestamp**, so metrics aren't inflated by multi-symbol
  interleaving.
- **The risk manager is in the loop**, not advisory: when it halts, the engine
  flattens all positions on the next bar and stops opening new ones.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from itertools import groupby
from typing import Dict, List, Optional

from ..config import Config
from ..data.base import DataFeed
from ..execution.base import Broker
from ..portfolio import Portfolio
from ..risk import RiskManager
from ..strategy.base import Strategy
from ..types import Bar, Order, Side, TradeRecord
from .metrics import Metrics, compute_metrics


@dataclass
class BacktestResult:
    equity_curve: List[float]
    timestamps: List[datetime]
    trades: List[TradeRecord]
    metrics: Metrics
    halted: bool
    halt_reason: str
    final_cash: float
    final_positions: Dict[str, float] = field(default_factory=dict)


class Backtester:
    def __init__(self, config: Config, strategy: Strategy, broker: Broker) -> None:
        problems = config.validate()
        if problems:
            raise ValueError("invalid config: " + "; ".join(problems))
        self.config = config
        self.strategy = strategy
        self.broker = broker
        self.portfolio = Portfolio(config.starting_cash)
        self.risk = RiskManager(config.risk)

    def run(self, feed: DataFeed) -> BacktestResult:
        last_price: Dict[str, float] = {}
        pending: Dict[str, Order] = {}
        equity_curve: List[float] = []
        timestamps: List[datetime] = []
        flattening = False

        for ts, group_iter in groupby(feed, key=lambda b: b.ts):
            group: List[Bar] = list(group_iter)

            # 1) Execute orders queued on the previous timestamp, at this bar's open.
            for bar in group:
                order = pending.pop(bar.symbol, None)
                if order is not None:
                    fill = self.broker.submit(order, bar)
                    if fill is not None:
                        self.portfolio.apply_fill(fill)
                last_price[bar.symbol] = bar.close

            # 2) Mark equity once for this timestamp.
            equity = self.portfolio.equity(last_price)
            equity_curve.append(equity)
            timestamps.append(ts)

            # 3) Risk marks / kill switch.
            self.risk.update_marks(equity, ts.date())
            if self.risk.halted and not flattening:
                # Queue flattening orders for all open positions; stop new signals.
                flattening = True
                for sym, pos in self.portfolio.positions.items():
                    if pos.quantity != 0:
                        side = Side.SELL if pos.quantity > 0 else Side.BUY
                        pending[sym] = Order(sym, side, abs(pos.quantity), ts,
                                             reason=f"risk halt: {self.risk.halt_reason}")
                continue
            if flattening or self.risk.halted:
                continue

            # 4) Strategy sees each bar; risk sizes any resulting orders.
            for bar in group:
                for signal in self.strategy.on_bar(bar):
                    decision = self.risk.evaluate(signal, self.portfolio, last_price)
                    if decision.order is not None:
                        pending[bar.symbol] = decision.order  # supersede stale intent

        if not equity_curve:
            raise ValueError("feed produced no bars")

        metrics = compute_metrics(equity_curve, self.portfolio.trades,
                                  self.config.periods_per_year)
        return BacktestResult(
            equity_curve=equity_curve,
            timestamps=timestamps,
            trades=self.portfolio.trades,
            metrics=metrics,
            halted=self.risk.halted,
            halt_reason=self.risk.halt_reason,
            final_cash=self.portfolio.cash,
            final_positions={s: p.quantity for s, p in self.portfolio.positions.items()
                             if p.quantity != 0},
        )
