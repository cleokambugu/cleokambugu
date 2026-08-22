"""Paper-trading runner: the same engine as the backtester, but stateful and
incremental, so it can run against a live/paper data stream and survive restarts.

Semantics deliberately match `backtest.engine.Backtester` bar-for-bar (single
symbol): a signal formed on a bar is executed at the *next* bar's open, equity is
marked once per bar, and the risk kill-switch flattens and halts. An equivalence
test asserts the runner and backtester produce identical results on the same feed.

Only paper/backtest brokers are used here. Live order routing stays hard-gated in
execution/live.py — this runner never constructs it for you.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Callable, Dict, Iterable, List, Optional

from .config import Config
from .execution.base import Broker
from .execution.simulated import SimulatedBroker
from .portfolio import Portfolio
from .risk import RiskManager
from .strategy.base import Strategy
from .types import Bar, Order, Position, Side, TradeRecord


@dataclass
class StepSnapshot:
    ts: datetime
    equity: float
    cash: float
    positions: Dict[str, float]
    halted: bool
    last_action: str


class PaperRunner:
    """Drives strategy → risk → (paper) broker incrementally, one bar at a time."""

    def __init__(self, config: Config, strategy: Strategy, broker: Optional[Broker] = None) -> None:
        problems = config.validate()
        if problems:
            raise ValueError("invalid config: " + "; ".join(problems))
        self.config = config
        self.strategy = strategy
        self.broker = broker or SimulatedBroker(config.costs)
        self.portfolio = Portfolio(config.starting_cash)
        self.risk = RiskManager(config.risk)
        self._pending: Dict[str, Order] = {}
        self._last_price: Dict[str, float] = {}
        self._flattening = False
        self.equity_history: List[float] = []
        self.ts_history: List[datetime] = []

    # --- core step (mirrors the backtester's per-timestamp logic) ----------
    def step(self, bar: Bar) -> StepSnapshot:
        action = "hold"

        # 1) Execute any order queued from the previous bar, at this bar's open.
        order = self._pending.pop(bar.symbol, None)
        if order is not None:
            fill = self.broker.submit(order, bar)
            if fill is not None:
                self.portfolio.apply_fill(fill)
                action = f"fill {order.side.value} {order.quantity:.6g} @ {fill.price:.4f}"
        self._last_price[bar.symbol] = bar.close

        # 2) Mark equity for this bar.
        equity = self.portfolio.equity(self._last_price)
        self.equity_history.append(equity)
        self.ts_history.append(bar.ts)

        # 3) Risk marks / kill switch.
        self.risk.update_marks(equity, bar.ts.date())
        if self.risk.halted and not self._flattening:
            self._flattening = True
            for sym, pos in self.portfolio.positions.items():
                if pos.quantity != 0:
                    side = Side.SELL if pos.quantity > 0 else Side.BUY
                    self._pending[sym] = Order(sym, side, abs(pos.quantity), bar.ts,
                                               reason=f"risk halt: {self.risk.halt_reason}")
            action = f"HALT: {self.risk.halt_reason}"
        elif not self._flattening:
            # 4) Strategy + risk sizing.
            for signal in self.strategy.on_bar(bar):
                decision = self.risk.evaluate(signal, self.portfolio, self._last_price)
                if decision.order is not None:
                    self._pending[bar.symbol] = decision.order
                    action = f"queue {decision.order.side.value} {decision.order.quantity:.6g}"

        return StepSnapshot(
            ts=bar.ts,
            equity=equity,
            cash=self.portfolio.cash,
            positions={s: p.quantity for s, p in self.portfolio.positions.items() if p.quantity != 0},
            halted=self.risk.halted,
            last_action=action,
        )

    def run(
        self,
        feed: Iterable[Bar],
        sleep_seconds: float = 0.0,
        max_steps: Optional[int] = None,
        on_step: Optional[Callable[[StepSnapshot], None]] = None,
        state_path: Optional[str] = None,
    ) -> List[StepSnapshot]:
        """Process bars from `feed`. For a true live loop, pass a PollingFeed and a
        sleep interval. Persists state after each step if `state_path` is given."""
        snaps: List[StepSnapshot] = []
        for i, bar in enumerate(feed):
            snap = self.step(bar)
            snaps.append(snap)
            if on_step:
                on_step(snap)
            if state_path:
                self.save_state(state_path)
            if max_steps is not None and i + 1 >= max_steps:
                break
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
        return snaps

    # --- state persistence (survive restarts) ------------------------------
    def save_state(self, path: str) -> None:
        state = {
            "cash": self.portfolio.cash,
            "starting_cash": self.portfolio.starting_cash,
            "positions": {
                s: {"quantity": p.quantity, "avg_price": p.avg_price, "realized_pnl": p.realized_pnl}
                for s, p in self.portfolio.positions.items()
            },
            "open_ts": {s: t.isoformat() for s, t in self.portfolio._open_ts.items()},
            "trades": [
                {"symbol": t.symbol, "opened": t.opened.isoformat(), "closed": t.closed.isoformat(),
                 "quantity": t.quantity, "entry_price": t.entry_price, "exit_price": t.exit_price,
                 "pnl": t.pnl}
                for t in self.portfolio.trades
            ],
            "pending": {
                s: {"side": o.side.value, "quantity": o.quantity, "ts": o.ts.isoformat(),
                    "reason": o.reason}
                for s, o in self._pending.items()
            },
            "last_price": self._last_price,
            "flattening": self._flattening,
            "risk": {
                "peak_equity": self.risk._peak_equity,
                "day": self.risk._day.isoformat() if self.risk._day else None,
                "day_start_equity": self.risk._day_start_equity,
                "halted": self.risk._halted,
                "halt_reason": self.risk.halt_reason,
            },
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2)

    def load_state(self, path: str) -> None:
        with open(path, encoding="utf-8") as fh:
            state = json.load(fh)
        pf = self.portfolio
        pf.cash = state["cash"]
        pf.starting_cash = state["starting_cash"]
        pf.positions = {
            s: Position(symbol=s, quantity=d["quantity"], avg_price=d["avg_price"],
                        realized_pnl=d["realized_pnl"])
            for s, d in state["positions"].items()
        }
        pf._open_ts = {s: datetime.fromisoformat(t) for s, t in state["open_ts"].items()}
        pf.trades = [
            TradeRecord(symbol=t["symbol"], opened=datetime.fromisoformat(t["opened"]),
                        closed=datetime.fromisoformat(t["closed"]), quantity=t["quantity"],
                        entry_price=t["entry_price"], exit_price=t["exit_price"], pnl=t["pnl"])
            for t in state["trades"]
        ]
        self._pending = {
            s: Order(symbol=s, side=Side(o["side"]), quantity=o["quantity"],
                     ts=datetime.fromisoformat(o["ts"]), reason=o["reason"])
            for s, o in state["pending"].items()
        }
        self._last_price = dict(state["last_price"])
        self._flattening = state["flattening"]
        r = state["risk"]
        self.risk._peak_equity = r["peak_equity"]
        self.risk._day = date.fromisoformat(r["day"]) if r["day"] else None
        self.risk._day_start_equity = r["day_start_equity"]
        self.risk._halted = r["halted"]
        self.risk.halt_reason = r["halt_reason"]


class PollingFeed:
    """Adapt a 'fetch latest bars' function into a bar stream that yields only
    NEW bars (dedup by (symbol, ts)). Use for a real paper loop that polls a venue.

    Example:
        def fetch(): return list(CcxtHistoricalFeed("binance", "BTC/USDT", limit=2))
        feed = PollingFeed(fetch, interval_seconds=60, max_polls=1440)
    """

    def __init__(self, fetch: Callable[[], Iterable[Bar]], interval_seconds: float = 60.0,
                 max_polls: Optional[int] = None) -> None:
        self.fetch = fetch
        self.interval_seconds = interval_seconds
        self.max_polls = max_polls
        self._seen: set = set()

    def __iter__(self):
        polls = 0
        while self.max_polls is None or polls < self.max_polls:
            for bar in sorted(self.fetch(), key=lambda b: b.ts):
                key = (bar.symbol, bar.ts)
                if key not in self._seen:
                    self._seen.add(key)
                    yield bar
            polls += 1
            if self.max_polls is not None and polls >= self.max_polls:
                break
            if self.interval_seconds > 0:
                time.sleep(self.interval_seconds)
