import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCENARIOS = ROOT / "research" / "claude-code" / "tools" / "scenarios"


class ScenarioHarnessTests(unittest.TestCase):
    def test_builders_reject_path_like_experiment_ids(self):
        for name, mode in (("build_e44.py", "depth"), ("build_e46.py", "hooks")):
            result = subprocess.run(
                [sys.executable, "-I", str(SCENARIOS / name), "../outside", mode],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0, name)
            self.assertIn("exp id must contain only", result.stderr, name)

    def test_runners_guard_cleanup_and_pipeline_status(self):
        for name in ("run_e44.sh", "run_e46.sh"):
            source = (SCENARIOS / name).read_text(encoding="utf-8")
            self.assertIn("set -o pipefail", source, name)
            self.assertIn("invalid experiment id", source, name)
            self.assertIn("|| exit $?", source, name)

    def test_e46_embeds_its_hook_logger(self):
        source = (SCENARIOS / "build_e46.py").read_text(encoding="utf-8")
        self.assertIn('logger = f"{proj}/hooklog.py"', source)
        self.assertNotIn("C:/Users/sergi/cc-rea-lab/hooklog.py", source)


if __name__ == "__main__":
    unittest.main()
