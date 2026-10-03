"""Reliability statistics for benchmark scores. Pure standard library.

Every function here answers a question a benchmark report should answer before it
makes a claim:

  * how much can this single score move?          -> bootstrap_ci / wilson_ci
  * how much does one benchmark item matter?      -> item_leverage
  * how much does the run-to-run seed move it?    -> seed_spread
  * is this A-vs-B difference even real?          -> two_prop_diff_ci

No numpy, no scipy: install nothing, run anywhere.
"""
from __future__ import annotations

import math
import random

Z95 = 1.959963984540054  # two-sided 95% normal quantile


def mean(xs):
    xs = list(xs)
    if not xs:
        raise ValueError("mean() of empty sequence")
    return sum(xs) / len(xs)


def bootstrap_ci(values, n_boot=10000, alpha=0.05, seed=12345):
    """Percentile bootstrap CI for the mean of `values`.

    Use when you have per-item outcomes and want an interval that does not assume
    a distribution. Returns (lo, hi).
    """
    values = [float(v) for v in values]
    if not values:
        raise ValueError("bootstrap_ci() needs at least one value")
    rng = random.Random(seed)
    n = len(values)
    means = sorted(mean(rng.choices(values, k=n)) for _ in range(n_boot))
    lo = means[max(0, int((alpha / 2) * n_boot))]
    hi = means[min(n_boot - 1, int((1 - alpha / 2) * n_boot))]
    return lo, hi


def wilson_ci(k, n, z=Z95):
    """Wilson score interval for a proportion k/n. Stable at 0 and 1, unlike
    the textbook normal interval. Returns (lo, hi)."""
    if n <= 0:
        raise ValueError("wilson_ci() needs n > 0")
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return centre - half, centre + half


def seed_spread(runs, key="score"):
    """Run-to-run spread across seeds. Accepts a list of dicts or a list of floats."""
    xs = [float(r[key]) if isinstance(r, dict) else float(r) for r in runs]
    if not xs:
        raise ValueError("seed_spread() needs at least one run")
    m = mean(xs)
    if len(xs) > 1:
        sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))
    else:
        sd = 0.0
    return {"n": len(xs), "mean": m, "sd": sd, "min": min(xs),
            "max": max(xs), "range": max(xs) - min(xs)}


def item_leverage(items, key="correct"):
    """How much the overall score moves when one item is removed.

    This is the "one answer can move the score by X points" number. Returns a
    list sorted by leverage magnitude, each dict:
        {id, value, leverage}
    where leverage = mean(all without this item) - mean(all), i.e. the signed
    score move if the item is removed (positive = removing it raises the score).
    """
    if key == "correct" and "correct" not in items[0]:
        for alt in ("value", "score", "pass"):
            if alt in items[0]:
                key = alt
                break
    vals = [float(it[key]) for it in items]
    full = mean(vals)
    n = len(vals)
    out = []
    for i, it in enumerate(items):
        rest = [v for j, v in enumerate(vals) if j != i]
        out.append({"id": it.get("id", i),
                    "value": vals[i],
                    "leverage": mean(rest) - full})
    out.sort(key=lambda r: abs(r["leverage"]), reverse=True)
    return out


def two_prop_diff_ci(k1, n1, k2, n2, z=Z95):
    """Difference of two proportions (p1 - p2) with a normal-approx CI.

    Returns {diff, lo, hi, significant}: significant is True when the interval
    excludes zero, i.e. the difference survives the sampling noise at 95%.
    """
    if n1 <= 0 or n2 <= 0:
        raise ValueError("two_prop_diff_ci() needs n1,n2 > 0")
    p1, p2 = k1 / n1, k2 / n2
    d = p1 - p2
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    lo, hi = d - z * se, d + z * se
    return {"diff": d, "lo": lo, "hi": hi,
            "significant": lo > 0 or hi < 0}
