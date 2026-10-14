import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_matrix import footer, tally

SAMPLE = """\
| # | Behaviour | Evidence | Spec | Status |
|---|---|---|---|---|
| 1 | One | E1 | 1 | Verified |
| 2 | Two | E2 | 1 | Verified (spec defined) |
| 3a | Three | E3 | 1 | Partially verified: details |
| 4 | Four | none | 1 | Untested |
| 5 | Five | none | 1 | Blocked |

Counts: 5 behaviours enumerated. Verified 2, partially verified 1, untested 1, blocked 1.
"""


class CheckMatrixTests(unittest.TestCase):
    def test_tally_reads_status_prefix_of_last_cell(self):
        rows, counts = tally(SAMPLE)
        self.assertEqual(rows, 5)
        self.assertEqual(counts["Verified"], 2)
        self.assertEqual(counts["Partially verified"], 1)

    def test_footer_matches_tally(self):
        rows, counts = tally(SAMPLE)
        n, want = footer(SAMPLE)
        self.assertEqual(n, rows)
        self.assertEqual({k: counts[k] for k in want}, want)

    def test_rows_outside_the_behaviour_section_are_ignored(self):
        text = (
            "## 1. Subsystems\n| 7 | Subsystem row | Blocked |\n\n"
            "## 2. Behavioural test matrix\n" + SAMPLE + "\n"
            "## 4. Open questions\n| 9 | A question | why | attempt | Blocked by tooling |\n"
        )

        rows, counts = tally(text)

        self.assertEqual(rows, 5)
        self.assertEqual(counts["Blocked"], 1)

    def test_missing_footer_is_an_error(self):
        with self.assertRaises(ValueError):
            footer("no footer here")


if __name__ == "__main__":
    unittest.main()
