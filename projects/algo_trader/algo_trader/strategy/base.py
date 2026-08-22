"""Strategy interface.

A strategy consumes bars one at a time (no peeking ahead) and emits Signals with
a *target weight*. It never sizes orders or touches cash — that is the risk
manager's job. Keeping strategies to "what do I want to hold?" makes them easy to
test, compose, and swap.
"""

from __future__ import annotations

import abc
from typing import List

from ..types import Bar, Signal


class Strategy(abc.ABC):
    """Base class. Subclasses maintain their own rolling state across on_bar()."""

    #: short unique name used by the registry / CLI
    name: str = "base"

    @abc.abstractmethod
    def on_bar(self, bar: Bar) -> List[Signal]:
        """Receive the latest bar; return zero or more Signals.

        Called in strict time order. Implementations must only use information up
        to and including `bar` — the backtester enforces next-bar execution, but
        strategies must not cheat by storing future data.
        """
        raise NotImplementedError

    def warmup(self) -> int:
        """Bars needed before signals are meaningful (for reporting)."""
        return 0
