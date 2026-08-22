"""Deterministic synthetic price feed — geometric Brownian motion with a seed.

Lets the whole system run and be tested with no network and no data files, while
still producing realistic-looking OHLCV. Deterministic for a given seed so tests
are stable.
"""

from __future__ import annotations

import math
import random
from datetime import timedelta
from typing import Iterator, List, Optional

from ..types import Bar, utc
from .base import DataFeed


class SyntheticFeed(DataFeed):
    def __init__(
        self,
        symbols: Optional[List[str]] = None,
        bars: int = 500,
        start_price: float = 100.0,
        mu: float = 0.05,           # annual drift
        sigma: float = 0.60,        # annual volatility (crypto-ish)
        periods_per_year: int = 365,
        seed: int = 7,
    ) -> None:
        self.symbols = symbols or ["SYN/USD"]
        self.bars = bars
        self.start_price = start_price
        self.mu = mu
        self.sigma = sigma
        self.periods_per_year = periods_per_year
        self.seed = seed

    def __iter__(self) -> Iterator[Bar]:
        dt = 1.0 / self.periods_per_year
        start = utc(2023, 1, 1)
        rng = random.Random(self.seed)

        # Independent path per symbol; emit interleaved, sorted by timestamp.
        prices = {s: self.start_price for s in self.symbols}
        for i in range(self.bars):
            ts = start + timedelta(days=i)
            for sym in self.symbols:
                p_prev = prices[sym]
                shock = rng.gauss(0.0, 1.0)
                # GBM step for the close.
                p = p_prev * math.exp(
                    (self.mu - 0.5 * self.sigma ** 2) * dt
                    + self.sigma * math.sqrt(dt) * shock
                )
                high = max(p_prev, p) * (1 + abs(rng.gauss(0, 0.003)))
                low = min(p_prev, p) * (1 - abs(rng.gauss(0, 0.003)))
                vol = abs(rng.gauss(1000, 200))
                prices[sym] = p
                yield Bar(sym, ts, open=p_prev, high=high, low=low, close=p, volume=vol)
