"""Live market-data adapters for crypto (ccxt) and US equities (Alpaca).

These are OPTIONAL and require extra packages plus your own API keys. They are
kept thin and import their dependencies lazily so the core stays zero-dependency
and always testable offline. Nothing here bypasses exchange terms or rate limits;
respect each venue's documented limits (ccxt exposes `enableRateLimit`).

They fetch *historical* bars for backtesting/paper. Neither places orders — order
routing is the broker layer's job, and live order routing is hard-gated.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterator, List

from ..types import Bar
from .base import DataFeed


class CcxtHistoricalFeed(DataFeed):
    """Crypto OHLCV via ccxt. `pip install ccxt`.

    Example:
        feed = CcxtHistoricalFeed("binance", "BTC/USDT", timeframe="1d", limit=500)
    """

    def __init__(self, exchange_id: str, symbol: str, timeframe: str = "1d",
                 limit: int = 500, since: int | None = None) -> None:
        self.exchange_id = exchange_id
        self.symbol = symbol
        self.timeframe = timeframe
        self.limit = limit
        self.since = since

    def __iter__(self) -> Iterator[Bar]:
        try:
            import ccxt  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise SystemExit("CcxtHistoricalFeed needs ccxt: pip install ccxt") from exc
        exchange = getattr(ccxt, self.exchange_id)({"enableRateLimit": True})
        ohlcv = exchange.fetch_ohlcv(self.symbol, timeframe=self.timeframe,
                                     since=self.since, limit=self.limit)
        for ts_ms, o, h, l, c, v in ohlcv:
            yield Bar(self.symbol, datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc),
                      float(o), float(h), float(l), float(c), float(v or 0.0))


class AlpacaHistoricalFeed(DataFeed):
    """US-equity bars via Alpaca. `pip install alpaca-py`; set API keys in env.

    Example:
        feed = AlpacaHistoricalFeed("AAPL", timeframe="1Day", limit=500)
    Uses your ALPACA_API_KEY / ALPACA_SECRET_KEY. Paper data is free.
    """

    def __init__(self, symbol: str, timeframe: str = "1Day", limit: int = 500) -> None:
        self.symbol = symbol
        self.timeframe = timeframe
        self.limit = limit

    def __iter__(self) -> Iterator[Bar]:
        try:
            import os
            from alpaca.data.historical import StockHistoricalDataClient  # type: ignore
            from alpaca.data.requests import StockBarsRequest  # type: ignore
            from alpaca.data.timeframe import TimeFrame  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise SystemExit("AlpacaHistoricalFeed needs alpaca-py: pip install alpaca-py") from exc

        key = os.environ.get("ALPACA_API_KEY")
        secret = os.environ.get("ALPACA_SECRET_KEY")
        if not key or not secret:
            raise SystemExit("set ALPACA_API_KEY and ALPACA_SECRET_KEY in the environment")

        client = StockHistoricalDataClient(key, secret)
        tf = TimeFrame.Day if self.timeframe == "1Day" else TimeFrame.Hour
        req = StockBarsRequest(symbol_or_symbols=self.symbol, timeframe=tf, limit=self.limit)
        bars = client.get_stock_bars(req)
        for b in bars[self.symbol]:
            ts = b.timestamp if b.timestamp.tzinfo else b.timestamp.replace(tzinfo=timezone.utc)
            yield Bar(self.symbol, ts, float(b.open), float(b.high), float(b.low),
                      float(b.close), float(b.volume or 0.0))
