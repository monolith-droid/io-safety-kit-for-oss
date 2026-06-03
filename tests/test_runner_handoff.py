import json
import tempfile
import unittest
from pathlib import Path

from codex_maintainer_safety_kit.handoff import render_handoff
from codex_maintainer_safety_kit.runner import build_run_report, load_job, write_report


ROOT = Path(__file__).resolve().parents[1]


class RunnerHandoffTests(unittest.TestCase):
    def test_report_only_job_plan_passes(self):
        job = load_job(ROOT / "examples" / "maintainer-job.json")

        report = build_run_report(job)

        self.assertTrue(report["passed"], report["blockers"])
        self.assertFalse(report["execution_allowed"])
        self.assertFalse(report["command_executed"])
        self.assertEqual(report["step_count"], 3)

    def test_job_execute_flag_blocks(self):
        job = load_job(ROOT / "examples" / "maintainer-job.json")
        job["execute"] = True

        report = build_run_report(job)

        self.assertFalse(report["passed"])
        self.assertIn("job_execution_not_supported_in_mvp", report["blockers"])

    def test_write_report_and_render_handoff(self):
        job = load_job(ROOT / "examples" / "maintainer-job.json")
        report = build_run_report(job)

        with tempfile.TemporaryDirectory() as tmp:
            path = write_report(report, Path(tmp) / "report.json")
            loaded = json.loads(path.read_text(encoding="utf-8"))

        markdown = render_handoff(loaded)

        self.assertIn("# Maintainer Handoff", markdown)
        self.assertIn("v0.1.0-maintainer-readiness", markdown)


if __name__ == "__main__":
    unittest.main()
