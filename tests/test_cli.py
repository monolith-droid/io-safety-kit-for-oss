import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from io_safety_kit.cli import main


class CliErrorContractTests(unittest.TestCase):
    def test_json_error_is_machine_readable_and_does_not_expose_missing_path(self):
        missing_path = Path("private-workspace") / "missing-manifest.json"
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = main(
                ["validate", "--manifest", str(missing_path), "--json"]
            )

        result = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 99)
        self.assertEqual(result["status"], "command_error")
        self.assertFalse(result["passed"])
        self.assertEqual(result["blockers"], ["command_error:FileNotFoundError"])
        self.assertEqual(result["warnings"], [])
        self.assertEqual(result["command"], "validate")
        self.assertEqual(result["error_type"], "FileNotFoundError")
        self.assertNotIn(str(missing_path), stdout.getvalue())

    def test_json_error_reports_invalid_json_without_exposing_contents(self):
        private_marker = "private-token-value"
        stdout = io.StringIO()

        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "invalid.json"
            manifest_path.write_text(
                '{"private": "' + private_marker + '"', encoding="utf-8"
            )
            with redirect_stdout(stdout):
                exit_code = main(
                    ["validate", "--manifest", str(manifest_path), "--json"]
                )

        result = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 99)
        self.assertEqual(result["blockers"], ["command_error:JSONDecodeError"])
        self.assertEqual(result["warnings"], [])
        self.assertNotIn(private_marker, stdout.getvalue())
        self.assertNotIn(str(manifest_path), stdout.getvalue())

    def test_text_error_is_sanitized(self):
        missing_path = Path("private-workspace") / "missing-manifest.json"
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            exit_code = main(["validate", "--manifest", str(missing_path)])

        self.assertEqual(exit_code, 99)
        self.assertEqual(stderr.getvalue().strip(), "error: FileNotFoundError")
        self.assertNotIn(str(missing_path), stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
