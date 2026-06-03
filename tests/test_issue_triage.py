import json
import tempfile
import unittest
from pathlib import Path

from io_safety_kit.issue_triage import render_issue_triage, write_issue_triage


ROOT = Path(__file__).resolve().parents[1]


def load_example(name):
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))


class IssueTriageTests(unittest.TestCase):
    def test_issue_triage_manifest_renders_deterministic_markdown(self):
        manifest = load_example("issue-triage-manifest.json")

        first = render_issue_triage(manifest)
        second = render_issue_triage(manifest)

        self.assertEqual(first, second)
        self.assertIn("# Issue Triage Report", first)
        self.assertIn("Gate status: `gate_allowed_report_only`", first)
        self.assertIn("- Labels mutated: `False`", first)
        self.assertIn("- `classify_issue_labels`", first)
        self.assertIn("Label suggestions are drafts for maintainer review.", first)

    def test_issue_triage_report_can_be_written(self):
        manifest = load_example("issue-triage-manifest.json")
        markdown = render_issue_triage(manifest)

        with tempfile.TemporaryDirectory() as tmp:
            path = write_issue_triage(markdown, Path(tmp) / "issue-triage.md")
            written = path.read_text(encoding="utf-8")

        self.assertEqual(written, markdown)
        self.assertIn("Issue Triage Report", written)


if __name__ == "__main__":
    unittest.main()
