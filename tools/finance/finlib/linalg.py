"""Minimal dense linear algebra — pure stdlib, no numpy.

Only what the portfolio module needs: matrix product, transpose, and solving
``A x = b`` / inverting a small covariance matrix by Gauss-Jordan elimination
with partial pivoting.

Covariance matrices in mean-variance optimisation are symmetric positive
definite and small (tens of assets, not thousands), so a plain O(n^3)
elimination is the right tool: exact enough, obvious to audit, no dependency.
"""

from __future__ import annotations

Matrix = list[list[float]]
Vector = list[float]


class SingularMatrixError(ValueError):
    """Raised when a matrix cannot be inverted (e.g. redundant assets)."""


def shape(a: Matrix) -> tuple[int, int]:
    return len(a), len(a[0]) if a else 0


def transpose(a: Matrix) -> Matrix:
    return [list(row) for row in zip(*a)]


def matmul(a: Matrix, b: Matrix) -> Matrix:
    """Standard matrix product."""
    n, k = shape(a)
    k2, m = shape(b)
    if k != k2:
        raise ValueError(f"inner dimensions disagree: {k} vs {k2}")
    bt = transpose(b)
    return [[sum(x * y for x, y in zip(row, col)) for col in bt] for row in a]


def matvec(a: Matrix, v: Vector) -> Vector:
    """Matrix times column vector."""
    if shape(a)[1] != len(v):
        raise ValueError("dimension mismatch")
    return [sum(x * y for x, y in zip(row, v)) for row in a]


def dot(u: Vector, v: Vector) -> float:
    if len(u) != len(v):
        raise ValueError("dimension mismatch")
    return sum(x * y for x, y in zip(u, v))


def identity(n: int) -> Matrix:
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def inverse(a: Matrix) -> Matrix:
    """Invert a square matrix by Gauss-Jordan with partial pivoting.

    Raises SingularMatrixError when the matrix is singular to working
    precision — for a covariance matrix that means two assets are perfectly
    collinear, which is a modelling problem, not a numerical one.
    """
    n, m = shape(a)
    if n != m:
        raise ValueError("matrix must be square")
    # Work on [A | I] and reduce the left block to the identity.
    aug = [list(a[i]) + identity(n)[i] for i in range(n)]

    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-14:
            raise SingularMatrixError(
                f"matrix is singular at column {col}; "
                "check for perfectly correlated or duplicated assets"
            )
        aug[col], aug[pivot] = aug[pivot], aug[col]

        p = aug[col][col]
        aug[col] = [x / p for x in aug[col]]

        for r in range(n):
            if r == col:
                continue
            factor = aug[r][col]
            if factor:
                aug[r] = [x - factor * y for x, y in zip(aug[r], aug[col])]

    return [row[n:] for row in aug]


def solve(a: Matrix, b: Vector) -> Vector:
    """Solve ``A x = b``."""
    return matvec(inverse(a), b)


def is_symmetric(a: Matrix, tol: float = 1e-9) -> bool:
    n, m = shape(a)
    if n != m:
        return False
    return all(abs(a[i][j] - a[j][i]) <= tol for i in range(n) for j in range(n))


def cov_from_returns(returns: list[Vector], sample: bool = True) -> Matrix:
    """Covariance matrix from per-asset return series.

    ``returns[i]`` is the return series of asset i; all series must be the same
    length. ``sample=True`` uses the n-1 denominator.
    """
    n_assets = len(returns)
    if n_assets == 0:
        raise ValueError("need at least one asset")
    t = len(returns[0])
    if any(len(r) != t for r in returns):
        raise ValueError("all return series must have the same length")
    denom = (t - 1) if sample else t
    if denom <= 0:
        raise ValueError("need at least two observations for a sample covariance")

    means = [sum(r) / t for r in returns]
    out = [[0.0] * n_assets for _ in range(n_assets)]
    for i in range(n_assets):
        for j in range(i, n_assets):
            c = sum(
                (returns[i][k] - means[i]) * (returns[j][k] - means[j])
                for k in range(t)
            ) / denom
            out[i][j] = out[j][i] = c
    return out


def corr_from_cov(cov: Matrix) -> Matrix:
    """Correlation matrix implied by a covariance matrix."""
    n = len(cov)
    sd = [cov[i][i] ** 0.5 for i in range(n)]
    return [
        [cov[i][j] / (sd[i] * sd[j]) if sd[i] and sd[j] else 0.0 for j in range(n)]
        for i in range(n)
    ]
