"""RSI mean-reversion — buy oversold, exit as it normalizes.

Wilder's RSI over `period`. Enter long when RSI < oversold; go flat when RSI
recovers above `exit_level`. Long-only by default. Transparent and backtestable.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from ..types import Bar, Side, Signal
from .base import Strategy
from .registry import register


class _RsiState:
    __slots__ = ("prev_close", "avg_gain", "avg_loss", "count", "in_pos")

    def __init__(self) -> None:
        self.prev_close: float = float("nan")
        self.avg_gain: float = 0.0
        self.avg_loss: float = 0.0
        self.count: int = 0
        self.in_pos: bool = False


@register("rsi_meanrev")
class RsiMeanReversion(Strategy):
    name = "rsi_meanrev"

    def __init__(self, period: int = 14, oversold: float = 30.0,
                 exit_level: float = 55.0, target_weight: float = 0.2) -> None:
        self.period = period
        self.oversold = oversold
        self.exit_level = exit_level
        self.target_weight = target_weight
        self._st: Dict[str, _RsiState] = defaultdict(_RsiState)

    def warmup(self) -> int:
        return self.period + 1

    def _rsi(self, st: _RsiState, close: float) -> float:
        if st.count == 0:
            st.prev_close = close
            st.count = 1
            return float("nan")
        change = close - st.prev_close
        gain = max(change, 0.0)
        loss = max(-change, 0.0)
        if st.count <= self.period:
            # Accumulate the initial simple averages.
            st.avg_gain += gain
            st.avg_loss += loss
            st.count += 1
            st.prev_close = close
            if st.count == self.period + 1:
                st.avg_gain /= self.period
                st.avg_loss /= self.period
            else:
                return float("nan")
        else:
            # Wilder smoothing.
            st.avg_gain = (st.avg_gain * (self.period - 1) + gain) / self.period
            st.avg_loss = (st.avg_loss * (self.period - 1) + loss) / self.period
            st.prev_close = close

        if st.avg_loss == 0:
            return 100.0
        rs = st.avg_gain / st.avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    def on_bar(self, bar: Bar) -> List[Signal]:
        st = self._st[bar.symbol]
        rsi = self._rsi(st, bar.close)
        if rsi != rsi:  # NaN during warmup
            return []
        if not st.in_pos and rsi < self.oversold:
            st.in_pos = True
            return [Signal(bar.symbol, Side.BUY, bar.ts, self.target_weight,
                           f"RSI {rsi:.1f} < {self.oversold} oversold")]
        if st.in_pos and rsi > self.exit_level:
            st.in_pos = False
            return [Signal(bar.symbol, Side.FLAT, bar.ts, 0.0,
                           f"RSI {rsi:.1f} > {self.exit_level} exit")]
        return []
