"""Gate tests for the stream-json experiment harness."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_stream import build_auto_permission_response


class BuildAutoPermissionResponseTests(unittest.TestCase):
    def test_allows_can_use_tool_with_matching_request_id(self):
        self.assertEqual(
            build_auto_permission_response("host-17", "can_use_tool", "allow", "ignored"),
            {
                "type": "control_response",
                "response": {
                    "subtype": "success",
                    "request_id": "host-17",
                    "response": {"behavior": "allow"},
                },
            },
        )

    def test_denial_preserves_the_configured_message(self):
        self.assertEqual(
            build_auto_permission_response("host-18", "can_use_tool", "deny", "Lab policy denied this"),
            {
                "type": "control_response",
                "response": {
                    "subtype": "success",
                    "request_id": "host-18",
                    "response": {"behavior": "deny", "message": "Lab policy denied this"},
                },
            },
        )

    def test_does_not_answer_unrelated_host_requests(self):
        self.assertIsNone(build_auto_permission_response("host-19", "get_status", "allow", "ignored"))

    def test_does_not_answer_when_auto_response_is_disabled(self):
        self.assertIsNone(build_auto_permission_response("host-20", "can_use_tool", None, "ignored"))


if __name__ == "__main__":
    unittest.main()
