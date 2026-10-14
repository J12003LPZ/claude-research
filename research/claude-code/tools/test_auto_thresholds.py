import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from auto_thresholds import bounds, derive, parse_run_id


class AutoThresholdTests(unittest.TestCase):
    def test_parse_run_ids(self):
        self.assertEqual(parse_run_id("E41t-sev25_5"), (25.5, None))
        self.assertEqual(parse_run_id("E41t-sev30"), (30.0, None))
        self.assertEqual(parse_run_id("E41u-s2-35_5"), (30.0, 35.5))
        self.assertEqual(parse_run_id("E41c-auto-sev18"), (18.0, None))
        self.assertIsNone(parse_run_id("E42-auto-denials"))

    def test_strict_threshold_bounds(self):
        points = [(0, True), (25, True), (25.5, False), (30, False)]
        self.assertEqual(bounds(points), (25, 25.5))

    def test_non_monotonic_scores_are_rejected(self):
        with self.assertRaises(ValueError):
            bounds([(10, False), (20, True)])

    def test_derive_separates_the_two_stages(self):
        rows = [
            {"stage1": 20.0, "stage2": None, "classifier_requests": 1, "tool_ran": True},
            {"stage1": 30.0, "stage2": None, "classifier_requests": 2, "tool_ran": False},
            {"stage1": 30.0, "stage2": 35.0, "classifier_requests": 2, "tool_ran": True},
            {"stage1": 30.0, "stage2": 40.0, "classifier_requests": 2, "tool_ran": False},
        ]
        self.assertEqual(derive(rows), {
            "t1": {"highest_allowed": 20.0, "lowest_escalated": 30.0},
            "t2": {"highest_allowed": 35.0, "lowest_denied": 40.0},
        })


if __name__ == "__main__":
    unittest.main()
