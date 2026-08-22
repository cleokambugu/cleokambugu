"""Broker interface. All order routing goes through a Broker implementation."""

from __future__ import annotations

import abc
from typing import Optional

from ..types import Bar, Fill, Order


class Broker(abc.ABC):
    """Abstract order router. Implementations: SimulatedBroker, LiveBroker."""

    @abc.abstractmethod
    def submit(self, order: Order, ref_bar: Bar) -> Optional[Fill]:
        """Submit an order. `ref_bar` is the bar whose price context applies.

        Returns a Fill if executed, or None if rejected/unfilled.
        """
        raise NotImplementedError
