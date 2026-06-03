import json
import unittest
from pathlib import Path

from codex_maintainer_safety_kit.approval import evaluate_gate, validate_manifest


ROOT = Path(__file__).resolve().parents[1]


def load_example(name):
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))


class ApprovalTests(unittest.TestCase):
    def test_pr_review_manifest_passes_gate(self):
        manifest = load_example("pr-review-manifest.json")

        validation = validate_manifest(manifest)
        gate = evaluate_gate(manifest)

        self.assertTrue(validation.passed, validation.blockers)
        self.assertTrue(gate.passed, gate.blockers)
        self.assertEqual(gate.status, "gate_allowed_report_only")

    def test_pending_security_audit_fails_closed(self):
        manifest = load_example("security-audit-manifest.json")

        validation = validate_manifest(manifest)
        gate = evaluate_gate(manifest)

        self.assertTrue(validation.passed, validation.blockers)
        self.assertFalse(gate.passed)
        self.assertIn("approval_not_approved:pending", gate.blockers)

    def test_blocked_action_invalidates_manifest(self):
        manifest = load_example("pr-review-manifest.json")
        manifest["allowed_actions"].append("read_secret_values")

        validation = validate_manifest(manifest)

        self.assertFalse(validation.passed)
        self.assertIn("blocked_action:read_secret_values", validation.blockers)

    def test_operation_mismatch_blocks_gate(self):
        manifest = load_example("issue-triage-manifest.json")

        gate = evaluate_gate(manifest, operation="pr_review")

        self.assertFalse(gate.passed)
        self.assertTrue(
            any(blocker.startswith("operation_mismatch:") for blocker in gate.blockers)
        )


if __name__ == "__main__":
    unittest.main()
