import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from codex_maintainer_safety_kit import approval as approval_impl
from io_safety_kit.approval import evaluate_gate, validate_manifest


ROOT = Path(__file__).resolve().parents[1]


def load_example(name):
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))


def load_blocked_action_fixture(name):
    return json.loads(
        (ROOT / "tests" / "fixtures" / "blocked_actions" / name).read_text(
            encoding="utf-8"
        )
    )


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

    def test_blocked_action_fixtures_fail_closed(self):
        cases = [
            ("read_secret.json", "blocked_action:read_secret_values"),
            ("force_push.json", "blocked_action:force_push_to_main"),
            ("change_visibility.json", "blocked_action:change_visibility_public"),
            (
                "disable_branch_protection.json",
                "blocked_action:disable_branch_protection_on_main",
            ),
        ]

        for fixture_name, expected_blocker in cases:
            with self.subTest(fixture=fixture_name):
                manifest = load_blocked_action_fixture(fixture_name)

                validation = validate_manifest(manifest)
                gate = evaluate_gate(manifest)

                self.assertFalse(validation.passed)
                self.assertIn(expected_blocker, validation.blockers)
                self.assertFalse(gate.passed)
                self.assertEqual(gate.status, "gate_blocked_fail_closed")
                self.assertIn(expected_blocker, gate.blockers)

    def test_operation_mismatch_blocks_gate(self):
        manifest = load_example("issue-triage-manifest.json")

        gate = evaluate_gate(manifest, operation="pr_review")

        self.assertFalse(gate.passed)
        self.assertTrue(
            any(blocker.startswith("operation_mismatch:") for blocker in gate.blockers)
        )

    def test_packaged_schema_matches_public_schema(self):
        packaged_schema = approval_impl.load_approval_manifest_schema()
        public_schema = json.loads(
            (ROOT / "schemas" / "approval-manifest.schema.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(packaged_schema, public_schema)

    def test_schema_validation_falls_back_without_jsonschema(self):
        manifest = load_example("pr-review-manifest.json")

        with patch.object(
            approval_impl, "_load_jsonschema_validator", return_value=None
        ):
            validation = validate_manifest(manifest, use_schema=True)

        self.assertTrue(validation.passed, validation.blockers)
        self.assertIn(
            "jsonschema_not_installed_schema_validation_skipped",
            validation.warnings,
        )
        self.assertEqual(
            validation.schema_validation,
            {
                "requested": True,
                "available": False,
                "schema": "schemas/approval-manifest.schema.json",
                "status": "schema_validation_skipped",
                "errors": [],
            },
        )

    def test_schema_validation_reports_schema_errors_when_available(self):
        if approval_impl._load_jsonschema_validator() is None:
            self.skipTest("jsonschema is not installed")

        manifest = copy.deepcopy(load_example("pr-review-manifest.json"))
        manifest["schema_version"] = "legacy.approval.v1"

        validation = validate_manifest(manifest, use_schema=True)
        data = validation.to_dict()

        self.assertFalse(validation.passed)
        self.assertTrue(
            any(
                blocker.startswith("schema_error:schema_version:")
                for blocker in validation.blockers
            )
        )
        self.assertEqual(data["schema_validation"]["status"], "schema_invalid")
        self.assertEqual(
            data["schema_validation"]["errors"][0]["path"],
            "schema_version",
        )


if __name__ == "__main__":
    unittest.main()
