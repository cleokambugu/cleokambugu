"""Configuration and the safety model.

The safety posture is encoded here, not left to discipline:

- The default mode is PAPER. BACKTEST and PAPER never touch real money.
- LIVE is unreachable unless the operator sets an explicit environment flag AND
  the run passes a validation checklist. See `LiveGate`.

This mirrors the "decide explicitly, bound the risk, fail safe" discipline from
notes/jam-with-ai/production-rag-playbook.md.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

from .types import Mode

# Environment flag that must equal exactly "1" to even consider live trading.
LIVE_ENV_FLAG = "ALGO_TRADER_ALLOW_LIVE"


@dataclass
class RiskLimits:
    """Hard risk limits enforced by the RiskManager on every order.

    Defaults are intentionally conservative — the point of v1 is not to blow up.
    """

    max_position_weight: float = 0.20      # ≤20% of equity in one symbol
    max_gross_exposure: float = 1.00       # sum of |weights| ≤ 100% (no leverage)
    risk_per_trade: float = 0.01           # size so a stop ≈ 1% of equity at risk
    max_daily_loss: float = 0.03           # flatten + halt if down 3% on the day
    max_drawdown_halt: float = 0.20        # halt if equity 20% below peak
    allow_short: bool = False              # long-only until explicitly enabled

    def validate(self) -> List[str]:
        problems: List[str] = []
        if not 0 < self.max_position_weight <= 1:
            problems.append("max_position_weight must be in (0, 1]")
        if not 0 < self.max_gross_exposure <= 3:
            problems.append("max_gross_exposure must be in (0, 3]")
        if not 0 < self.risk_per_trade <= 0.1:
            problems.append("risk_per_trade must be in (0, 0.1]")
        if not 0 < self.max_daily_loss <= 1:
            problems.append("max_daily_loss must be in (0, 1]")
        return problems


@dataclass
class CostModel:
    """Trading frictions applied by the simulated broker."""

    fee_rate: float = 0.0010     # 10 bps per trade (taker-ish default)
    slippage_rate: float = 0.0005  # 5 bps adverse slippage per fill


@dataclass
class Config:
    """Top-level run configuration."""

    mode: Mode = Mode.PAPER
    starting_cash: float = 10_000.0
    symbols: List[str] = field(default_factory=lambda: ["BTC/USDT"])
    periods_per_year: int = 365          # 365 for daily crypto; 252 for daily equities
    risk: RiskLimits = field(default_factory=RiskLimits)
    costs: CostModel = field(default_factory=CostModel)

    def validate(self) -> List[str]:
        problems = list(self.risk.validate())
        if self.starting_cash <= 0:
            problems.append("starting_cash must be positive")
        if not self.symbols:
            problems.append("at least one symbol is required")
        return problems


@dataclass
class LiveGate:
    """Decides whether live trading may proceed. Fails closed.

    Two independent conditions must both hold:
      1. The environment flag ALGO_TRADER_ALLOW_LIVE == "1".
      2. The caller passes an explicit acknowledgement and a clean config.

    Even then, this only *permits* the live broker to be constructed; the broker
    itself re-checks on every submit.
    """

    acknowledged_paper_first: bool = False
    config_problems: List[str] = field(default_factory=list)

    def env_enabled(self) -> bool:
        return os.environ.get(LIVE_ENV_FLAG) == "1"

    def reasons_blocked(self) -> List[str]:
        blocked: List[str] = []
        if not self.env_enabled():
            blocked.append(f"{LIVE_ENV_FLAG} is not set to '1'")
        if not self.acknowledged_paper_first:
            blocked.append("operator has not acknowledged paper-trading was validated first")
        blocked.extend(self.config_problems)
        return blocked

    def allowed(self) -> bool:
        return not self.reasons_blocked()
