import json
import tempfile
import unittest
from pathlib import Path

from io_safety_kit.pr_review import render_pr_review, write_pr_review


ROOT = Path(__file__).resolve().parents[1]


def load_example(name):
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))


class PrReviewTests(unittest.TestCase):
    def test_pr_review_manifest_renders_deterministic_markdown(self):
        manifest = load_example("pr-review-manifest.json")

        first = render_pr_review(manifest)
        second = render_pr_review(manifest)

        self.assertEqual(first, second)
        self.assertIn("# PR Review Report", first)
        self.assertIn("Gate status: `gate_allowed_report_only`", first)
        self.assertIn("- GitHub mutation performed: `False`", first)
        self.assertIn("- `read_pull_request_diff`", first)
        self.assertIn("Review this local report before drafting GitHub comments.", first)

    def test_pr_review_report_can_be_written(self):
        manifest = load_example("pr-review-manifest.json")
        markdown = render_pr_review(manifest)

        with tempfile.TemporaryDirectory() as tmp:
            path = write_pr_review(markdown, Path(tmp) / "pr-review.md")
            written = path.read_text(encoding="utf-8")

        self.assertEqual(written, markdown)
        self.assertIn("PR Review Report", written)


if __name__ == "__main__":
    unittest.main()
