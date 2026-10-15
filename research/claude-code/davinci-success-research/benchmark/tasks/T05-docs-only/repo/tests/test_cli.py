import unittest
from cli import build_parser


class CliTests(unittest.TestCase):
    def test_defaults(self):
        ns = build_parser().parse_args([])
        self.assertEqual((ns.dry_run, ns.retries, ns.timeout), (False, 3, 30.0))


if __name__ == "__main__":
    unittest.main()
