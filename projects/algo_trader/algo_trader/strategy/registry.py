"""A tiny name→factory registry so strategies are discoverable by string.

Enables the CLI (`--strategy ma_cross`) and the optimizer to enumerate and
instantiate strategies without hard-coding imports everywhere.
"""

from __future__ import annotations

from typing import Callable, Dict

from .base import Strategy

REGISTRY: Dict[str, Callable[..., Strategy]] = {}


def register(name: str) -> Callable[[Callable[..., Strategy]], Callable[..., Strategy]]:
    def deco(factory: Callable[..., Strategy]) -> Callable[..., Strategy]:
        if name in REGISTRY:
            raise ValueError(f"strategy '{name}' already registered")
        REGISTRY[name] = factory
        return factory
    return deco


def create(name: str, **params: object) -> Strategy:
    if name not in REGISTRY:
        raise KeyError(f"unknown strategy '{name}'. Known: {sorted(REGISTRY)}")
    return REGISTRY[name](**params)
