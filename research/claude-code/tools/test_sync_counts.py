import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sync_counts import family_counts, sync


class SyncCountsTests(unittest.TestCase):
    def test_family_counts_use_only_experiment_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "MANIFEST.json"
            path.write_text(json.dumps({"entries": [
                {"id": "E01-a", "kind": "experiment"}, {"id": "E02-b", "kind": "experiment"},
                {"id": "C1-x", "kind": "experiment"}, {"id": "P-plan", "kind": "experiment"},
                {"id": "static", "kind": "static-or-aggregate"},
            ]}), encoding="utf-8")

            self.assertEqual(family_counts(path), {"n": 4, "E": 2, "C": 1, "P": 1})

    def test_sync_rewrites_one_sentence_and_rejects_ambiguity(self):
        counts = {"n": 9, "E": 5, "C": 3, "P": 1}
        text = "done, 3 manifest runs: 1 E, 13 C, 8 P | rest"

        new, _ = sync(text, r"\d+ manifest runs: \d+ E, 13 C, 8 P", "{n} manifest runs: {E} E, {C} C, {P} P", counts)

        self.assertEqual(new, "done, 9 manifest runs: 5 E, 3 C, 1 P | rest")
        with self.assertRaises(ValueError):
            sync(text + " " + text, r"\d+ manifest runs: \d+ E, 13 C, 8 P", "x", counts)
        with self.assertRaises(ValueError):
            sync("nothing here", r"\d+ manifest runs", "x", counts)


if __name__ == "__main__":
    unittest.main()
