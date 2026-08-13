import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from importlib import resources

from jsonschema import Draft202012Validator

from codex_maintainer_safety_kit.cli import emit
from io_safety_kit.cli import main


ROOT = Path(__file__).resolve().parents[1]


def load_command_result_schema():
    return json.loads(
        resources.files("codex_maintainer_safety_kit")
        .joinpath("schemas/command-result.schema.json")
        .read_text(encoding="utf-8")
    )


class CliErrorContractTests(unittest.TestCase):
    def test_packaged_command_result_schema_matches_public_copy(self):
        public_schema = json.loads(
            (ROOT / "schemas" / "command-result.schema.json").read_text(
                encoding="utf-8"
            )
        )
        packaged_schema = load_command_result_schema()

        self.assertEqual(packaged_schema, public_schema)
        Draft202012Validator.check_schema(packaged_schema)

    def test_json_emit_normalizes_common_envelope(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            emit(
                {
                    "status": "handoff_written",
                    "passed": True,
                    "path": "reports/handoff.md",
                },
                True,
            )

        result = json.loads(stdout.getvalue())
        Draft202012Validator(load_command_result_schema()).validate(result)
        self.assertEqual(result["blockers"], [])
        self.assertEqual(result["warnings"], [])
        self.assertEqual(result["path"], "reports/handoff.md")

    def test_json_emit_wraps_non_array_blockers_and_warnings(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            emit(
                {
                    "status": "blocked",
                    "passed": False,
                    "blockers": "one-blocker",
                    "warnings": "one-warning",
                },
                True,
            )

        result = json.loads(stdout.getvalue())
        Draft202012Validator(load_command_result_schema()).validate(result)
        self.assertEqual(result["blockers"], ["one-blocker"])
        self.assertEqual(result["warnings"], ["one-warning"])

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
