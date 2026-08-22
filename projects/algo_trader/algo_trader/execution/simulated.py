"""Simulated broker for backtest and paper modes.

Fills at the reference bar's price with adverse slippage and a fee. In the
backtester the reference bar is the *next* bar after the signal, which is how we
avoid look-ahead bias (you cannot trade on a close using that same close).
"""

from __future__ import annotations

from typing import Optional

from ..config import CostModel
from ..types import Bar, Fill, Order, Side
from .base import Broker


class SimulatedBroker(Broker):
    def __init__(self, costs: CostModel) -> None:
        self.costs = costs

    def submit(self, order: Order, ref_bar: Bar) -> Optional[Fill]:
        # Fill at the open of the reference bar (the executable price), nudged by
        # slippage against us: buys fill a touch higher, sells a touch lower.
        base = ref_bar.open
        slip = base * self.costs.slippage_rate
        if order.side is Side.BUY:
            price = base + slip
        else:
            price = base - slip
        fee = price * order.quantity * self.costs.fee_rate
        return Fill(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=price,
            ts=ref_bar.ts,
            fee=fee,
            slippage=slip * order.quantity,
        )
