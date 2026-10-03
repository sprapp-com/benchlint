"""benchlint — benchmark reporting hygiene: a linter + reliability toolkit.

Ask three questions of any benchmark number before you believe it:
  1. how much can this single score move?   (interval)
  2. how much does one item matter?         (item leverage)
  3. is an A-vs-B gap bigger than the noise? (two-proportion test)

CLI:  benchlint lint | reliab | ci | diff
"""
from .lint import gate, lint, worst
from .stats import (bootstrap_ci, item_leverage, seed_spread,
                    two_prop_diff_ci, wilson_ci)

__version__ = "0.1.0"
__all__ = ["lint", "worst", "gate", "bootstrap_ci", "wilson_ci",
           "seed_spread", "item_leverage", "two_prop_diff_ci"]
