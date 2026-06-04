import copy
import json
import unittest
from pathlib import Path

from io_safety_kit.signature import compute_manifest_payload_digest
from io_safety_kit.trust_policy import evaluate_trust_policy


ROOT = Path(__file__).resolve().parents[1]


def load_example(name):
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))


class TrustPolicyTests(unittest.TestCase):
    def test_signed_fixture_passes_trust_policy(self):
        manifest = load_example("signed-pr-review-manifest.json")
        policy = load_example("trust-policy.json")

        result = evaluate_trust_policy(manifest, policy)

        self.assertTrue(result.passed, result.blockers)
        self.assertEqual(result.status, "trust_policy_allowed")
        self.assertTrue(result.signature_digest_verified)
        self.assertTrue(result.trusted_identity_matched)
        self.assertFalse(result.to_dict()["cryptographic_signature_verified"])

    def test_untrusted_identity_fails_closed(self):
        manifest = copy.deepcopy(load_example("signed-pr-review-manifest.json"))
        manifest["signature"]["identity"] = "unknown@example.invalid"
        policy = load_example("trust-policy.json")

        result = evaluate_trust_policy(manifest, policy)

        self.assertFalse(result.passed)
        blocker = (
            "signature_identity_not_trusted:"
            "unknown@example.invalid:synthetic-public-fixture-key"
        )
        self.assertIn(
            blocker,
            result.blockers,
        )

    def test_operation_outside_policy_fails_closed(self):
        manifest = copy.deepcopy(load_example("signed-pr-review-manifest.json"))
        manifest["operation"] = "security_audit"
        manifest["signature"]["payload_digest"] = compute_manifest_payload_digest(
            manifest
        )
        policy = load_example("trust-policy.json")

        result = evaluate_trust_policy(manifest, policy)

        self.assertFalse(result.passed)
        self.assertIn("signature_operation_not_allowed:security_audit", result.blockers)

    def test_risk_above_policy_fails_closed(self):
        manifest = copy.deepcopy(load_example("signed-pr-review-manifest.json"))
        manifest["risk_level"] = "high"
        manifest["signature"]["payload_digest"] = compute_manifest_payload_digest(
            manifest
        )
        policy = load_example("trust-policy.json")

        result = evaluate_trust_policy(manifest, policy)

        self.assertFalse(result.passed)
        self.assertIn(
            "signature_risk_level_exceeds_policy:manifest=high:policy=medium",
            result.blockers,
        )

    def test_tampered_manifest_blocks_before_policy_can_pass(self):
        manifest = copy.deepcopy(load_example("signed-pr-review-manifest.json"))
        manifest["reason"] = "Review a different pull request than the approved one."
        policy = load_example("trust-policy.json")

        result = evaluate_trust_policy(manifest, policy)

        self.assertFalse(result.passed)
        self.assertFalse(result.signature_digest_verified)
        self.assertIn("signature_payload_digest_mismatch", result.blockers)

    def test_repository_mismatch_fails_closed(self):
        manifest = load_example("signed-pr-review-manifest.json")
        policy = copy.deepcopy(load_example("trust-policy.json"))
        policy["repository"] = "example/other-repo"

        result = evaluate_trust_policy(manifest, policy)

        self.assertFalse(result.passed)
        blocker = (
            "policy_repository_mismatch:"
            "policy=example/other-repo:"
            "manifest=monolith-droid/io-safety-kit-for-oss"
        )
        self.assertIn(
            blocker,
            result.blockers,
        )


if __name__ == "__main__":
    unittest.main()
