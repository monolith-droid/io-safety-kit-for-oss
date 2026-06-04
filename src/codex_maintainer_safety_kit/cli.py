from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .approval import evaluate_gate, load_json, validate_manifest
from .handoff import load_report, render_handoff, write_handoff
from .issue_triage import render_issue_triage, write_issue_triage
from .pr_review import render_pr_review, write_pr_review
from .promotion import (
    evaluate_promotion_candidate,
    load_candidate,
    render_promotion_report,
    write_promotion_report,
)
from .runner import build_run_report, load_job, write_report
from .signature import check_signature_metadata
from .trust_policy import evaluate_trust_policy


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
    result = validate_manifest(manifest, use_schema=args.schema).to_dict()
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


def cmd_pr_review(args: argparse.Namespace) -> int:
    manifest = load_json(args.manifest)
    gate = evaluate_gate(manifest, operation="pr_review")
    markdown = render_pr_review(manifest)
    if args.out:
        write_pr_review(markdown, args.out)
        data = {
            "status": "pr_review_report_written",
            "path": str(Path(args.out)),
            "passed": gate.passed,
            "github_mutation_performed": False,
        }
        emit(data, args.json)
    else:
        print(markdown)
    return 0 if gate.passed else 2


def cmd_issue_triage(args: argparse.Namespace) -> int:
    manifest = load_json(args.manifest)
    gate = evaluate_gate(manifest, operation="issue_triage")
    markdown = render_issue_triage(manifest)
    if args.out:
        write_issue_triage(markdown, args.out)
        data = {
            "status": "issue_triage_report_written",
            "path": str(Path(args.out)),
            "passed": gate.passed,
            "github_mutation_performed": False,
            "labels_mutated": False,
            "comments_posted": False,
        }
        emit(data, args.json)
    else:
        print(markdown)
    return 0 if gate.passed else 2


def cmd_promotion_check(args: argparse.Namespace) -> int:
    candidate = load_candidate(args.candidate)
    result = evaluate_promotion_candidate(candidate)
    markdown = render_promotion_report(candidate)
    if args.out:
        write_promotion_report(markdown, args.out)
        data = result.to_dict()
        data["path"] = str(Path(args.out))
        emit(data, args.json)
    elif args.json:
        emit(result.to_dict(), True)
    else:
        print(markdown)
    return 0 if result.passed else 2


def cmd_signature_check(args: argparse.Namespace) -> int:
    manifest = load_json(args.manifest)
    result = check_signature_metadata(manifest).to_dict()
    emit(result, args.json)
    return 0 if result["passed"] else 2


def cmd_trust_policy_check(args: argparse.Namespace) -> int:
    manifest = load_json(args.manifest)
    policy = load_json(args.policy)
    result = evaluate_trust_policy(manifest, policy).to_dict()
    emit(result, args.json)
    return 0 if result["passed"] else 2


def _program_name() -> str:
    stem = Path(sys.argv[0]).stem
    if stem == "__main__":
        return "python -m io_safety_kit"
    return stem or "iosk"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=_program_name(),
        description="Fail-closed maintainer workflow checks for AI-assisted OSS work.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate an approval manifest.")
    validate.add_argument("--manifest", required=True, help="Path to approval manifest JSON.")
    validate.add_argument(
        "--schema",
        action="store_true",
        help="Also run optional JSON Schema validation when jsonschema is installed.",
    )
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
    handoff.add_argument(
        "--json", action="store_true", help="Emit JSON output when writing a file."
    )
    handoff.set_defaults(func=cmd_handoff)

    pr_review = subparsers.add_parser(
        "pr-review", help="Render a report-only PR review Markdown report."
    )
    pr_review.add_argument(
        "--manifest", required=True, help="Path to PR review manifest JSON."
    )
    pr_review.add_argument("--out", default=None, help="Optional Markdown output path.")
    pr_review.add_argument(
        "--json", action="store_true", help="Emit JSON output when writing a file."
    )
    pr_review.set_defaults(func=cmd_pr_review)

    issue_triage = subparsers.add_parser(
        "issue-triage", help="Render a report-only issue triage Markdown report."
    )
    issue_triage.add_argument(
        "--manifest", required=True, help="Path to issue triage manifest JSON."
    )
    issue_triage.add_argument("--out", default=None, help="Optional Markdown output path.")
    issue_triage.add_argument(
        "--json", action="store_true", help="Emit JSON output when writing a file."
    )
    issue_triage.set_defaults(func=cmd_issue_triage)

    promotion = subparsers.add_parser(
        "promotion-check",
        help="Evaluate whether private/downstream output is safe to promote publicly.",
    )
    promotion.add_argument(
        "--candidate", required=True, help="Path to promotion candidate JSON."
    )
    promotion.add_argument("--out", default=None, help="Optional Markdown output path.")
    promotion.add_argument(
        "--json", action="store_true", help="Emit JSON output instead of Markdown."
    )
    promotion.set_defaults(func=cmd_promotion_check)

    signature = subparsers.add_parser(
        "signature-check",
        help="Check signed approval manifest digest metadata.",
    )
    signature.add_argument(
        "--manifest", required=True, help="Path to signed approval manifest JSON."
    )
    signature.add_argument("--json", action="store_true", help="Emit JSON output.")
    signature.set_defaults(func=cmd_signature_check)

    trust_policy = subparsers.add_parser(
        "trust-policy-check",
        help="Check signed manifest metadata against a trust policy.",
    )
    trust_policy.add_argument(
        "--manifest", required=True, help="Path to signed approval manifest JSON."
    )
    trust_policy.add_argument(
        "--policy", required=True, help="Path to trust policy JSON."
    )
    trust_policy.add_argument("--json", action="store_true", help="Emit JSON output.")
    trust_policy.set_defaults(func=cmd_trust_policy_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 99
