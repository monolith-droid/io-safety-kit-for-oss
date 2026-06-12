import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "examples" / "cross-platform-dogfooding-report.json"
DOC = ROOT / "docs" / "cross-platform-dogfooding.md"


class CrossPlatformDogfoodingTests(unittest.TestCase):
    def test_cross_platform_report_is_public_safe_and_report_only(self):
        report = json.loads(REPORT.read_text(encoding="utf-8"))

        self.assertTrue(report["passed"], report["blockers"])
        self.assertEqual(report["mode"], "report_only")
        self.assertEqual(report["status"], "cross_platform_dogfooding_ready")
        self.assertEqual(report["blockers"], [])
        self.assertIsInstance(report["warnings"], list)
        self.assertEqual(
            {lane["lane_id"] for lane in report["lanes"]},
            {"implementation-lane", "operations-lane"},
        )

        for lane in report["lanes"]:
            self.assertTrue(lane["report_only"])
            self.assertIsInstance(lane["blockers"], list)
            self.assertIsInstance(lane["warnings"], list)
            self.assertIsInstance(lane["promotion_candidates"], list)
            self.assertIsInstance(lane["private_boundaries"], list)
            self.assertFalse(lane["side_effects"]["command_executed"])
            self.assertFalse(lane["side_effects"]["external_publish_performed"])
            self.assertFalse(lane["side_effects"]["scheduler_mutated"])
            self.assertFalse(lane["side_effects"]["worker_dispatched"])
            self.assertFalse(lane["side_effects"]["secret_values_read"])

    def test_cross_platform_report_uses_synthetic_boundaries(self):
        text = REPORT.read_text(encoding="utf-8")

        forbidden_fragments = [
            "C:\\",
            "/Users/",
            "GoogleDrive",
            "approval_id",
            "token",
            "password",
            "\"secret_value\":",
        ]
        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, text)

    def test_cross_platform_doc_links_fixture_and_lanes(self):
        body = DOC.read_text(encoding="utf-8")

        self.assertIn("examples/cross-platform-dogfooding-report.json", body)
        self.assertIn("implementation_lane", body)
        self.assertIn("operations_lane", body)
        self.assertIn("report-only", body)
        self.assertIn("Use `iosk promotion-check`", body)


if __name__ == "__main__":
    unittest.main()
