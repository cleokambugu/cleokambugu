"""Feature engineering from a rolling window of closes. Pure Python.

Every feature at bar t uses only closes up to and including t — no future data.
Features are simple, standard, and interpretable: momentum over several horizons,
volatility, and an RSI-like oscillator.
"""

from __future__ import annotations

import math
from collections import deque
from typing import Deque, List, Optional


class FeatureBuilder:
    """Maintains a rolling close window and emits a feature vector per bar."""

    def __init__(self, lookback: int = 50) -> None:
        self.lookback = lookback
        self._closes: Deque[float] = deque(maxlen=lookback + 1)

    @property
    def n_features(self) -> int:
        return 6

    def ready(self) -> bool:
        return len(self._closes) >= self.lookback

    def update(self, close: float) -> Optional[List[float]]:
        """Add a close; return the feature vector if enough history, else None."""
        self._closes.append(close)
        if len(self._closes) < self.lookback:
            return None
        closes = list(self._closes)

        def ret(n: int) -> float:
            if len(closes) <= n or closes[-n - 1] == 0:
                return 0.0
            return closes[-1] / closes[-n - 1] - 1.0

        # Momentum over several horizons.
        r1, r5, r10 = ret(1), ret(5), ret(10)

        # Realized volatility of 1-bar returns over the window.
        rets = [closes[i] / closes[i - 1] - 1.0 for i in range(1, len(closes)) if closes[i - 1] != 0]
        mean = sum(rets) / len(rets) if rets else 0.0
        var = sum((x - mean) ** 2 for x in rets) / len(rets) if rets else 0.0
        vol = math.sqrt(var)

        # Price relative to its window mean (z-ish).
        wmean = sum(closes) / len(closes)
        rel = (closes[-1] / wmean - 1.0) if wmean else 0.0

        # RSI-style oscillator scaled to [-1, 1].
        gains = sum(max(closes[i] - closes[i - 1], 0.0) for i in range(1, len(closes)))
        losses = sum(max(closes[i - 1] - closes[i], 0.0) for i in range(1, len(closes)))
        rsi = 50.0 if (gains + losses) == 0 else 100.0 * gains / (gains + losses)
        rsi_scaled = (rsi - 50.0) / 50.0

        return [r1, r5, r10, vol, rel, rsi_scaled]
