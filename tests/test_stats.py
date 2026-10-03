import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from benchlint import stats


class TestWilson(unittest.TestCase):
    def test_center_and_bounds(self):
        lo, hi = stats.wilson_ci(400, 500)
        self.assertLess(lo, 0.8)
        self.assertGreater(hi, 0.8)
        self.assertGreater(hi, lo)

    def test_at_boundary_is_stable(self):
        lo, hi = stats.wilson_ci(500, 500)
        self.assertEqual(hi, 1.0)
        self.assertLess(lo, 1.0)

    def test_shrinks_with_n(self):
        w_small = stats.wilson_ci(40, 50)
        w_big = stats.wilson_ci(4000, 5000)
        self.assertLess(w_big[1] - w_big[0], w_small[1] - w_small[0])


class TestBootstrap(unittest.TestCase):
    def test_covers_the_mean(self):
        vals = [1] * 34 + [0] * 6
        lo, hi = stats.bootstrap_ci(vals, n_boot=4000)
        self.assertLessEqual(lo, 0.85)
        self.assertGreaterEqual(hi, 0.85)

    def test_deterministic(self):
        vals = [1, 0, 1, 1, 0, 1, 1, 1]
        self.assertEqual(stats.bootstrap_ci(vals), stats.bootstrap_ci(vals))

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            stats.bootstrap_ci([])


class TestSeedSpread(unittest.TestCase):
    def test_basic(self):
        s = stats.seed_spread([{"score": 0.80}, {"score": 0.90}])
        self.assertEqual(s["n"], 2)
        self.assertAlmostEqual(s["mean"], 0.85)
        self.assertGreater(s["sd"], 0)

    def test_single_run_is_zero_sd(self):
        self.assertEqual(stats.seed_spread([0.7])["sd"], 0.0)


class TestItemLeverage(unittest.TestCase):
    def test_top_item_is_the_outlier(self):
        items = [{"id": i, "correct": 1} for i in range(9)] + [{"id": "bad", "correct": 0}]
        top = stats.item_leverage(items)[0]
        self.assertEqual(top["id"], "bad")
        self.assertGreater(top["leverage"], 0)

    def test_magnitude_is_one_over_n_minus_one(self):
        items = [{"id": i, "correct": 1} for i in range(9)] + [{"id": "bad", "correct": 0}]
        top = stats.item_leverage(items)[0]
        # (x - mean) / (n - 1) = (0 - 0.9) / 9
        self.assertAlmostEqual(top["leverage"], 0.1, places=6)


class TestDiff(unittest.TestCase):
    def test_real_gap(self):
        d = stats.two_prop_diff_ci(900, 1000, 700, 1000)
        self.assertTrue(d["significant"])
        self.assertGreater(d["lo"], 0)

    def test_noise_not_significant(self):
        d = stats.two_prop_diff_ci(810, 1000, 800, 1000)
        self.assertFalse(d["significant"])
        self.assertLess(d["lo"], 0)
        self.assertGreater(d["hi"], 0)


if __name__ == "__main__":
    unittest.main()
