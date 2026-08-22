"""Portfolio accounting: cash, positions, equity, and closed-trade records."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from .types import Fill, Position, Side, TradeRecord


class Portfolio:
    """Tracks cash and positions, applies fills, marks equity to market.

    Average-cost accounting. Supports long and short. Realized PnL is booked when
    a position is reduced or flipped.
    """

    def __init__(self, starting_cash: float) -> None:
        self.starting_cash = starting_cash
        self.cash = starting_cash
        self.positions: Dict[str, Position] = {}
        self.trades: List[TradeRecord] = []
        self._open_ts: Dict[str, datetime] = {}

    def position(self, symbol: str) -> Position:
        return self.positions.setdefault(symbol, Position(symbol=symbol))

    def apply_fill(self, fill: Fill) -> None:
        """Update cash and the affected position from an executed fill."""
        pos = self.position(fill.symbol)
        signed = fill.quantity if fill.side is Side.BUY else -fill.quantity

        # Cash: buying spends, selling receives; fees always cost.
        self.cash -= signed * fill.price
        self.cash -= fill.fee

        prev_qty = pos.quantity
        new_qty = prev_qty + signed

        if prev_qty == 0 or (prev_qty > 0) == (signed > 0):
            # Opening or increasing in the same direction → blend average price.
            if new_qty != 0:
                pos.avg_price = (pos.avg_price * prev_qty + fill.price * signed) / new_qty
            if prev_qty == 0:
                self._open_ts[fill.symbol] = fill.ts
        else:
            # Reducing, closing, or flipping → realize PnL on the closed amount.
            closed_qty = min(abs(signed), abs(prev_qty))
            direction = 1 if prev_qty > 0 else -1
            pnl = (fill.price - pos.avg_price) * closed_qty * direction
            pos.realized_pnl += pnl
            self.trades.append(
                TradeRecord(
                    symbol=fill.symbol,
                    opened=self._open_ts.get(fill.symbol, fill.ts),
                    closed=fill.ts,
                    quantity=closed_qty,
                    entry_price=pos.avg_price,
                    exit_price=fill.price,
                    pnl=pnl,
                )
            )
            if new_qty == 0:
                pos.avg_price = 0.0
                self._open_ts.pop(fill.symbol, None)
            elif (new_qty > 0) != (prev_qty > 0):
                # Flipped past zero: remaining qty opens a new position at fill price.
                pos.avg_price = fill.price
                self._open_ts[fill.symbol] = fill.ts

        pos.quantity = new_qty

    def equity(self, prices: Dict[str, float]) -> float:
        """Mark-to-market total equity = cash + sum(position market values)."""
        total = self.cash
        for sym, pos in self.positions.items():
            if pos.quantity != 0:
                price = prices.get(sym)
                if price is None:
                    raise KeyError(f"no mark price for open position {sym}")
                total += pos.market_value(price)
        return total

    def gross_exposure(self, prices: Dict[str, float]) -> float:
        """Sum of |position value| / equity — the leverage check input."""
        eq = self.equity(prices)
        if eq <= 0:
            return float("inf")
        gross = sum(
            abs(pos.market_value(prices[sym]))
            for sym, pos in self.positions.items()
            if pos.quantity != 0
        )
        return gross / eq
