from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .signature import check_signature_metadata


TRUST_POLICY_SCHEMA_VERSION = "iosk.trust-policy.v1"
REQUIRED_POLICY_FIELDS = {
    "schema_version",
    "policy_id",
    "repository",
    "trusted_identities",
}
REQUIRED_IDENTITY_FIELDS = {
    "identity",
    "key_id",
    "allowed_operations",
    "max_risk_level",
}
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


@dataclass
class TrustPolicyCheckResult:
    passed: bool
    status: str
    blockers: list[str]
    warnings: list[str]
    manifest: dict[str, Any]
    policy: dict[str, Any]
    signature_digest_verified: bool
    trusted_identity_matched: bool

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
            "policy_id": self.policy.get("policy_id"),
            "signature_identity": signature.get("identity"),
            "signature_key_id": signature.get("key_id"),
            "signature_digest_verified": self.signature_digest_verified,
            "trusted_identity_matched": self.trusted_identity_matched,
            "cryptographic_signature_verified": False,
        }


def _validate_policy_shape(policy: dict[str, Any]) -> list[str]:
    blockers: list[str] = []

    missing = sorted(REQUIRED_POLICY_FIELDS - set(policy))
    blockers.extend(f"policy_missing_field:{field}" for field in missing)

    if policy.get("schema_version") != TRUST_POLICY_SCHEMA_VERSION:
        blockers.append(f"policy_unsupported_schema:{policy.get('schema_version')}")

    identities = policy.get("trusted_identities")
    if not isinstance(identities, list) or not identities:
        blockers.append("policy_trusted_identities_must_be_non_empty_list")
        return blockers

    for index, entry in enumerate(identities):
        if not isinstance(entry, dict):
            blockers.append(f"policy_trusted_identity_not_object:{index}")
            continue

        missing_entry_fields = sorted(REQUIRED_IDENTITY_FIELDS - set(entry))
        blockers.extend(
            f"policy_trusted_identity_missing:{index}:{field}"
            for field in missing_entry_fields
        )

        operations = entry.get("allowed_operations")
        if not isinstance(operations, list) or not operations:
            blockers.append(
                f"policy_allowed_operations_must_be_non_empty_list:{index}"
            )

        max_risk = entry.get("max_risk_level")
        if max_risk not in RISK_ORDER:
            blockers.append(f"policy_unsupported_max_risk_level:{index}:{max_risk}")

        status = entry.get("status", "active")
        if status not in {"active", "revoked"}:
            blockers.append(f"policy_unsupported_identity_status:{index}:{status}")

    return blockers


def evaluate_trust_policy(
    manifest: dict[str, Any], policy: dict[str, Any]
) -> TrustPolicyCheckResult:
    signature_result = check_signature_metadata(manifest)
    blockers = list(signature_result.blockers)
    warnings = list(signature_result.warnings)
    blockers.extend(_validate_policy_shape(policy))

    if policy.get("repository") != manifest.get("repository"):
        policy_repository = policy.get("repository")
        manifest_repository = manifest.get("repository")
        blockers.append(
            f"policy_repository_mismatch:policy={policy_repository}:manifest={manifest_repository}"
        )

    signature = manifest.get("signature")
    if not isinstance(signature, dict):
        signature = {}

    signature_identity = signature.get("identity")
    signature_key_id = signature.get("key_id")
    operation = manifest.get("operation")
    risk_level = manifest.get("risk_level")
    trusted_identity_matched = False

    identities = policy.get("trusted_identities")
    if isinstance(identities, list):
        exact_matches = [
            entry
            for entry in identities
            if isinstance(entry, dict)
            and entry.get("identity") == signature_identity
            and entry.get("key_id") == signature_key_id
        ]
    else:
        exact_matches = []

    if not exact_matches and signature_identity and signature_key_id:
        blockers.append(
            f"signature_identity_not_trusted:{signature_identity}:{signature_key_id}"
        )

    for entry in exact_matches:
        status = entry.get("status", "active")
        if status == "revoked":
            blockers.append(f"signature_identity_revoked:{signature_identity}")
            continue

        operations = entry.get("allowed_operations")
        if (
            isinstance(operations, list)
            and operation not in operations
            and "*" not in operations
        ):
            blockers.append(f"signature_operation_not_allowed:{operation}")
            continue

        max_risk = entry.get("max_risk_level")
        if (
            max_risk in RISK_ORDER
            and risk_level in RISK_ORDER
            and RISK_ORDER[risk_level] > RISK_ORDER[max_risk]
        ):
            blocker = (
                "signature_risk_level_exceeds_policy:"
                f"manifest={risk_level}:policy={max_risk}"
            )
            blockers.append(
                blocker
            )
            continue

        trusted_identity_matched = True
        break

    warnings.append("trust_policy_check_uses_public_metadata_only")

    passed = not blockers and trusted_identity_matched
    status = "trust_policy_allowed" if passed else "trust_policy_blocked_fail_closed"
    return TrustPolicyCheckResult(
        passed=passed,
        status=status,
        blockers=blockers,
        warnings=warnings,
        manifest=manifest,
        policy=policy,
        signature_digest_verified=signature_result.passed,
        trusted_identity_matched=trusted_identity_matched,
    )
