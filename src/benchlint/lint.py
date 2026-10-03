"""The linter: check a benchmark report for reporting-hygiene gaps.

Input is a small JSON report (schema in README). Output is a list of findings,
each with a code, a severity, the offending location, and a concrete fix. The
rules here are the machine-readable form of the checklist in RULES.md.
"""
from __future__ import annotations

import math

SEVERITIES = ("critical", "major", "minor", "nit")

RANK_WORDS = (
    "outperform", "outperforms", "outperformed", "better than", "beats", "beat ",
    "worse than", "ranks", "ranked", "ranking", "safest", "state-of-the-art",
    "sota", "leads", "ahead of", "superior",
)


def _decimals(x):
    s = repr(float(x))
    if "e" in s or "E" in s:
        return 6
    return len(s.split(".")[1].rstrip("0")) if "." in s else 0


def _precision_floor(n, p=0.5):
    """Reasonable number of decimals given n samples: anything past the
    standard-error scale is false precision. Uses the proportion SE when the
    score looks like a proportion, otherwise the 1/sqrt(n) scale."""
    if not n or n <= 0:
        return 3
    if p is not None and 0.0 < p < 1.0:
        se = math.sqrt(p * (1 - p) / n)
    else:
        se = 1.0 / math.sqrt(n)
    if se <= 0:
        return 3
    return max(0, int(round(-math.log10(se))))


def lint(report):
    findings = []

    def add(code, severity, message, where=None, fix=None):
        findings.append({"code": code, "severity": severity,
                         "message": message, "where": where, "fix": fix})

    models = report.get("models") or []
    claims = report.get("claims") or []
    has_ci = any(m.get("ci") for m in models)
    n_models = len(models)

    # --- protocol description ------------------------------------------------
    if not (report.get("harness") or report.get("protocol") or report.get("method")):
        add("L009", "minor",
            "report does not name the harness/protocol and settings behind the numbers",
            "report",
            "add a 'harness'/'protocol' field: scorer version, prompt format, "
            "reasoning mode, decoding settings")

    # --- per-model checks ----------------------------------------------------
    for m in models:
        name = m.get("name", "<unnamed>")
        if not m.get("n"):
            add("L002", "minor",
                f"model {name!r} has no sample size (n)",
                f"models[{name}]",
                "state n, and whether it is the full set or a sample")
        if not m.get("ci"):
            add("L001", "major",
                f"model {name!r} reports a point score with no interval",
                f"models[{name}]",
                "add a 95% interval (bootstrap_ci / wilson_ci); state the method")
        n, sc = m.get("n"), m.get("score")
        if n and sc is not None:
            floor = _precision_floor(n, sc if isinstance(sc, (int, float)) else 0.5)
            if _decimals(sc) > floor:
                add("L005", "nit",
                    f"model {name!r} reports {sc} ({_decimals(sc)} decimals) but "
                    f"n={n} supports about {floor}",
                    f"models[{name}].score",
                    "round to the precision the sample size supports")

    # --- comparative / ranking claims ---------------------------------------
    for c in claims:
        text = c if isinstance(c, str) else c.get("text", "")
        low = text.lower()
        is_rank = any(w in low for w in RANK_WORDS)
        if is_rank and not has_ci:
            add("L008", "major",
                f"comparative claim with no interval on any model: {text!r}",
                "claims",
                "attach intervals and state whether they overlap before ranking")
        if is_rank:
            add("L004", "minor",
                f"ranking language: {text!r}",
                "claims",
                "replace 'outperforms/ranks/beats' with a neutral, "
                "interval-aware statement or drop it")

    # --- reliability provenance ---------------------------------------------
    runs = report.get("runs")
    if runs is not None and len(runs) == 1:
        if claims:
            add("L003", "major",
                "single-run result used to support a claim",
                "runs",
                "run at least 2-3 seeds and report the spread, or state the "
                "claim is single-run and provisional")
    if n_models >= 2 and not report.get("seed_spread"):
        add("L006", "minor",
            "multiple models compared but no run-to-run seed spread reported",
            "report",
            "report seed_spread() so readers see the noise floor between models")
    if not report.get("items") and not report.get("item_leverage"):
        add("L007", "minor",
            "no item-level outcomes, so item leverage cannot be checked",
            "report",
            "publish per-item correctness (or item_leverage) — one item can "
            "move a composite by several points")

    order = {s: i for i, s in enumerate(SEVERITIES)}
    findings.sort(key=lambda f: order[f["severity"]])
    return findings


def worst(findings):
    order = {s: i for i, s in enumerate(SEVERITIES)}
    if not findings:
        return None
    return min(findings, key=lambda f: order[f["severity"]])["severity"]


def gate(findings, fail_on=("critical", "major")):
    """True when the report passes: no finding at or above `fail_on`."""
    order = {s: i for i, s in enumerate(SEVERITIES)}
    limit = max(order[s] for s in fail_on)
    return all(order[f["severity"]] > limit for f in findings)
