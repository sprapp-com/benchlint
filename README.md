# benchlint

**A benchmark report is a measurement claim. `benchlint` checks the claim before you believe it.**

Most benchmark numbers in the wild are single runs, with no interval, no sample
size, and a sentence that says one model "outperforms" another. Often the gap is
smaller than the noise, or one item moved the whole score. `benchlint` is a small,
dependency-free toolkit that makes those problems visible:

- **`lint`** — scans a results report (JSON) for reporting gaps: missing
  intervals, missing `n`, ranking language with no test behind it, false
  precision, single-run claims, absent seed spread and item leverage.
- **`reliab`** — from per-item outcomes (CSV), reports the accuracy, a Wilson and
  a bootstrap interval, and the **item leverage**: how many points the score
  moves if you delete a single item.
- **`ci`** — a Wilson interval for one proportion.
- **`diff`** — is an A-vs-B gap real, or within sampling noise?

Standard library only. Works offline. No gate, no cost.

## Install

```bash
git clone https://github.com/sprapp-com/benchlint
cd benchlint
pip install -e .          # or just run with: PYTHONPATH=src python -m benchlint.cli
```

## Use

```bash
# 1. Lint a report (exit code 1 if any critical/major finding)
benchlint lint examples/report_flawed.json

# 2. Reliability of an item-level run
benchlint reliab examples/items.csv --col correct

# 3. One proportion with an interval
benchlint ci --k 400 --n 500

# 4. Is the A-vs-B gap real?
benchlint diff --k1 900 --n1 1000 --k2 700 --n2 1000
```

`examples/report_clean.json` shows a report that passes; `examples/report_flawed.json`
shows one that fails, and why.

## The report schema

```jsonc
{
  "benchmark": "ExampleBench",
  "metric": "accuracy",
  "harness": "scorer version, prompt format, reasoning mode, decoding, full set or sample",
  "models": [
    {"name": "Model A", "score": 0.828, "n": 24213, "ci": [0.823, 0.833]}
  ],
  "runs": [{"seed": 1, "score": 0.8281}, {"seed": 2, "score": 0.8265}],
  "seed_spread": {"n": 2, "mean": 0.827, "sd": 0.001, "range": 0.002},
  "item_leverage": {"max_abs_points": 0.9},
  "claims": ["one plain-language sentence per claim"]
}
```

Only `models` is required. Everything else upgrades the report from "a number"
to "a measurement you can defend".

## Rules

The linter implements the checklist in [`RULES.md`](RULES.md). Codes look like
`L001` (missing interval), `L008` (comparative claim with no interval), and so
on. Severities are `critical`, `major`, `minor`, `nit`; the gate fails on
`critical`/`major`.

## Why this exists

This is a small give-back from work on regional-language model evaluation, where
the same three questions — *how much can this move?, how much does one item
matter?, is the gap real?* — decided whether a published score was trustworthy.
The library is generic on purpose: it is about **benchmark reporting hygiene in
any language**, not any particular model.

## License

Apache-2.0. Use it, fork it, ship it inside your own evaluator.
