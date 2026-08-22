"""Risk management: turn a strategy signal into a safely-sized order, and halt
trading when protective limits are breached.

This layer exists so a strategy can be as aggressive as it likes while the
account stays bounded. Every order in the system passes through here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Optional

from .config import RiskLimits
from .portfolio import Portfolio
from .types import Order, Side, Signal


@dataclass
class RiskDecision:
    """Outcome of evaluating a signal: an order to place (or None), plus a note."""

    order: Optional[Order]
    note: str
    halt: bool = False


class RiskManager:
    """Position sizing + hard limits + daily-loss / drawdown kill switch."""

    def __init__(self, limits: RiskLimits) -> None:
        self.limits = limits
        self._peak_equity: float = 0.0
        self._day: Optional[date] = None
        self._day_start_equity: float = 0.0
        self._halted: bool = False
        self.halt_reason: str = ""

    # --- kill switch -------------------------------------------------------
    def update_marks(self, equity: float, day: date) -> None:
        """Call once per bar with current equity. Trips the halt if breached."""
        if self._day != day:
            self._day = day
            self._day_start_equity = equity
        self._peak_equity = max(self._peak_equity, equity)

        if self._day_start_equity > 0:
            daily_ret = (equity - self._day_start_equity) / self._day_start_equity
            if daily_ret <= -self.limits.max_daily_loss:
                self._trip(f"daily loss {daily_ret:.2%} ≤ -{self.limits.max_daily_loss:.0%}")
        if self._peak_equity > 0:
            dd = (equity - self._peak_equity) / self._peak_equity
            if dd <= -self.limits.max_drawdown_halt:
                self._trip(f"drawdown {dd:.2%} ≤ -{self.limits.max_drawdown_halt:.0%}")

    def _trip(self, reason: str) -> None:
        if not self._halted:
            self._halted = True
            self.halt_reason = reason

    @property
    def halted(self) -> bool:
        return self._halted

    # --- sizing ------------------------------------------------------------
    def evaluate(
        self,
        signal: Signal,
        portfolio: Portfolio,
        prices: Dict[str, float],
    ) -> RiskDecision:
        """Convert a signal into a sized, limit-checked order (or a reason not to)."""
        if self._halted:
            return RiskDecision(None, f"halted: {self.halt_reason}", halt=True)

        price = prices.get(signal.symbol)
        if price is None or price <= 0:
            return RiskDecision(None, "no valid price")

        equity = portfolio.equity(prices)
        if equity <= 0:
            return RiskDecision(None, "non-positive equity", halt=True)

        pos = portfolio.position(signal.symbol)

        # Resolve desired target weight, applying caps and the short policy.
        target_w = 0.0 if signal.side is Side.FLAT else signal.target_weight
        if not self.limits.allow_short:
            target_w = max(0.0, target_w)
        cap = self.limits.max_position_weight
        target_w = max(-cap, min(cap, target_w))

        target_qty = target_w * equity / price
        delta_qty = target_qty - pos.quantity
        if abs(delta_qty * price) < 1e-9 or abs(delta_qty) < 1e-12:
            return RiskDecision(None, "already at target")

        # Gross-exposure check on the resulting book.
        projected_gross = self._projected_gross(portfolio, prices, signal.symbol, target_qty, equity)
        if projected_gross > self.limits.max_gross_exposure + 1e-9:
            return RiskDecision(
                None,
                f"blocked: gross exposure {projected_gross:.2f} > "
                f"{self.limits.max_gross_exposure:.2f}",
            )

        side = Side.BUY if delta_qty > 0 else Side.SELL
        order = Order(
            symbol=signal.symbol,
            side=side,
            quantity=abs(delta_qty),
            ts=signal.ts,
            reason=signal.reason or f"target_weight={target_w:.3f}",
        )
        return RiskDecision(order, f"sized to weight {target_w:.3f}")

    def _projected_gross(
        self,
        portfolio: Portfolio,
        prices: Dict[str, float],
        symbol: str,
        new_qty: float,
        equity: float,
    ) -> float:
        gross = 0.0
        for sym, pos in portfolio.positions.items():
            qty = new_qty if sym == symbol else pos.quantity
            if qty != 0:
                gross += abs(qty * prices[sym])
        if symbol not in portfolio.positions and new_qty != 0:
            gross += abs(new_qty * prices[symbol])
        return gross / equity if equity > 0 else float("inf")
