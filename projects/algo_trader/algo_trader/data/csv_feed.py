"""CSV feed: read OHLCV bars from one or more CSV files (no dependencies).

Expected columns (header, case-insensitive): timestamp, open, high, low, close,
volume. `timestamp` may be ISO-8601 or a UNIX epoch (seconds). One file per
symbol; bars from all files are merged and yielded in timestamp order.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from typing import Dict, Iterator, List

from ..types import Bar
from .base import DataFeed


def _parse_ts(raw: str) -> datetime:
    raw = raw.strip()
    if raw.isdigit():
        return datetime.fromtimestamp(int(raw), tz=timezone.utc)
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class CsvFeed(DataFeed):
    def __init__(self, files_by_symbol: Dict[str, str]) -> None:
        """:param files_by_symbol: {symbol: path_to_csv}."""
        self.files_by_symbol = files_by_symbol

    def _read(self, symbol: str, path: str) -> List[Bar]:
        out: List[Bar] = []
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            norm = {name.lower(): name for name in (reader.fieldnames or [])}
            required = ["timestamp", "open", "high", "low", "close"]
            missing = [c for c in required if c not in norm]
            if missing:
                raise ValueError(f"{path}: missing columns {missing}")
            for row in reader:
                out.append(
                    Bar(
                        symbol=symbol,
                        ts=_parse_ts(row[norm["timestamp"]]),
                        open=float(row[norm["open"]]),
                        high=float(row[norm["high"]]),
                        low=float(row[norm["low"]]),
                        close=float(row[norm["close"]]),
                        volume=float(row[norm["volume"]]) if "volume" in norm else 0.0,
                    )
                )
        return out

    def __iter__(self) -> Iterator[Bar]:
        all_bars: List[Bar] = []
        for symbol, path in self.files_by_symbol.items():
            all_bars.extend(self._read(symbol, path))
        all_bars.sort(key=lambda b: b.ts)
        yield from all_bars
