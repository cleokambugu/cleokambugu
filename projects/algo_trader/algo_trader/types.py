"""Core value types shared across the system.

Deliberately plain dataclasses with no external dependencies, so the whole engine
runs on a bare Python install and every layer speaks the same vocabulary.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


class Side(enum.Enum):
    """Direction of an order or target position."""

    BUY = "buy"
    SELL = "sell"
    FLAT = "flat"  # signal to close any open position


class Mode(enum.Enum):
    """Execution mode. Only BACKTEST and PAPER are reachable without opt-in."""

    BACKTEST = "backtest"
    PAPER = "paper"
    LIVE = "live"  # hard-gated; see execution/live.py


@dataclass(frozen=True)
class Bar:
    """One OHLCV candle for a symbol at a point in time (tz-aware UTC)."""

    symbol: str
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def __post_init__(self) -> None:
        if self.ts.tzinfo is None:
            raise ValueError("Bar.ts must be timezone-aware (UTC)")
        if self.high < self.low:
            raise ValueError(f"Bar high < low for {self.symbol} @ {self.ts}")


@dataclass(frozen=True)
class Signal:
    """A strategy's intent for a symbol.

    :param target_weight: desired fraction of total equity to hold in this symbol,
        in [-1, 1]. 0 means flat. The risk manager turns this into a sized order.
    :param reason: human-readable explanation (kept for transparency/tracing).
    """

    symbol: str
    side: Side
    ts: datetime
    target_weight: float = 0.0
    reason: str = ""

    def __post_init__(self) -> None:
        if not -1.0 <= self.target_weight <= 1.0:
            raise ValueError("target_weight must be within [-1, 1]")


@dataclass(frozen=True)
class Order:
    """An instruction to trade a quantity of a symbol."""

    symbol: str
    side: Side
    quantity: float  # always positive; direction is in `side`
    ts: datetime
    reason: str = ""

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("Order.quantity must be positive")
        if self.side is Side.FLAT:
            raise ValueError("Order.side cannot be FLAT; emit BUY/SELL")


@dataclass(frozen=True)
class Fill:
    """The result of executing an order."""

    symbol: str
    side: Side
    quantity: float
    price: float
    ts: datetime
    fee: float = 0.0
    slippage: float = 0.0


@dataclass
class Position:
    """A held position with running average cost."""

    symbol: str
    quantity: float = 0.0       # signed: negative = short
    avg_price: float = 0.0
    realized_pnl: float = 0.0

    def market_value(self, price: float) -> float:
        return self.quantity * price

    def unrealized_pnl(self, price: float) -> float:
        return (price - self.avg_price) * self.quantity


@dataclass
class TradeRecord:
    """A round-trip (or partial) close, used for win-rate stats."""

    symbol: str
    opened: datetime
    closed: datetime
    quantity: float
    entry_price: float
    exit_price: float
    pnl: float


def utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """Small helper for constructing tz-aware timestamps in tests and feeds."""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
