from .base import Strategy
from .registry import REGISTRY, register, create
from . import ma_cross, rsi_mean_reversion  # noqa: F401 (populate registry)
# Import strategies defined in sibling packages so they self-register too.
from ..signals import sentiment as _sentiment  # noqa: F401
from ..ml import strategy as _ml_strategy  # noqa: F401

__all__ = ["Strategy", "REGISTRY", "register", "create"]
