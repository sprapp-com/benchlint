import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from benchlint.lint import gate, lint, worst

HERE = os.path.dirname(__file__)
EX = os.path.join(HERE, "..", "examples")


def codes(report):
    return {f["code"] for f in lint(report)}


def load(name):
    with open(os.path.join(EX, name)) as f:
        return json.load(f)


class TestLint(unittest.TestCase):
    def test_flawed_report_fails_gate(self):
        rep = load("report_flawed.json")
        f = lint(rep)
        self.assertFalse(gate(f))
        # missing interval, single-run claim, comparative w/o interval
        for c in ("L001", "L003", "L004", "L008"):
            self.assertIn(c, {x["code"] for x in f})

    def test_clean_report_passes_gate(self):
        self.assertTrue(gate(lint(load("report_clean.json"))))

    def test_missing_n_flagged(self):
        self.assertIn("L002", codes({"models": [{"name": "x", "score": 0.5}]}))

    def test_overprecision_flagged(self):
        rep = {"harness": "h",
               "models": [{"name": "x", "score": 0.82831, "n": 20, "ci": [0.7, 0.9]}]}
        self.assertIn("L005", codes(rep))

    def test_seed_spread_absent_when_comparing(self):
        rep = {"harness": "h", "models": [
            {"name": "a", "score": 0.8, "n": 100, "ci": [0.7, 0.9]},
            {"name": "b", "score": 0.7, "n": 100, "ci": [0.6, 0.8]}]}
        self.assertIn("L006", codes(rep))

    def test_worst_severity(self):
        self.assertEqual(worst(lint(load("report_flawed.json"))), "major")


if __name__ == "__main__":
    unittest.main()
