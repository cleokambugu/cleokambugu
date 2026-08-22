"""Data feed interface: a source of Bars in non-decreasing timestamp order."""

from __future__ import annotations

import abc
from typing import Iterator

from ..types import Bar


class DataFeed(abc.ABC):
    """Yields Bars ordered by time. Multi-symbol feeds interleave by timestamp."""

    @abc.abstractmethod
    def __iter__(self) -> Iterator[Bar]:
        raise NotImplementedError
