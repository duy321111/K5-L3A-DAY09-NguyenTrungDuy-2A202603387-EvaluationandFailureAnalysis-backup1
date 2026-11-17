"""Offline classifier calibration and paired, item-level uncertainty estimates."""
from __future__ import annotations
from collections.abc import Sequence
from math import comb, isfinite
from numbers import Integral
import numpy as np
from scipy.stats import bootstrap

POS = "FAIL"


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    if len(human) != len(judge) or not len(human):
        raise ValueError("labels must have equal, nonzero lengths")
    out = dict(tp=0, fp=0, fn=0, tn=0)
    for h, j in zip(human, judge):
        if h not in {"PASS", "FAIL"} or j not in {"PASS", "FAIL"}:
            raise ValueError("labels must be PASS or FAIL")
        out[("tp" if h == POS else "fp") if j == POS else ("fn" if h == POS else "tn")] += 1
    return out


def precision_recall(human, judge):
    c = confusion(human, judge)
    return (c['tp'] / (c['tp'] + c['fp']) if c['tp'] + c['fp'] else 0.0,
            c['tp'] / (c['tp'] + c['fn']) if c['tp'] + c['fn'] else 0.0)


def cohen_kappa(human, judge):
    c = confusion(human, judge)
    n = sum(c.values())
    po = (c['tp'] + c['tn']) / n
    pe = ((c['tp'] + c['fn']) * (c['tp'] + c['fp']) +
          (c['tn'] + c['fp']) * (c['tn'] + c['fn'])) / n**2
    if pe == 1:
        raise ValueError("kappa undefined: expected agreement is one")
    return (po - pe) / (1 - pe)


def rogan_gladen(observed_rate, sensitivity, specificity):
    if any(not isfinite(x) or not 0 <= x <= 1 for x in (observed_rate, sensitivity, specificity)):
        raise ValueError("rates must be finite and in [0,1]")
    denominator = sensitivity + specificity - 1
    if denominator <= 0:
        raise ValueError("judge has no usable discrimination for rate correction")
    return max(0.0, min(1.0, (observed_rate + specificity - 1) / denominator))


def paired_bootstrap(a, b, *, n_resamples=1000, rng=2027, confidence=0.95):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.ndim != 1 or b.ndim != 1 or a.size != b.size or not a.size:
        raise ValueError("paired vectors must be nonempty, 1-D and equally sized")
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ValueError("paired vectors must be finite")
    if n_resamples < 1 or not 0 < confidence < 1:
        raise ValueError("invalid bootstrap configuration")
    delta = float(np.mean(a - b))
    if np.array_equal(a, b):
        return 0.0, 0.0, 0.0
    if a.size == 1:
        return delta, delta, delta
    result = bootstrap((a, b), lambda x, y, axis: np.mean(x - y, axis=axis),
                       paired=True, vectorized=True, method="percentile",
                       n_resamples=n_resamples, confidence_level=confidence,
                       rng=np.random.default_rng(rng))
    return delta, float(result.confidence_interval.low), float(result.confidence_interval.high)


def _validate_k(n, c, k):
    if any(isinstance(x, bool) or not isinstance(x, Integral) for x in (n, c, k)):
        raise ValueError("n, c, k must be integers")
    if n < 1 or not 0 <= c <= n or not 1 <= k <= n:
        raise ValueError("require n>=1, 0<=c<=n, 1<=k<=n")


def pass_at_k(n: int, c: int, k: int) -> float:
    _validate_k(n, c, k)
    return 1.0 - (comb(n-c, k) / comb(n, k) if n-c >= k else 0.0)


def pass_hat_k(n: int, c: int, k: int) -> float:
    _validate_k(n, c, k)
    return comb(c, k) / comb(n, k) if c >= k else 0.0
