"""benchlint command-line interface.

  benchlint lint   <report.json>                 report-hygiene checks
  benchlint reliab <items.csv> [--col name]      reliability of an item-level run
  benchlint ci     --k K --n N                   one proportion with a Wilson CI
  benchlint diff   --k1 K1 --n1 N1 --k2 K2 --n2 N2   is an A-vs-B gap real?
"""
from __future__ import annotations

import argparse
import csv
import json
import sys

from . import stats
from .lint import gate, lint, worst

_SEV_ORDER = {"critical": 0, "major": 1, "minor": 2, "nit": 3}


def _load_items(path, col, idcol):
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            item = {k: (float(v) if _isnum(v) else v) for k, v in row.items()}
            if idcol in item:
                item["id"] = item.pop(idcol)
            rows.append(item)
    if not rows:
        sys.exit(f"no rows in {path}")
    if col not in rows[0]:
        sys.exit(f"column {col!r} not found; columns: {list(rows[0])}")
    return rows


def _isnum(v):
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


def cmd_lint(a):
    rep = json.load(open(a.report))
    findings = lint(rep)
    if not findings:
        print("benchlint: clean — no reporting gaps found.")
        return 0
    for f in sorted(findings, key=lambda f: _SEV_ORDER[f["severity"]]):
        where = f"  [{f['where']}]" if f.get("where") else ""
        print(f"{f['severity'].upper():8} {f['code']}  {f['message']}{where}")
        if f.get("fix"):
            print(f"{'':8}       -> {f['fix']}")
    ok = gate(findings)
    print(f"\nworst: {worst(findings)}   gate(critical/major): "
          f"{'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def cmd_reliab(a):
    items = _load_items(a.items, a.col, a.idcol)
    vals = [it[a.col] for it in items]
    k = sum(1 for v in vals if v >= 1)
    n = len(vals)
    lo, hi = stats.wilson_ci(k, n)
    blo, bhi = stats.bootstrap_ci(vals, n_boot=a.boot, seed=a.seed)
    print(f"items          {n}")
    print(f"accuracy        {k}/{n} = {k/n:.4f}")
    print(f"95% Wilson CI   [{lo:.4f}, {hi:.4f}]")
    print(f"95% boot CI     [{blo:.4f}, {bhi:.4f}]  ({a.boot} resamples)")
    lev = stats.item_leverage(items, key=a.col)[:a.top]
    print(f"\ntop {len(lev)} item leverage (score move if that item is removed):")
    for r in lev:
        print(f"  {str(r['id']):>24}  value={r['value']:.3g}  "
              f"leverage={r['leverage']*100:+.3f} pts")
    return 0


def cmd_ci(a):
    lo, hi = stats.wilson_ci(a.k, a.n)
    print(f"{a.k}/{a.n} = {a.k/a.n:.4f}   95% Wilson CI [{lo:.4f}, {hi:.4f}]")
    return 0


def cmd_diff(a):
    d = stats.two_prop_diff_ci(a.k1, a.n1, a.k2, a.n2)
    verdict = ("real at 95%" if d["significant"]
               else "NOT distinguishable from sampling noise at 95%")
    print(f"A {a.k1}/{a.n1} = {a.k1/a.n1:.4f}")
    print(f"B {a.k2}/{a.n2} = {a.k2/a.n2:.4f}")
    print(f"diff {d['diff']:+.4f}  95% CI [{d['lo']:+.4f}, {d['hi']:+.4f}]")
    print(f"-> {verdict}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="benchlint", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("lint", help="check a JSON report for reporting gaps")
    p.add_argument("report")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("reliab", help="reliability stats from item-level outcomes")
    p.add_argument("items", help="CSV with a header row")
    p.add_argument("--col", default="correct", help="outcome column (default: correct)")
    p.add_argument("--idcol", default="id", help="id column (default: id)")
    p.add_argument("--boot", type=int, default=10000)
    p.add_argument("--seed", type=int, default=12345)
    p.add_argument("--top", type=int, default=5)
    p.set_defaults(func=cmd_reliab)

    p = sub.add_parser("ci", help="Wilson interval for one proportion")
    p.add_argument("--k", type=int, required=True)
    p.add_argument("--n", type=int, required=True)
    p.set_defaults(func=cmd_ci)

    p = sub.add_parser("diff", help="is an A-vs-B proportion gap real?")
    p.add_argument("--k1", type=int, required=True)
    p.add_argument("--n1", type=int, required=True)
    p.add_argument("--k2", type=int, required=True)
    p.add_argument("--n2", type=int, required=True)
    p.set_defaults(func=cmd_diff)

    a = ap.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
