from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .approval import evaluate_gate, load_json, validate_manifest
from .handoff import load_report, render_handoff, write_handoff
from .runner import build_run_report, load_job, write_report


def emit(data: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return
    print(f"status: {data.get('status')}")
    if data.get("blockers"):
        print("blockers:")
        for blocker in data["blockers"]:
            print(f"  - {blocker}")
    if data.get("warnings"):
        print("warnings:")
        for warning in data["warnings"]:
            print(f"  - {warning}")


def cmd_validate(args: argparse.Namespace) -> int:
    manifest = load_json(args.manifest)
    result = validate_manifest(manifest).to_dict()
    emit(result, args.json)
    return 0 if result["passed"] else 1


def cmd_gate(args: argparse.Namespace) -> int:
    manifest = load_json(args.manifest)
    result = evaluate_gate(manifest, operation=args.operation).to_dict()
    emit(result, args.json)
    return 0 if result["passed"] else 2


def cmd_run(args: argparse.Namespace) -> int:
    job = load_job(args.job)
    report = build_run_report(job)
    if args.out:
        write_report(report, args.out)
        report["report_path"] = str(Path(args.out))
    emit(report, args.json)
    return 0 if report["passed"] else 3


def cmd_handoff(args: argparse.Namespace) -> int:
    report = load_report(args.report)
    markdown = render_handoff(report)
    if args.out:
        write_handoff(markdown, args.out)
        data = {"status": "handoff_written", "path": str(Path(args.out)), "passed": True}
        emit(data, args.json)
    else:
        print(markdown)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cmsk",
        description="Fail-closed maintainer workflow checks for AI-assisted OSS work.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate an approval manifest.")
    validate.add_argument("--manifest", required=True, help="Path to approval manifest JSON.")
    validate.add_argument("--json", action="store_true", help="Emit JSON output.")
    validate.set_defaults(func=cmd_validate)

    gate = subparsers.add_parser("gate", help="Evaluate the fail-closed approval gate.")
    gate.add_argument("--manifest", required=True, help="Path to approval manifest JSON.")
    gate.add_argument("--operation", default=None, help="Optional operation expected by caller.")
    gate.add_argument("--json", action="store_true", help="Emit JSON output.")
    gate.set_defaults(func=cmd_gate)

    run = subparsers.add_parser("run", help="Build a report-only maintainer job plan.")
    run.add_argument("--job", required=True, help="Path to job JSON.")
    run.add_argument("--out", default=None, help="Optional report JSON output path.")
    run.add_argument("--json", action="store_true", help="Emit JSON output.")
    run.set_defaults(func=cmd_run)

    handoff = subparsers.add_parser("handoff", help="Render a maintainer handoff from a run report.")
    handoff.add_argument("--report", required=True, help="Path to report JSON.")
    handoff.add_argument("--out", default=None, help="Optional Markdown output path.")
    handoff.add_argument("--json", action="store_true", help="Emit JSON output when writing a file.")
    handoff.set_defaults(func=cmd_handoff)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 99
