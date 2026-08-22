from .base import Strategy
from .registry import REGISTRY, register, create
from . import ma_cross, rsi_mean_reversion  # noqa: F401 (populate registry)

__all__ = ["Strategy", "REGISTRY", "register", "create"]
