"""algo_trader — a safety-first algorithmic trading framework.

Layers: data → strategy → risk → execution, tied together by a backtester.
Modes: BACKTEST and PAPER are always available; LIVE is hard-gated (config.py).

Built on the production discipline studied in notes/jam-with-ai/: explicit
decisions, bounded loops, structured types, fail-safe defaults, and tests.
"""

from .config import Config, RiskLimits, CostModel, LiveGate
from .types import Bar, Signal, Order, Fill, Side, Mode

__all__ = [
    "Config", "RiskLimits", "CostModel", "LiveGate",
    "Bar", "Signal", "Order", "Fill", "Side", "Mode",
]
__version__ = "0.1.0"
