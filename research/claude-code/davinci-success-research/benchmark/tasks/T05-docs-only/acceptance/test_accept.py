import os
import re
import unittest

README = os.path.join(os.getcwd(), "README.md")


def text():
    with open(README, encoding="utf-8") as fh:
        return fh.read()


def line_with(flag):
    for ln in text().splitlines():
        if flag in ln:
            return ln
    return ""


class Accept(unittest.TestCase):
    def test_usage_section(self):
        self.assertRegex(text(), r"(?m)^## Usage\s*$")

    def test_every_flag_present(self):
        for flag in ("--dry-run", "--retries", "--timeout"):
            self.assertIn(flag, text())

    def test_retries_default(self):
        self.assertRegex(line_with("--retries"), r"\b3\b")

    def test_timeout_default(self):
        self.assertRegex(line_with("--timeout"), r"\b30(\.0)?\b")

    def test_no_invented_flags(self):
        found = set(re.findall(r"--[a-z][a-z-]*", text()))
        self.assertLessEqual(found, {"--dry-run", "--retries", "--timeout", "--help"})


if __name__ == "__main__":
    unittest.main()
