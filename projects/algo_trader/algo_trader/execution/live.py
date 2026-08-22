"""Live broker — HARD-GATED. Fails closed.

This class deliberately refuses to do anything until an operator has:
  1. set the environment flag ALGO_TRADER_ALLOW_LIVE=1, and
  2. passed a LiveGate that acknowledges paper trading was validated first.

Even after construction, every submit() re-checks the gate. The actual venue
integration (ccxt / Alpaca) is intentionally left as a clearly-marked adapter
point: wiring a real order-placement call is a decision the operator makes
consciously, with their own keys, after the safety gates pass — not something
that ships enabled.

Nothing here bypasses any exchange rule, rate limit, or terms of service.
"""

from __future__ import annotations

from typing import Optional

from ..config import LiveGate
from ..types import Bar, Fill, Order
from .base import Broker


class LiveTradingBlocked(RuntimeError):
    """Raised when live trading is attempted without passing the gate."""


class LiveBroker(Broker):
    def __init__(self, gate: LiveGate, venue_client: object | None = None) -> None:
        """:param venue_client: an authenticated exchange/broker client the
        operator constructs themselves (e.g. a ccxt exchange or Alpaca client).
        Left None here on purpose."""
        blocked = gate.reasons_blocked()
        if blocked:
            raise LiveTradingBlocked(
                "Live trading is disabled. Resolve all of the following, then "
                "construct LiveBroker again:\n  - " + "\n  - ".join(blocked)
            )
        self.gate = gate
        self.venue = venue_client

    def submit(self, order: Order, ref_bar: Bar) -> Optional[Fill]:
        # Re-check the gate on every order — construction alone is not a licence.
        blocked = self.gate.reasons_blocked()
        if blocked:
            raise LiveTradingBlocked("Live gate closed at submit: " + "; ".join(blocked))
        if self.venue is None:
            raise LiveTradingBlocked(
                "No venue client wired. To place real orders, construct LiveBroker "
                "with an authenticated broker/exchange client (your own keys) and "
                "implement the order call at this adapter point. This is a "
                "deliberate manual step, not a default."
            )
        # Adapter point — intentionally not implemented. A real implementation
        # would translate `order` into the venue's order API and return a Fill
        # from the venue's response. Kept unimplemented so nothing places real
        # orders without the operator writing this consciously.
        raise NotImplementedError(
            "Venue order placement is intentionally not implemented in v1. "
            "Validate in paper first; wire your venue here when you are ready."
        )
