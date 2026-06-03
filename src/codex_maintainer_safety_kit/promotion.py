from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "schema_version",
    "candidate_id",
    "source",
    "summary",
    "public_value",
    "output_artifacts",
    "privacy_review",
    "generalization",
    "promotion_plan",
}

FORBIDDEN_SOURCE_MARKERS = {
    "secret",
    "token",
    "password",
    "private transcript",
    "local absolute path",
    "personal identity",
    "approval id",
    "service credential",
}

PUBLIC_ARTIFACT_TYPES = {
    "doc",
    "example",
    "fixture",
    "schema",
    "test",
    "issue",
    "pull_request",
    "release_note",
}


def _dict_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


@dataclass
class PromotionResult:
    passed: bool
    status: str
    blockers: list[str]
    warnings: list[str]
    candidate: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        source = _dict_value(self.candidate.get("source"))
        plan = _dict_value(self.candidate.get("promotion_plan"))
        return {
            "passed": self.passed,
            "status": self.status,
            "blockers": self.blockers,
            "warnings": self.warnings,
            "candidate_id": self.candidate.get("candidate_id"),
            "source_kind": source.get("kind"),
            "promotion_target": plan.get("target"),
            "public_issue_required": True,
            "external_publish_performed": False,
        }


def load_candidate(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def _truthy(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _list_values(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def evaluate_promotion_candidate(candidate: dict[str, Any]) -> PromotionResult:
    blockers: list[str] = []
    warnings: list[str] = []

    missing = sorted(REQUIRED_FIELDS - set(candidate))
    blockers.extend(f"missing_field:{field}" for field in missing)

    source = _dict_value(candidate.get("source"))
    if source.get("kind") not in {"private_downstream", "local_workflow", "public_repo"}:
        blockers.append(f"unsupported_source_kind:{source.get('kind')}")
    if not source.get("description"):
        blockers.append("source_description_required")

    privacy = _dict_value(candidate.get("privacy_review"))
    for field in (
        "secrets_removed",
        "personal_data_removed",
        "local_paths_removed",
        "private_context_removed",
        "synthetic_example_used",
    ):
        if not _truthy(privacy.get(field)):
            blockers.append(f"privacy_review_failed:{field}")

    source_markers = {
        str(item).lower() for item in _list_values(privacy.get("source_markers"))
    }
    for marker in sorted(source_markers & FORBIDDEN_SOURCE_MARKERS):
        blockers.append(f"forbidden_source_marker:{marker}")

    generalization = _dict_value(candidate.get("generalization"))
    if not _truthy(generalization.get("useful_to_other_maintainers")):
        blockers.append("not_useful_to_other_maintainers")
    if not _truthy(generalization.get("private_names_removed")):
        blockers.append("private_names_not_removed")
    if not _truthy(generalization.get("can_be_tested_in_ci")):
        warnings.append("not_tested_in_ci_yet")
    if not generalization.get("public_problem_statement"):
        blockers.append("public_problem_statement_required")

    artifacts = _list_values(candidate.get("output_artifacts"))
    if not artifacts:
        blockers.append("output_artifacts_required")
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            blockers.append(f"artifact_not_object:{index}")
            continue
        artifact_type = artifact.get("type")
        if artifact_type not in PUBLIC_ARTIFACT_TYPES:
            blockers.append(f"unsupported_artifact_type:{artifact_type}")
        if not artifact.get("path"):
            blockers.append(f"artifact_missing_path:{index}")

    plan = _dict_value(candidate.get("promotion_plan"))
    if plan.get("target") not in {"issue", "pull_request", "release"}:
        blockers.append(f"unsupported_promotion_target:{plan.get('target')}")
    if not plan.get("maintainer_review"):
        blockers.append("maintainer_review_required")
    if _truthy(plan.get("external_publish")):
        blockers.append("external_publish_not_supported")

    passed = not blockers
    return PromotionResult(
        passed=passed,
        status="promotion_candidate_ready" if passed else "promotion_candidate_blocked",
        blockers=blockers,
        warnings=warnings,
        candidate=candidate,
    )


def render_promotion_report(candidate: dict[str, Any]) -> str:
    result = evaluate_promotion_candidate(candidate)
    artifacts = _list_values(candidate.get("output_artifacts"))
    source = _dict_value(candidate.get("source"))
    plan = _dict_value(candidate.get("promotion_plan"))

    lines = [
        "# Safe Output Promotion Report",
        "",
        f"- Candidate: `{candidate.get('candidate_id', '')}`",
        f"- Status: `{result.status}`",
        f"- Source kind: `{source.get('kind', '')}`",
        f"- Promotion target: `{plan.get('target', '')}`",
        "- Mode: `report_only`",
        "- External publish performed: `False`",
        "",
        "## Summary",
        "",
        candidate.get("summary", ""),
        "",
        "## Public Value",
        "",
        candidate.get("public_value", ""),
        "",
        "## Output Artifacts",
        "",
    ]

    if artifacts:
        for artifact in artifacts:
            if isinstance(artifact, dict):
                lines.append(
                    f"- `{artifact.get('type', '')}`: {artifact.get('path', '')}"
                )
    else:
        lines.append("- None")

    lines.extend(["", "## Blockers", ""])
    if result.blockers:
        lines.extend(f"- `{blocker}`" for blocker in result.blockers)
    else:
        lines.append("- None")

    lines.extend(["", "## Warnings", ""])
    if result.warnings:
        lines.extend(f"- `{warning}`" for warning in result.warnings)
    else:
        lines.append("- None")

    lines.extend(["", "## Maintainer Next Steps", ""])
    if result.passed:
        lines.extend(
            [
                "- Open or link a public issue before implementation.",
                "- Keep examples synthetic and privacy-safe.",
                "- Add tests or docs before release promotion.",
            ]
        )
    else:
        lines.extend(
            [
                "- Resolve blockers before publishing this output.",
                "- Replace private context with synthetic examples.",
                "- Re-run the promotion check before opening a public PR.",
            ]
        )

    lines.append("")
    return "\n".join(lines)


def write_promotion_report(markdown: str, output: str | Path) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(markdown)
    return output
