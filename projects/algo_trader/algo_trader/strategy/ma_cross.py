"""Moving-average crossover — a transparent trend-following baseline.

Long when the fast SMA is above the slow SMA; flat (or short, if enabled)
otherwise. Per-symbol rolling windows; no look-ahead.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Deque, Dict, List

from ..types import Bar, Side, Signal
from .base import Strategy
from .registry import register


@register("ma_cross")
class MACrossStrategy(Strategy):
    name = "ma_cross"

    def __init__(self, fast: int = 20, slow: int = 50, target_weight: float = 0.2,
                 allow_short: bool = False) -> None:
        if fast >= slow:
            raise ValueError("fast window must be < slow window")
        self.fast = fast
        self.slow = slow
        self.target_weight = target_weight
        self.allow_short = allow_short
        self._win: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=slow))

    def warmup(self) -> int:
        return self.slow

    @staticmethod
    def _sma(values: Deque[float], n: int) -> float:
        if len(values) < n:
            return float("nan")
        # mean of the last n
        return sum(list(values)[-n:]) / n

    def on_bar(self, bar: Bar) -> List[Signal]:
        w = self._win[bar.symbol]
        w.append(bar.close)
        if len(w) < self.slow:
            return []

        fast_ma = self._sma(w, self.fast)
        slow_ma = self._sma(w, self.slow)
        if fast_ma > slow_ma:
            return [Signal(bar.symbol, Side.BUY, bar.ts, self.target_weight,
                           f"fast{self.fast}>{self.slow}slow")]
        if self.allow_short:
            return [Signal(bar.symbol, Side.SELL, bar.ts, -self.target_weight,
                           f"fast{self.fast}<{self.slow}slow")]
        return [Signal(bar.symbol, Side.FLAT, bar.ts, 0.0, "trend down → flat")]
