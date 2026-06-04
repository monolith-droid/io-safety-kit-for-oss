import copy
import json
import unittest
from pathlib import Path

from io_safety_kit.signature import (
    canonical_manifest_payload,
    check_signature_metadata,
    compute_manifest_payload_digest,
)


ROOT = Path(__file__).resolve().parents[1]


def load_example(name):
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))


class SignatureTests(unittest.TestCase):
    def test_signed_pr_review_fixture_passes_digest_check(self):
        manifest = load_example("signed-pr-review-manifest.json")

        result = check_signature_metadata(manifest)

        self.assertTrue(result.passed, result.blockers)
        self.assertEqual(result.status, "signature_digest_verified")
        self.assertEqual(
            result.computed_payload_digest,
            manifest["signature"]["payload_digest"],
        )
        self.assertIn(
            "signature_check_verifies_public_digest_metadata_only",
            result.warnings,
        )
        self.assertFalse(result.to_dict()["cryptographic_signature_verified"])

    def test_canonical_payload_excludes_signature_metadata(self):
        manifest = load_example("signed-pr-review-manifest.json")

        payload = canonical_manifest_payload(manifest)
        payload_data = json.loads(payload)

        self.assertIn("approval", payload_data)
        self.assertNotIn("signature", payload_data)

    def test_tampered_manifest_fails_digest_check(self):
        manifest = copy.deepcopy(load_example("signed-pr-review-manifest.json"))
        manifest["reason"] = "Review a different pull request than the approved one."

        result = check_signature_metadata(manifest)

        self.assertFalse(result.passed)
        self.assertIn("signature_payload_digest_mismatch", result.blockers)
        self.assertNotEqual(
            result.computed_payload_digest,
            manifest["signature"]["payload_digest"],
        )

    def test_missing_signature_fails_closed(self):
        manifest = load_example("pr-review-manifest.json")

        result = check_signature_metadata(manifest)

        self.assertFalse(result.passed)
        self.assertIn("signature_missing", result.blockers)

    def test_digest_helper_is_stable_for_fixture(self):
        manifest = load_example("signed-pr-review-manifest.json")

        digest = compute_manifest_payload_digest(manifest)

        self.assertEqual(
            digest,
            "sha256:92daa6d24fe7e7c1c901dcd3750a3479f4f978894862aeb528df3350c2d85611",
        )


if __name__ == "__main__":
    unittest.main()
