"""A tiny, dependency-free classifier so the ML path runs and tests offline.

LogisticRegressionGD is standardized logistic regression trained by batch gradient
descent — enough to learn a real signal on engineered features, with no numpy or
scikit-learn. For production you can swap in `SklearnPredictor` (lazy-imported).
"""

from __future__ import annotations

import abc
import math
from typing import List, Sequence


class Predictor(abc.ABC):
    @abc.abstractmethod
    def fit(self, X: Sequence[Sequence[float]], y: Sequence[int]) -> "Predictor":
        raise NotImplementedError

    @abc.abstractmethod
    def predict_proba_up(self, x: Sequence[float]) -> float:
        """Probability in [0, 1] that the forward return is positive."""
        raise NotImplementedError


def _sigmoid(z: float) -> float:
    if z < -35:
        return 0.0
    if z > 35:
        return 1.0
    return 1.0 / (1.0 + math.exp(-z))


class LogisticRegressionGD(Predictor):
    def __init__(self, lr: float = 0.1, epochs: int = 300, l2: float = 1e-4) -> None:
        self.lr = lr
        self.epochs = epochs
        self.l2 = l2
        self.w: List[float] = []
        self.b: float = 0.0
        self._mu: List[float] = []
        self._sd: List[float] = []
        self._fitted = False

    def _standardize_fit(self, X: Sequence[Sequence[float]]) -> List[List[float]]:
        n, d = len(X), len(X[0])
        self._mu = [0.0] * d
        self._sd = [1.0] * d
        for j in range(d):
            col = [X[i][j] for i in range(n)]
            mu = sum(col) / n
            var = sum((v - mu) ** 2 for v in col) / n
            self._mu[j] = mu
            self._sd[j] = math.sqrt(var) or 1.0
        return [self._standardize(row) for row in X]

    def _standardize(self, x: Sequence[float]) -> List[float]:
        return [(x[j] - self._mu[j]) / self._sd[j] for j in range(len(x))]

    def fit(self, X: Sequence[Sequence[float]], y: Sequence[int]) -> "LogisticRegressionGD":
        if not X:
            raise ValueError("empty training set")
        Xs = self._standardize_fit(X)
        n, d = len(Xs), len(Xs[0])
        self.w = [0.0] * d
        self.b = 0.0
        for _ in range(self.epochs):
            gw = [0.0] * d
            gb = 0.0
            for i in range(n):
                z = self.b + sum(self.w[j] * Xs[i][j] for j in range(d))
                err = _sigmoid(z) - y[i]
                for j in range(d):
                    gw[j] += err * Xs[i][j]
                gb += err
            for j in range(d):
                self.w[j] -= self.lr * (gw[j] / n + self.l2 * self.w[j])
            self.b -= self.lr * (gb / n)
        self._fitted = True
        return self

    def predict_proba_up(self, x: Sequence[float]) -> float:
        if not self._fitted:
            return 0.5
        xs = self._standardize(x)
        z = self.b + sum(self.w[j] * xs[j] for j in range(len(xs)))
        return _sigmoid(z)


class SklearnPredictor(Predictor):  # pragma: no cover - optional dependency
    """Upgrade path: wrap any scikit-learn classifier with predict_proba."""

    def __init__(self, estimator: object | None = None) -> None:
        if estimator is None:
            try:
                from sklearn.ensemble import GradientBoostingClassifier
            except ImportError as exc:
                raise SystemExit("SklearnPredictor needs scikit-learn: pip install scikit-learn") from exc
            estimator = GradientBoostingClassifier()
        self.estimator = estimator

    def fit(self, X, y):
        self.estimator.fit(list(X), list(y))
        return self

    def predict_proba_up(self, x):
        proba = self.estimator.predict_proba([list(x)])[0]
        classes = list(self.estimator.classes_)
        return float(proba[classes.index(1)]) if 1 in classes else 0.5
