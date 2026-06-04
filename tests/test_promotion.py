import json
import tempfile
import unittest
from pathlib import Path

from io_safety_kit.promotion import (
    evaluate_promotion_candidate,
    load_candidate,
    render_promotion_report,
    summarize_review_evidence,
    write_promotion_report,
)


ROOT = Path(__file__).resolve().parents[1]


class PromotionTests(unittest.TestCase):
    def test_safe_candidate_passes(self):
        candidate = load_candidate(ROOT / "examples" / "promotion-candidate.json")

        result = evaluate_promotion_candidate(candidate)
        report = render_promotion_report(candidate)

        self.assertTrue(result.passed, result.blockers)
        self.assertEqual(result.status, "promotion_candidate_ready")
        self.assertIn("Safe Output Promotion Report", report)
        self.assertIn("External publish performed: `False`", report)
        self.assertIn("Review Evidence", report)
        self.assertIn("Evidence status: `review_evidence_ready`", report)
        self.assertIn("Evidence checks passed: `3/3`", report)
        self.assertIn("Reviewed by role: `maintainer`", report)
        self.assertIn("`synthetic-example`: `passed`", report)

        result_data = result.to_dict()
        self.assertEqual(
            result_data["review_evidence"]["status"],
            "review_evidence_ready",
        )
        self.assertTrue(
            result_data["review_evidence"]["ready_for_public_review"]
        )
        self.assertEqual(result_data["review_evidence"]["check_count"], 3)
        self.assertEqual(result_data["review_evidence"]["passed_check_count"], 3)
        self.assertEqual(
            result_data["review_evidence"]["check_ids"],
            ["synthetic-example", "public-artifacts", "side-effects"],
        )

    def test_secret_marker_blocks_candidate(self):
        candidate = load_candidate(ROOT / "examples" / "promotion-candidate.json")
        candidate["privacy_review"]["source_markers"] = ["secret"]

        result = evaluate_promotion_candidate(candidate)

        self.assertFalse(result.passed)
        self.assertIn("forbidden_source_marker:secret", result.blockers)

    def test_missing_synthetic_example_blocks_candidate(self):
        candidate = load_candidate(ROOT / "examples" / "promotion-candidate.json")
        candidate["privacy_review"]["synthetic_example_used"] = False

        result = evaluate_promotion_candidate(candidate)

        self.assertFalse(result.passed)
        self.assertIn(
            "privacy_review_failed:synthetic_example_used",
            result.blockers,
        )

    def test_missing_review_evidence_blocks_candidate(self):
        candidate = load_candidate(ROOT / "examples" / "promotion-candidate.json")
        candidate.pop("review_evidence")

        result = evaluate_promotion_candidate(candidate)

        self.assertFalse(result.passed)
        self.assertIn("missing_field:review_evidence", result.blockers)
        self.assertIn("review_evidence_required", result.blockers)

    def test_failed_review_evidence_blocks_candidate(self):
        candidate = load_candidate(ROOT / "examples" / "promotion-candidate.json")
        candidate["review_evidence"]["checks"][0]["status"] = "failed"

        result = evaluate_promotion_candidate(candidate)

        self.assertFalse(result.passed)
        self.assertIn(
            "review_evidence_check_not_passed:synthetic-example",
            result.blockers,
        )
        result_data = result.to_dict()
        self.assertEqual(
            result_data["review_evidence"]["status"],
            "review_evidence_blocked",
        )
        self.assertFalse(
            result_data["review_evidence"]["ready_for_public_review"]
        )
        self.assertEqual(
            result_data["review_evidence"]["failed_check_ids"],
            ["synthetic-example"],
        )

    def test_review_evidence_summary_tracks_malformed_checks(self):
        candidate = load_candidate(ROOT / "examples" / "promotion-candidate.json")
        candidate["review_evidence"]["checks"] = [
            {
                "status": "passed",
                "evidence": "A check without an id is not reviewable enough.",
            },
            "manual note",
            {
                "id": "missing-note",
                "status": "passed",
            },
        ]

        summary = summarize_review_evidence(candidate)

        self.assertEqual(summary.status, "review_evidence_blocked")
        self.assertEqual(summary.check_count, 3)
        self.assertEqual(summary.malformed_check_count, 1)
        self.assertEqual(summary.missing_id_check_indices, [0])
        self.assertEqual(summary.missing_evidence_check_ids, ["missing-note"])

    def test_malformed_nested_values_block_without_crashing(self):
        candidate = load_candidate(ROOT / "examples" / "promotion-candidate.json")
        candidate["source"] = "private"
        candidate["promotion_plan"] = "release"
        candidate["review_evidence"] = "checked"

        result = evaluate_promotion_candidate(candidate)
        report = render_promotion_report(candidate)

        self.assertFalse(result.passed)
        self.assertIn("unsupported_source_kind:None", result.blockers)
        self.assertIn("unsupported_promotion_target:None", result.blockers)
        self.assertIn("review_evidence_required", result.blockers)
        self.assertIn("promotion_candidate_blocked", report)

    def test_promotion_report_can_be_written(self):
        candidate = load_candidate(ROOT / "examples" / "promotion-candidate.json")
        markdown = render_promotion_report(candidate)

        with tempfile.TemporaryDirectory() as tmp:
            path = write_promotion_report(markdown, Path(tmp) / "promotion.md")
            written = path.read_text(encoding="utf-8")

        self.assertEqual(written, markdown)


if __name__ == "__main__":
    unittest.main()
