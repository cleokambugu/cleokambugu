"""Performance metrics from an equity curve and closed trades.

Pure Python. These are the numbers that tell you whether a strategy is worth
anything — and, just as important, how badly it can hurt (drawdown).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Sequence

from ..types import TradeRecord


@dataclass
class Metrics:
    start_equity: float
    end_equity: float
    total_return: float
    cagr: float
    sharpe: float
    max_drawdown: float
    volatility_annual: float
    num_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def _returns(equity: Sequence[float]) -> List[float]:
    out = []
    for i in range(1, len(equity)):
        prev = equity[i - 1]
        if prev > 0:
            out.append(equity[i] / prev - 1.0)
        else:
            out.append(0.0)
    return out


def max_drawdown(equity: Sequence[float]) -> float:
    peak = -math.inf
    mdd = 0.0
    for v in equity:
        peak = max(peak, v)
        if peak > 0:
            mdd = min(mdd, v / peak - 1.0)
    return mdd  # negative number, e.g. -0.23


def compute_metrics(
    equity: Sequence[float],
    trades: List[TradeRecord],
    periods_per_year: int,
) -> Metrics:
    if len(equity) < 2:
        raise ValueError("need at least two equity points")

    start, end = equity[0], equity[-1]
    total_return = end / start - 1.0 if start > 0 else 0.0

    rets = _returns(equity)
    n = len(rets)
    mean = sum(rets) / n if n else 0.0
    var = sum((r - mean) ** 2 for r in rets) / (n - 1) if n > 1 else 0.0
    std = math.sqrt(var)
    vol_annual = std * math.sqrt(periods_per_year)
    sharpe = (mean / std * math.sqrt(periods_per_year)) if std > 0 else 0.0

    years = n / periods_per_year if periods_per_year else 0.0
    cagr = (end / start) ** (1 / years) - 1.0 if years > 0 and start > 0 else 0.0

    wins = [t.pnl for t in trades if t.pnl > 0]
    losses = [t.pnl for t in trades if t.pnl < 0]
    num = len(trades)
    win_rate = len(wins) / num if num else 0.0
    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = sum(losses) / len(losses) if losses else 0.0
    gross_win = sum(wins)
    gross_loss = -sum(losses)
    profit_factor = (gross_win / gross_loss) if gross_loss > 0 else (math.inf if gross_win > 0 else 0.0)

    return Metrics(
        start_equity=start,
        end_equity=end,
        total_return=total_return,
        cagr=cagr,
        sharpe=sharpe,
        max_drawdown=max_drawdown(equity),
        volatility_annual=vol_annual,
        num_trades=num,
        win_rate=win_rate,
        avg_win=avg_win,
        avg_loss=avg_loss,
        profit_factor=profit_factor,
    )
