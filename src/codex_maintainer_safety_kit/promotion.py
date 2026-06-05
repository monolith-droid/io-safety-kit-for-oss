from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any


SCHEMA_RESOURCE = "schemas/promotion-candidate.schema.json"

REQUIRED_FIELDS = {
    "schema_version",
    "candidate_id",
    "source",
    "summary",
    "public_value",
    "output_artifacts",
    "privacy_review",
    "generalization",
    "review_evidence",
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

EVIDENCE_BUNDLE_ITEM_KINDS = {
    "check",
    "ci_run",
    "doc",
    "example",
    "issue",
    "pull_request",
    "release",
    "schema",
    "test",
}

EVIDENCE_BUNDLE_REFERENCE_TYPES = {
    "ci_run",
    "issue",
    "path",
    "pull_request",
    "release",
    "url",
}


def _dict_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


@dataclass
class ReviewEvidenceSummary:
    status: str
    reviewed_by_role: str | None
    check_count: int
    passed_check_count: int
    check_ids: list[str]
    failed_check_ids: list[str]
    missing_evidence_check_ids: list[str]
    missing_id_check_indices: list[int]
    malformed_check_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "ready_for_public_review": self.status == "review_evidence_ready",
            "reviewed_by_role": self.reviewed_by_role,
            "check_count": self.check_count,
            "passed_check_count": self.passed_check_count,
            "check_ids": self.check_ids,
            "failed_check_ids": self.failed_check_ids,
            "missing_evidence_check_ids": self.missing_evidence_check_ids,
            "missing_id_check_indices": self.missing_id_check_indices,
            "malformed_check_count": self.malformed_check_count,
        }


@dataclass
class EvidenceBundleSummary:
    status: str
    bundle_id: str | None
    item_count: int
    reference_count: int
    item_ids: list[str]
    missing_reference_item_ids: list[str]
    invalid_reference_targets: list[str]
    malformed_item_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "present": self.status != "evidence_bundle_not_provided",
            "ready_for_public_review": self.status == "evidence_bundle_ready",
            "bundle_id": self.bundle_id,
            "item_count": self.item_count,
            "reference_count": self.reference_count,
            "item_ids": self.item_ids,
            "missing_reference_item_ids": self.missing_reference_item_ids,
            "invalid_reference_targets": self.invalid_reference_targets,
            "malformed_item_count": self.malformed_item_count,
        }


@dataclass
class PromotionResult:
    passed: bool
    status: str
    blockers: list[str]
    warnings: list[str]
    candidate: dict[str, Any]
    schema_validation: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        source = _dict_value(self.candidate.get("source"))
        plan = _dict_value(self.candidate.get("promotion_plan"))
        data = {
            "passed": self.passed,
            "status": self.status,
            "blockers": self.blockers,
            "warnings": self.warnings,
            "candidate_id": self.candidate.get("candidate_id"),
            "source_kind": source.get("kind"),
            "promotion_target": plan.get("target"),
            "public_issue_required": True,
            "external_publish_performed": False,
            "review_evidence": summarize_review_evidence(self.candidate).to_dict(),
        }
        bundle_summary = summarize_evidence_bundle(self.candidate)
        if bundle_summary.status != "evidence_bundle_not_provided":
            data["evidence_bundle"] = bundle_summary.to_dict()
        if self.schema_validation is not None:
            data["schema_validation"] = self.schema_validation
        return data


def load_candidate(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def load_promotion_candidate_schema() -> dict[str, Any]:
    schema_path = resources.files(__package__).joinpath(SCHEMA_RESOURCE)
    data = json.loads(schema_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in packaged schema {SCHEMA_RESOURCE}")
    return data


def _load_jsonschema_validator() -> Any | None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return None
    return Draft202012Validator


def _schema_path(parts: Any) -> str:
    path = ".".join(str(part) for part in parts)
    return path or "<root>"


def _truthy(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _list_values(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _looks_private_reference(target: str) -> bool:
    lowered = target.lower()
    if lowered.startswith("file:") or target.startswith("/"):
        return True
    if len(target) > 2 and target[1] == ":" and target[2] in {"\\", "/"}:
        return True
    if "\\" in target:
        return True
    return any(marker in lowered for marker in FORBIDDEN_SOURCE_MARKERS)


def summarize_review_evidence(candidate: dict[str, Any]) -> ReviewEvidenceSummary:
    evidence = _dict_value(candidate.get("review_evidence"))
    reviewed_by_role = evidence.get("reviewed_by_role")
    reviewed_by_role_text = str(reviewed_by_role) if reviewed_by_role else None
    checks = _list_values(evidence.get("checks"))

    check_ids: list[str] = []
    failed_check_ids: list[str] = []
    missing_evidence_check_ids: list[str] = []
    missing_id_check_indices: list[int] = []
    passed_check_count = 0
    malformed_check_count = 0

    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            malformed_check_count += 1
            continue

        check_id_value = check.get("id")
        check_id = str(check_id_value) if check_id_value else ""
        if check_id:
            check_ids.append(check_id)
        else:
            missing_id_check_indices.append(index)
            check_id = f"missing:{index}"

        if check.get("status") == "passed":
            passed_check_count += 1
        else:
            failed_check_ids.append(check_id)

        if not check.get("evidence"):
            missing_evidence_check_ids.append(check_id)

    ready = (
        bool(evidence)
        and bool(reviewed_by_role_text)
        and bool(checks)
        and malformed_check_count == 0
        and not failed_check_ids
        and not missing_evidence_check_ids
        and not missing_id_check_indices
    )

    return ReviewEvidenceSummary(
        status="review_evidence_ready" if ready else "review_evidence_blocked",
        reviewed_by_role=reviewed_by_role_text,
        check_count=len(checks),
        passed_check_count=passed_check_count,
        check_ids=check_ids,
        failed_check_ids=failed_check_ids,
        missing_evidence_check_ids=missing_evidence_check_ids,
        missing_id_check_indices=missing_id_check_indices,
        malformed_check_count=malformed_check_count,
    )


def summarize_evidence_bundle(candidate: dict[str, Any]) -> EvidenceBundleSummary:
    if "evidence_bundle" not in candidate:
        return EvidenceBundleSummary(
            status="evidence_bundle_not_provided",
            bundle_id=None,
            item_count=0,
            reference_count=0,
            item_ids=[],
            missing_reference_item_ids=[],
            invalid_reference_targets=[],
            malformed_item_count=0,
        )

    bundle = _dict_value(candidate.get("evidence_bundle"))
    items = _list_values(bundle.get("items"))
    item_ids: list[str] = []
    missing_reference_item_ids: list[str] = []
    invalid_reference_targets: list[str] = []
    reference_count = 0
    malformed_item_count = 0

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            malformed_item_count += 1
            continue

        item_id_value = item.get("id")
        item_id = str(item_id_value) if item_id_value else f"missing:{index}"
        if item_id_value:
            item_ids.append(item_id)

        references = _list_values(item.get("references"))
        if not references:
            missing_reference_item_ids.append(item_id)
            continue

        for reference_index, reference in enumerate(references):
            if not isinstance(reference, dict):
                malformed_item_count += 1
                continue
            target = reference.get("target")
            if not target:
                invalid_reference_targets.append(f"{item_id}:missing:{reference_index}")
                continue
            target_text = str(target)
            reference_count += 1
            if _looks_private_reference(target_text):
                invalid_reference_targets.append(target_text)

    ready = (
        bool(bundle)
        and _truthy(bundle.get("public_safe"))
        and bool(bundle.get("bundle_id"))
        and bool(items)
        and malformed_item_count == 0
        and not missing_reference_item_ids
        and not invalid_reference_targets
    )

    return EvidenceBundleSummary(
        status="evidence_bundle_ready" if ready else "evidence_bundle_blocked",
        bundle_id=str(bundle.get("bundle_id")) if bundle.get("bundle_id") else None,
        item_count=len(items),
        reference_count=reference_count,
        item_ids=item_ids,
        missing_reference_item_ids=missing_reference_item_ids,
        invalid_reference_targets=invalid_reference_targets,
        malformed_item_count=malformed_item_count,
    )


def evaluate_promotion_candidate(
    candidate: dict[str, Any], *, use_schema: bool = False
) -> PromotionResult:
    blockers: list[str] = []
    warnings: list[str] = []
    schema_validation: dict[str, Any] | None = None

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

    evidence = _dict_value(candidate.get("review_evidence"))
    if not evidence:
        blockers.append("review_evidence_required")
    if not evidence.get("reviewed_by_role"):
        blockers.append("review_evidence_reviewed_by_role_required")

    evidence_checks = _list_values(evidence.get("checks"))
    if not evidence_checks:
        blockers.append("review_evidence_checks_required")
    for index, check in enumerate(evidence_checks):
        if not isinstance(check, dict):
            blockers.append(f"review_evidence_check_not_object:{index}")
            continue
        check_id = check.get("id")
        if not check_id:
            blockers.append(f"review_evidence_check_missing_id:{index}")
        status = check.get("status")
        if status != "passed":
            blockers.append(f"review_evidence_check_not_passed:{check_id}")
        if not check.get("evidence"):
            blockers.append(f"review_evidence_check_missing_evidence:{check_id}")

    plan = _dict_value(candidate.get("promotion_plan"))
    if plan.get("target") not in {"issue", "pull_request", "release"}:
        blockers.append(f"unsupported_promotion_target:{plan.get('target')}")
    if not plan.get("maintainer_review"):
        blockers.append("maintainer_review_required")
    if _truthy(plan.get("external_publish")):
        blockers.append("external_publish_not_supported")

    if "evidence_bundle" in candidate:
        bundle = _dict_value(candidate.get("evidence_bundle"))
        bundle_summary = summarize_evidence_bundle(candidate)
        if not bundle:
            blockers.append("evidence_bundle_must_be_object")
        if not _truthy(bundle.get("public_safe")):
            blockers.append("evidence_bundle_not_public_safe")
        if not bundle.get("bundle_id"):
            blockers.append("evidence_bundle_id_required")

        bundle_items = _list_values(bundle.get("items"))
        if not bundle_items:
            blockers.append("evidence_bundle_items_required")
        for index, item in enumerate(bundle_items):
            if not isinstance(item, dict):
                blockers.append(f"evidence_bundle_item_not_object:{index}")
                continue
            item_id = item.get("id")
            if not item_id:
                blockers.append(f"evidence_bundle_item_missing_id:{index}")
            if item.get("kind") not in EVIDENCE_BUNDLE_ITEM_KINDS:
                blockers.append(f"unsupported_evidence_bundle_item_kind:{item.get('kind')}")
            if not item.get("summary"):
                blockers.append(f"evidence_bundle_item_missing_summary:{item_id}")
            references = _list_values(item.get("references"))
            if not references:
                blockers.append(f"evidence_bundle_item_references_required:{item_id}")
            for reference_index, reference in enumerate(references):
                if not isinstance(reference, dict):
                    blockers.append(
                        f"evidence_bundle_reference_not_object:{item_id}:{reference_index}"
                    )
                    continue
                reference_type = reference.get("type")
                target = reference.get("target")
                if reference_type not in EVIDENCE_BUNDLE_REFERENCE_TYPES:
                    blockers.append(
                        f"unsupported_evidence_bundle_reference_type:{reference_type}"
                    )
                if not target:
                    blockers.append(
                        f"evidence_bundle_reference_missing_target:{item_id}:{reference_index}"
                    )
                elif _looks_private_reference(str(target)):
                    blockers.append(f"private_evidence_bundle_reference:{target}")

        if bundle_summary.status != "evidence_bundle_ready":
            blockers.append(bundle_summary.status)

    if use_schema:
        schema_validation = {
            "requested": True,
            "available": False,
            "schema": SCHEMA_RESOURCE,
            "status": "schema_validation_skipped",
            "errors": [],
        }
        validator_class = _load_jsonschema_validator()
        if validator_class is None:
            warnings.append("jsonschema_not_installed_schema_validation_skipped")
        else:
            try:
                schema = load_promotion_candidate_schema()
                validator_class.check_schema(schema)
                validator = validator_class(schema)
                errors = sorted(
                    validator.iter_errors(candidate),
                    key=lambda error: (
                        [str(part) for part in error.absolute_path],
                        error.message,
                    ),
                )
            except Exception as exc:
                blockers.append(
                    f"schema_validation_unavailable:{type(exc).__name__}:{exc}"
                )
            else:
                schema_validation["available"] = True
                schema_validation["status"] = (
                    "schema_valid" if not errors else "schema_invalid"
                )
                for error in errors:
                    path = _schema_path(error.absolute_path)
                    message = str(error.message)
                    schema_validation["errors"].append(
                        {
                            "path": path,
                            "message": message,
                            "validator": str(error.validator),
                        }
                    )
                    blockers.append(f"schema_error:{path}:{message}")

    passed = not blockers
    return PromotionResult(
        passed=passed,
        status="promotion_candidate_ready" if passed else "promotion_candidate_blocked",
        blockers=blockers,
        warnings=warnings,
        candidate=candidate,
        schema_validation=schema_validation,
    )


def render_promotion_report(candidate: dict[str, Any]) -> str:
    result = evaluate_promotion_candidate(candidate)
    artifacts = _list_values(candidate.get("output_artifacts"))
    source = _dict_value(candidate.get("source"))
    plan = _dict_value(candidate.get("promotion_plan"))
    evidence = _dict_value(candidate.get("review_evidence"))
    evidence_summary = summarize_review_evidence(candidate)
    evidence_checks = _list_values(evidence.get("checks"))
    bundle_summary = summarize_evidence_bundle(candidate)
    evidence_bundle = _dict_value(candidate.get("evidence_bundle"))
    bundle_items = _list_values(evidence_bundle.get("items"))

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

    lines.extend(["", "## Review Evidence", ""])
    lines.append(f"- Evidence status: `{evidence_summary.status}`")
    lines.append(
        "- Evidence checks passed: "
        f"`{evidence_summary.passed_check_count}/{evidence_summary.check_count}`"
    )
    lines.append(f"- Reviewed by role: `{evidence.get('reviewed_by_role', '')}`")
    if evidence_summary.failed_check_ids:
        failed = ", ".join(f"`{check_id}`" for check_id in evidence_summary.failed_check_ids)
        lines.append(f"- Failed checks: {failed}")
    if evidence_summary.missing_evidence_check_ids:
        missing = ", ".join(
            f"`{check_id}`" for check_id in evidence_summary.missing_evidence_check_ids
        )
        lines.append(f"- Missing evidence notes: {missing}")
    if evidence_summary.malformed_check_count:
        lines.append(
            f"- Malformed evidence checks: `{evidence_summary.malformed_check_count}`"
        )
    if evidence_checks:
        for check in evidence_checks:
            if isinstance(check, dict):
                check_id = check.get("id", "")
                status = check.get("status", "")
                evidence_note = check.get("evidence", "")
                lines.append(
                    f"- `{check_id}`: `{status}` - {evidence_note}"
                )
    else:
        lines.append("- None")

    if bundle_summary.status != "evidence_bundle_not_provided":
        lines.extend(["", "## Evidence Bundle", ""])
        lines.append(f"- Bundle status: `{bundle_summary.status}`")
        lines.append(f"- Bundle id: `{bundle_summary.bundle_id or ''}`")
        lines.append(f"- Bundle items: `{bundle_summary.item_count}`")
        lines.append(f"- Public references: `{bundle_summary.reference_count}`")
        if bundle_summary.invalid_reference_targets:
            invalid = ", ".join(
                f"`{target}`" for target in bundle_summary.invalid_reference_targets
            )
            lines.append(f"- Invalid references: {invalid}")
        if bundle_items:
            for item in bundle_items:
                if isinstance(item, dict):
                    lines.append(
                        f"- `{item.get('id', '')}`: `{item.get('kind', '')}` - "
                        f"{item.get('summary', '')}"
                    )

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
