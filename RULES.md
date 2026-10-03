# The benchlint checklist

Before a benchmark score becomes a claim, it should survive these questions.
Each maps to a linter code.

## 1. Can the score move? (intervals)

| | |
|---|---|
| **L001** *major* | A point score is reported with no interval. Add a 95% interval and say how you made it. |
| **L002** *minor* | No sample size `n`. State it, and whether it is the full set or a sample. |
| **L005** *nit* | False precision: more decimals than the standard error supports. Round down. |

A single-run composite over a few hundred items carries an interval of several
points. Two models a few points apart are usually **not** distinguishable.

## 2. How much does one item matter? (leverage)

| | |
|---|---|
| **L007** *minor* | No item-level outcomes, so leverage cannot be checked. One item can move a small composite by several points. |

`benchlint reliab` computes the exact move for every item, sorted by size.

## 3. Is the gap real? (comparisons)

| | |
|---|---|
| **L008** *major* | A comparative claim with no interval on any model. |
| **L004** *minor* | Ranking language ("outperforms", "ranks", "safest") with no test behind it. |
| **L006** *minor* | Multiple models compared, but no run-to-run seed spread reported. |

`benchlint diff` answers "is the gap bigger than the noise?" directly.

## 4. Is it reproducible? (provenance)

| | |
|---|---|
| **L003** *major* | A single run is used to support a claim. Run 2–3 seeds, report the spread, or label the claim provisional. |
| **L009** *minor* | The harness/protocol is not named: scorer version, prompt format, reasoning mode, decoding settings. |

## The habit

1. Report the interval, not just the score.
2. Report `n`.
3. Report the seed spread.
4. Publish item-level outcomes, or at least the leverage.
5. Say "the intervals overlap", not "we outperform".
6. Name the protocol so someone can reproduce it.
