from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Any


SCHEMA_RESOURCE = "schemas/approval-manifest.schema.json"

SUPPORTED_OPERATIONS = {
    "pr_review",
    "issue_triage",
    "release_checklist",
    "security_audit",
    "dependency_audit",
    "maintainer_handoff",
    "ci_failure_analysis",
}

RISK_LEVELS = {"low", "medium", "high"}

BLOCKED_ACTION_KEYWORDS = {
    "delete_repo",
    "change_visibility",
    "force_push",
    "merge_without_review",
    "read_secret",
    "exfiltrate",
    "external_publish",
    "disable_branch_protection",
    "edit_github_secrets",
    "destructive_cleanup",
}

REQUIRED_FIELDS = {
    "schema_version",
    "operation",
    "repository",
    "requested_by",
    "reason",
    "risk_level",
    "allowed_actions",
    "targets",
    "approval",
}


@dataclass
class CheckResult:
    passed: bool
    status: str
    blockers: list[str]
    warnings: list[str]
    manifest: dict[str, Any]
    schema_validation: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = {
            "passed": self.passed,
            "status": self.status,
            "blockers": self.blockers,
            "warnings": self.warnings,
            "operation": self.manifest.get("operation"),
            "repository": self.manifest.get("repository"),
            "risk_level": self.manifest.get("risk_level"),
            "approval_status": self.manifest.get("approval", {}).get("status"),
        }
        if self.schema_validation is not None:
            data["schema_validation"] = self.schema_validation
        return data


def load_json(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def load_approval_manifest_schema() -> dict[str, Any]:
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


def _parse_datetime(value: str) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def validate_manifest(
    manifest: dict[str, Any], *, use_schema: bool = False
) -> CheckResult:
    blockers: list[str] = []
    warnings: list[str] = []
    schema_validation: dict[str, Any] | None = None

    missing = sorted(REQUIRED_FIELDS - set(manifest))
    blockers.extend(f"missing_field:{field}" for field in missing)

    operation = manifest.get("operation")
    if operation not in SUPPORTED_OPERATIONS:
        blockers.append(f"unsupported_operation:{operation}")

    risk_level = manifest.get("risk_level")
    if risk_level not in RISK_LEVELS:
        blockers.append(f"unsupported_risk_level:{risk_level}")

    actions = manifest.get("allowed_actions")
    if not isinstance(actions, list) or not actions:
        blockers.append("allowed_actions_must_be_non_empty_list")
        actions = []

    for action in actions:
        action_text = str(action).lower()
        for keyword in BLOCKED_ACTION_KEYWORDS:
            if keyword in action_text:
                blockers.append(f"blocked_action:{action}")

    targets = manifest.get("targets")
    if not isinstance(targets, list) or not targets:
        blockers.append("targets_must_be_non_empty_list")
    else:
        for index, target in enumerate(targets):
            if not isinstance(target, dict):
                blockers.append(f"target_not_object:{index}")
                continue
            if not target.get("type"):
                blockers.append(f"target_missing_type:{index}")
            if not (target.get("path") or target.get("url") or target.get("ref")):
                blockers.append(f"target_missing_locator:{index}")

    approval = manifest.get("approval")
    if not isinstance(approval, dict):
        blockers.append("approval_must_be_object")
        approval = {}

    approval_status = approval.get("status")
    if approval_status not in {"pending", "approved", "rejected"}:
        blockers.append(f"unsupported_approval_status:{approval_status}")

    if approval_status == "approved":
        for field in ("approval_id", "approved_by", "approved_at", "expires_at"):
            if not approval.get(field):
                blockers.append(f"approved_manifest_missing:{field}")
        approved_at = _parse_datetime(str(approval.get("approved_at", "")))
        expires_at = _parse_datetime(str(approval.get("expires_at", "")))
        if approved_at is None:
            blockers.append("invalid_approved_at")
        if expires_at is None:
            blockers.append("invalid_expires_at")
        elif expires_at <= datetime.now(timezone.utc):
            blockers.append("approval_expired")
    elif approval_status == "pending":
        warnings.append("approval_pending_gate_will_block")
    elif approval_status == "rejected":
        warnings.append("approval_rejected_gate_will_block")

    command = manifest.get("command")
    if command:
        if not isinstance(command, dict):
            blockers.append("command_must_be_object")
        elif command.get("execute") is True:
            blockers.append("command_execution_not_supported_in_mvp")

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
                schema = load_approval_manifest_schema()
                validator_class.check_schema(schema)
                validator = validator_class(schema)
                errors = sorted(
                    validator.iter_errors(manifest),
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
    status = "manifest_valid" if passed else "manifest_invalid"
    return CheckResult(passed, status, blockers, warnings, manifest, schema_validation)


def evaluate_gate(manifest: dict[str, Any], operation: str | None = None) -> CheckResult:
    validation = validate_manifest(manifest)
    blockers = list(validation.blockers)
    warnings = list(validation.warnings)

    requested_operation = operation or manifest.get("operation")
    if requested_operation != manifest.get("operation"):
        blockers.append(
            f"operation_mismatch:requested={requested_operation}:manifest={manifest.get('operation')}"
        )

    approval = manifest.get("approval", {})
    if approval.get("status") != "approved":
        blockers.append(f"approval_not_approved:{approval.get('status')}")

    if manifest.get("risk_level") == "high":
        warnings.append("high_risk_operation_requires_extra_maintainer_review")

    passed = not blockers
    status = "gate_allowed_report_only" if passed else "gate_blocked_fail_closed"
    return CheckResult(passed, status, blockers, warnings, manifest)
