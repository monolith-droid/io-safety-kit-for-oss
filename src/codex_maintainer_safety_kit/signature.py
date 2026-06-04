from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from .approval import validate_manifest


SIGNED_MANIFEST_FIELDS = (
    "schema_version",
    "operation",
    "repository",
    "requested_by",
    "reason",
    "risk_level",
    "allowed_actions",
    "targets",
    "command",
    "approval",
)

SUPPORTED_SIGNATURE_TYPES = {"detached", "inline"}
SUPPORTED_SIGNATURE_ALGORITHMS = {"sha256-canonical-json-v1"}


@dataclass
class SignatureCheckResult:
    passed: bool
    status: str
    blockers: list[str]
    warnings: list[str]
    manifest: dict[str, Any]
    computed_payload_digest: str
    recorded_payload_digest: str | None

    def to_dict(self) -> dict[str, Any]:
        signature = self.manifest.get("signature")
        if not isinstance(signature, dict):
            signature = {}

        return {
            "passed": self.passed,
            "status": self.status,
            "blockers": self.blockers,
            "warnings": self.warnings,
            "operation": self.manifest.get("operation"),
            "repository": self.manifest.get("repository"),
            "risk_level": self.manifest.get("risk_level"),
            "signature_type": signature.get("type"),
            "signature_identity": signature.get("identity"),
            "signature_algorithm": signature.get("algorithm"),
            "computed_payload_digest": self.computed_payload_digest,
            "recorded_payload_digest": self.recorded_payload_digest,
            "cryptographic_signature_verified": False,
        }


def canonical_manifest_payload(manifest: dict[str, Any]) -> str:
    payload = {
        field: manifest[field]
        for field in SIGNED_MANIFEST_FIELDS
        if field in manifest
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_manifest_payload_digest(manifest: dict[str, Any]) -> str:
    payload = canonical_manifest_payload(manifest).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return f"sha256:{digest}"


def _is_safe_relative_path(value: str) -> bool:
    if not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts


def check_signature_metadata(manifest: dict[str, Any]) -> SignatureCheckResult:
    validation = validate_manifest(manifest)
    blockers = list(validation.blockers)
    warnings = list(validation.warnings)

    computed_digest = compute_manifest_payload_digest(manifest)
    recorded_digest: str | None = None

    signature = manifest.get("signature")
    if not isinstance(signature, dict):
        blockers.append("signature_missing")
        signature = {}

    for field in ("type", "algorithm", "identity", "key_id", "payload_digest"):
        if not signature.get(field):
            blockers.append(f"signature_missing:{field}")

    signature_type = signature.get("type")
    if signature_type and signature_type not in SUPPORTED_SIGNATURE_TYPES:
        blockers.append(f"signature_unsupported_type:{signature_type}")

    algorithm = signature.get("algorithm")
    if algorithm and algorithm not in SUPPORTED_SIGNATURE_ALGORITHMS:
        blockers.append(f"signature_unsupported_algorithm:{algorithm}")

    recorded_digest_value = signature.get("payload_digest")
    if isinstance(recorded_digest_value, str):
        recorded_digest = recorded_digest_value
        if not recorded_digest.startswith("sha256:"):
            blockers.append("signature_payload_digest_must_be_sha256")
        elif recorded_digest != computed_digest:
            blockers.append("signature_payload_digest_mismatch")

    if signature_type == "detached":
        signature_path = signature.get("signature_path")
        if not isinstance(signature_path, str) or not signature_path:
            blockers.append("signature_missing:signature_path")
        elif not _is_safe_relative_path(signature_path):
            blockers.append("signature_path_must_be_safe_relative_path")
    elif signature_type == "inline" and not signature.get("signature"):
        blockers.append("signature_missing:signature")

    warnings.append("signature_provider_verification_not_implemented")
    warnings.append("signature_check_verifies_public_digest_metadata_only")

    passed = not blockers
    status = "signature_digest_verified" if passed else "signature_check_failed"
    return SignatureCheckResult(
        passed=passed,
        status=status,
        blockers=blockers,
        warnings=warnings,
        manifest=manifest,
        computed_payload_digest=computed_digest,
        recorded_payload_digest=recorded_digest,
    )
