"""ML-scored strategy with online walk-forward training.

The critical property is no look-ahead in the *labels*. A bar's label is the sign
of its forward return over `horizon` bars — which is only knowable `horizon` bars
later. So at bar t we train only on bars i where i + horizon <= t (their outcome
has actually happened), and predict on bar t (whose label is still unknown). The
model is periodically retrained on this growing, strictly-past dataset.

Per-symbol models, so symbols don't leak into each other. Long-only via the risk
manager; sizing scales with the model's confidence.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, List, Optional

from ..types import Bar, Side, Signal
from ..strategy.base import Strategy
from ..strategy.registry import register
from .features import FeatureBuilder
from .model import LogisticRegressionGD, Predictor


class _SymState:
    def __init__(self, lookback: int) -> None:
        self.builder = FeatureBuilder(lookback)
        self.closes: List[float] = []
        self.feats: List[Optional[List[float]]] = []
        self.X_train: List[List[float]] = []
        self.y_train: List[int] = []
        self.model: Optional[Predictor] = None
        self.last_train_at: int = -10 ** 9
        self.in_pos: bool = False


@register("ml_scored")
class MLStrategy(Strategy):
    name = "ml_scored"

    def __init__(
        self,
        lookback: int = 30,
        horizon: int = 5,
        min_train: int = 60,
        retrain_every: int = 25,
        enter_margin: float = 0.05,
        max_weight: float = 0.2,
        model_factory: Optional[Callable[[], Predictor]] = None,
    ) -> None:
        self.lookback = lookback
        self.horizon = horizon
        self.min_train = min_train
        self.retrain_every = retrain_every
        self.enter_margin = enter_margin
        self.max_weight = max_weight
        self.model_factory = model_factory or (lambda: LogisticRegressionGD())
        self._st: Dict[str, _SymState] = {}

    def warmup(self) -> int:
        return self.lookback + self.horizon + self.min_train

    def on_bar(self, bar: Bar) -> List[Signal]:
        st = self._st.get(bar.symbol)
        if st is None:
            st = self._st[bar.symbol] = _SymState(self.lookback)

        st.closes.append(bar.close)
        st.feats.append(st.builder.update(bar.close))
        t = len(st.closes) - 1

        # A label for bar i = t - horizon just became known (close[t] observed).
        i = t - self.horizon
        if i >= 0 and st.feats[i] is not None:
            label = 1 if st.closes[i + self.horizon] > st.closes[i] else 0
            st.X_train.append(st.feats[i])  # type: ignore[arg-type]
            st.y_train.append(label)

        # Retrain on the strictly-past, realized dataset (needs both classes).
        if (len(st.X_train) >= self.min_train
                and (st.model is None or t - st.last_train_at >= self.retrain_every)
                and len(set(st.y_train)) >= 2):
            st.model = self.model_factory().fit(st.X_train, st.y_train)
            st.last_train_at = t

        feat_now = st.feats[t]
        if st.model is None or feat_now is None:
            return []

        prob_up = st.model.predict_proba_up(feat_now)
        if not st.in_pos and prob_up > 0.5 + self.enter_margin:
            st.in_pos = True
            weight = min(self.max_weight, self.max_weight * (prob_up - 0.5) * 2.0)
            return [Signal(bar.symbol, Side.BUY, bar.ts, weight, f"P(up)={prob_up:.2f}")]
        if st.in_pos and prob_up < 0.5:
            st.in_pos = False
            return [Signal(bar.symbol, Side.FLAT, bar.ts, 0.0, f"P(up)={prob_up:.2f} < 0.5")]
        return []
