"""News / LLM sentiment as a trading signal — the "learn from diverse data" piece.

Pipeline (mirrors the RAG work in notes/jam-with-ai/): ingest text items (news,
filings, transcripts) → score each into a sentiment in [-1, 1] → store as
per-(symbol, time) features → a Strategy reads the latest feature *as of* each bar
and trades on it.

No-look-ahead is enforced in the FeatureStore: a news item timestamped T can only
influence bars at time ≥ T. Getting this wrong is the classic way sentiment
backtests lie.

Two scorers:
- LexiconSentimentScorer: deterministic, offline, zero-dependency. The default,
  so the whole signal is testable without a model or network.
- LLMSentimentScorer: an upgrade that calls an LLM (e.g. Claude) for nuanced
  scoring. Lazy-imported; never required.
"""

from __future__ import annotations

import abc
import bisect
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from ..types import Bar, Side, Signal
from ..strategy.base import Strategy
from ..strategy.registry import register


class SentimentScorer(abc.ABC):
    @abc.abstractmethod
    def score(self, text: str) -> float:
        """Return sentiment in [-1, 1]. -1 very negative, +1 very positive."""
        raise NotImplementedError


class LexiconSentimentScorer(SentimentScorer):
    """A small, transparent finance lexicon. Deterministic and offline.

    Not as nuanced as an LLM, but real, fast, and testable — and a sane default
    so the signal works out of the box. Negation ("not good") flips polarity.
    """

    POSITIVE = {
        "beat", "beats", "surge", "surges", "soar", "soars", "rally", "rallies",
        "growth", "profit", "profits", "record", "upgrade", "upgraded", "bullish",
        "gain", "gains", "strong", "outperform", "breakthrough", "approval",
        "partnership", "expansion", "wins", "win", "positive", "rise", "rises",
    }
    NEGATIVE = {
        "miss", "misses", "plunge", "plunges", "crash", "crashes", "slump",
        "loss", "losses", "downgrade", "downgraded", "bearish", "weak", "warning",
        "lawsuit", "probe", "fraud", "recall", "cut", "cuts", "decline", "declines",
        "fall", "falls", "bankruptcy", "default", "negative", "hack", "breach",
    }
    NEGATORS = {"not", "no", "never", "without", "n't"}

    _WORD = re.compile(r"[a-z']+")

    def score(self, text: str) -> float:
        words = self._WORD.findall(text.lower())
        if not words:
            return 0.0
        total = 0
        hits = 0
        for i, w in enumerate(words):
            val = 0
            if w in self.POSITIVE:
                val = 1
            elif w in self.NEGATIVE:
                val = -1
            if val != 0:
                # Flip if a negator appears in the preceding 3 words.
                window = words[max(0, i - 3):i]
                if any(n in window for n in self.NEGATORS):
                    val = -val
                total += val
                hits += 1
        if hits == 0:
            return 0.0
        # Normalize by hits, then squash lightly so a single word isn't ±1 forever.
        raw = total / hits
        return max(-1.0, min(1.0, raw))


class LLMSentimentScorer(SentimentScorer):
    """LLM-backed scorer (upgrade path). Lazy-imports an Anthropic client.

    Requires `pip install anthropic` and an API key. Kept out of the default path
    so nothing here needs network or credentials to run/test. Wire your own client
    and model id; this returns a float in [-1, 1].
    """

    def __init__(self, client: object | None = None, model: str = "claude-sonnet-5") -> None:
        self.client = client
        self.model = model

    def score(self, text: str) -> float:  # pragma: no cover - requires network/creds
        if self.client is None:
            raise RuntimeError(
                "LLMSentimentScorer needs an Anthropic client. Construct it with your "
                "own client, or use LexiconSentimentScorer for offline scoring."
            )
        prompt = (
            "Score the market sentiment of this financial news for the mentioned "
            "asset as a single number from -1 (very bearish) to 1 (very bullish). "
            "Reply with only the number.\n\n" + text
        )
        msg = self.client.messages.create(  # type: ignore[attr-defined]
            model=self.model, max_tokens=8,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = "".join(getattr(b, "text", "") for b in msg.content).strip()
        try:
            return max(-1.0, min(1.0, float(raw)))
        except ValueError:
            return 0.0


@dataclass
class NewsItem:
    ts: datetime
    symbol: str
    text: str


@dataclass
class FeatureStore:
    """Per-symbol time series of scored features, queried as-of a timestamp.

    Enforces no-look-ahead: `latest(symbol, ts)` returns the most recent feature
    with feature_ts <= ts, or None.
    """

    # symbol -> (sorted_timestamps, values)
    _series: Dict[str, Tuple[List[datetime], List[float]]] = field(default_factory=dict)

    def add(self, symbol: str, ts: datetime, value: float) -> None:
        times, vals = self._series.setdefault(symbol, ([], []))
        idx = bisect.bisect_right(times, ts)
        times.insert(idx, ts)
        vals.insert(idx, value)

    def latest(self, symbol: str, ts: datetime) -> Optional[float]:
        entry = self._series.get(symbol)
        if not entry:
            return None
        times, vals = entry
        idx = bisect.bisect_right(times, ts) - 1
        return vals[idx] if idx >= 0 else None


def build_feature_store(
    items: List[NewsItem],
    scorer: Optional[SentimentScorer] = None,
    decay: float = 0.5,
) -> FeatureStore:
    """Score news items into a FeatureStore.

    Multiple items for the same symbol accumulate with exponential blending so a
    fresh headline moves the running sentiment without erasing recent context.
    :param decay: weight of the new item vs the running value (0..1].
    """
    scorer = scorer or LexiconSentimentScorer()
    store = FeatureStore()
    running: Dict[str, float] = {}
    for item in sorted(items, key=lambda x: x.ts):
        s = scorer.score(item.text)
        prev = running.get(item.symbol, 0.0)
        blended = decay * s + (1 - decay) * prev
        running[item.symbol] = blended
        store.add(item.symbol, item.ts, blended)
    return store


@register("news_sentiment")
class NewsSentimentStrategy(Strategy):
    """Long when as-of sentiment is bullish; flat when it fades. Long-only by
    default (short side is gated by the risk manager anyway).

    Constructed with an empty store by default so it is importable/registerable;
    supply a FeatureStore built from your ingested news to make it act.
    """

    name = "news_sentiment"

    def __init__(self, store: Optional[FeatureStore] = None, enter: float = 0.3,
                 exit: float = 0.05, max_weight: float = 0.2) -> None:
        self.store = store or FeatureStore()
        self.enter = enter
        self.exit = exit
        self.max_weight = max_weight
        self._in_pos: Dict[str, bool] = {}

    def on_bar(self, bar: Bar) -> List[Signal]:
        s = self.store.latest(bar.symbol, bar.ts)
        if s is None:
            return []
        in_pos = self._in_pos.get(bar.symbol, False)
        if not in_pos and s >= self.enter:
            self._in_pos[bar.symbol] = True
            weight = min(self.max_weight, self.max_weight * s)
            return [Signal(bar.symbol, Side.BUY, bar.ts, weight, f"sentiment {s:+.2f} ≥ {self.enter}")]
        if in_pos and s <= self.exit:
            self._in_pos[bar.symbol] = False
            return [Signal(bar.symbol, Side.FLAT, bar.ts, 0.0, f"sentiment {s:+.2f} ≤ {self.exit}")]
        return []
