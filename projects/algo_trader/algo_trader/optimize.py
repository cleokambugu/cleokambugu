"""Walk-forward parameter search — the honest form of "adaptive strategies".

The system "adapts" by searching a parameter grid on an in-sample window and
keeping the choice that then performs on a *separate* out-of-sample window. This
is deliberately not a black box that invents strategies unsupervised: unbounded
self-modifying trading logic is how you overfit noise and lose money. Walk-forward
selection is the defensible version — it adapts while guarding against fitting the
past.

Returns the parameters that generalized best (by out-of-sample Sharpe), plus the
full record so you can see how stable the choice is.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Callable, Dict, List, Sequence, Tuple

from .backtest.engine import Backtester
from .config import Config
from .data.base import DataFeed
from .execution.simulated import SimulatedBroker
from .strategy.registry import create
from .types import Bar


@dataclass
class WalkForwardResult:
    best_params: Dict[str, object]
    in_sample_sharpe: float
    out_sample_sharpe: float
    all_results: List[Tuple[Dict[str, object], float, float]]  # params, is_sharpe, oos_sharpe


class _ListFeed(DataFeed):
    def __init__(self, bars: Sequence[Bar]) -> None:
        self._bars = list(bars)

    def __iter__(self):
        return iter(self._bars)


def _grid(param_grid: Dict[str, Sequence]) -> List[Dict[str, object]]:
    keys = list(param_grid)
    return [dict(zip(keys, combo)) for combo in itertools.product(*param_grid.values())]


def _sharpe(config: Config, strategy_name: str, params: Dict[str, object],
            bars: Sequence[Bar]) -> float:
    bt = Backtester(config, create(strategy_name, **params), SimulatedBroker(config.costs))
    return bt.run(_ListFeed(bars)).metrics.sharpe


def walk_forward(
    config: Config,
    strategy_name: str,
    param_grid: Dict[str, Sequence],
    feed: DataFeed,
    split: float = 0.6,
) -> WalkForwardResult:
    """Grid-search on the first `split` of the data, validate on the rest."""
    bars = list(feed)
    if len(bars) < 20:
        raise ValueError("not enough bars for a walk-forward split")
    cut = int(len(bars) * split)
    in_sample, out_sample = bars[:cut], bars[cut:]

    records: List[Tuple[Dict[str, object], float, float]] = []
    for params in _grid(param_grid):
        try:
            is_sh = _sharpe(config, strategy_name, params, in_sample)
            oos_sh = _sharpe(config, strategy_name, params, out_sample)
        except ValueError:
            continue  # invalid combo (e.g. fast>=slow) — skip
        records.append((params, is_sh, oos_sh))

    if not records:
        raise ValueError("no valid parameter combinations")

    # Choose by in-sample, then report how it did out-of-sample (no peeking to pick).
    best = max(records, key=lambda r: r[1])
    return WalkForwardResult(
        best_params=best[0],
        in_sample_sharpe=best[1],
        out_sample_sharpe=best[2],
        all_results=sorted(records, key=lambda r: r[2], reverse=True),
    )
